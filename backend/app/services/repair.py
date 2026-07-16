"""
Targeted Repair Phase — ONE deterministic repair pass, not a loop.

    Generation → Static Validation → Targeted Repair → Final Verification

After the Validator runs, this takes every file flagged with a real syntax
problem (Python syntax errors, JS/JSX bracket imbalance / markdown
contamination — never warnings like "empty file" or dependency hints) and
attempts exactly ONE LLM-driven fix per file. A fix is only ever accepted if
it's independently re-verified to actually pass; otherwise the file is
reverted to its original, unmodified content. This is intentionally NOT a
retry loop — if one targeted attempt doesn't fix it, another identical call
is unlikely to either (the root cause is usually a prompt/hallucination/
truncation issue, not transient noise), so we report it instead of retrying.

Toggle REPAIR_ENABLED = False to fully disable this phase without touching
any other code path.
"""
from app.agents.utils import strip_fences
from app.agents.validator_agent import _validate_js_basic, _validate_python

REPAIR_ENABLED = True

REPAIR_SYSTEM = """You are a precise code repair tool. You will be given one file's exact \
content and the specific syntax error found in it. Fix ONLY that error — do not rewrite \
unrelated code, do not change working logic, do not add features or comments. Return ONLY \
the corrected raw file content: no markdown code fences, no explanation, no filename header, \
nothing except the fixed file content."""


def _select_repair_candidates(validation_report: dict) -> list[dict]:
    """Pick only real syntax problems worth an LLM repair attempt. Explicitly
    excludes low-stakes warnings (empty file, missing requirements.txt) that
    a single-file rewrite can't meaningfully address anyway."""
    candidates = list(validation_report.get("errors", []))  # always Python syntax errors today
    for w in validation_report.get("warnings", []):
        file = w.get("file", "") or ""
        if file.endswith((".js", ".jsx", ".ts", ".tsx")) and "unmatched brackets" in w.get("issue", "").lower():
            candidates.append(w)
    return candidates


def _validate_single_file(filepath: str, content: str) -> dict | None:
    if filepath.endswith(".py"):
        return _validate_python(filepath, content)
    if filepath.endswith((".js", ".jsx", ".ts", ".tsx")):
        return _validate_js_basic(filepath, content)
    return None


async def run_targeted_repair(all_files: dict, validation_report: dict, provider, emit) -> dict:
    """
    Mutates `all_files` in place for any file that's successfully repaired.

    `emit(event, message, data=None)` is an async callback the caller uses to
    surface progress (kept generic so this module doesn't depend on
    AgentEvent/BaseAgent — the orchestrator wraps it appropriately).

    Returns:
        {"attempted": [...], "repaired": [...], "reverted": [...]}
    """
    report = {"attempted": [], "repaired": [], "reverted": []}

    if not REPAIR_ENABLED:
        return report

    candidates = _select_repair_candidates(validation_report)
    if not candidates:
        return report

    await emit("log", f"Targeted Repair: attempting {len(candidates)} file(s) with real errors")

    for diagnostic in candidates:
        filepath = diagnostic.get("file")
        original_content = all_files.get(filepath)
        if not filepath or original_content is None:
            continue

        report["attempted"].append(filepath)

        prompt = f"""File: {filepath}

Exact error: {diagnostic.get('issue')}
Likely cause: {diagnostic.get('likely_cause')}
Suggested fix: {diagnostic.get('suggested_fix')}

--- FILE CONTENT ---
{original_content}
--- END FILE CONTENT ---

Return ONLY the corrected file content."""

        try:
            raw = await provider.complete(REPAIR_SYSTEM, prompt)
        except Exception as exc:
            await emit("log", f"Repair attempt failed for {filepath}: {exc} — keeping original")
            report["reverted"].append(filepath)
            continue

        fixed_content = strip_fences(raw.strip())

        # Only accept the fix if it's independently re-verified to actually
        # pass — never trust the LLM's own claim that it fixed the issue.
        still_broken = _validate_single_file(filepath, fixed_content)
        if still_broken is None and fixed_content.strip():
            all_files[filepath] = fixed_content
            report["repaired"].append(filepath)
            await emit("log", f"Repaired {filepath}")
        else:
            report["reverted"].append(filepath)
            await emit(
                "log",
                f"Repair attempt for {filepath} did not pass verification — keeping original",
            )

    return report
