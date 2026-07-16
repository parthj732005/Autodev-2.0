import ast
import re

from app.agents.base_agent import BaseAgent


class ValidatorAgent(BaseAgent):
    name = "ValidatorAgent"
    max_retries = 0

    async def execute(self, context: dict) -> dict:
        all_files: dict = context.get("all_files", {})
        report = {"passed": [], "warnings": [], "errors": []}

        await self.emit("log", f"Validating {len(all_files)} generated files")

        for filepath, content in all_files.items():
            if not content or not content.strip():
                report["warnings"].append({
                    "file": filepath,
                    "line": None,
                    "issue": "Empty file",
                    "likely_cause": "Agent produced no content for this file",
                    "suggested_fix": "Regenerate or manually create the file",
                })
                continue

            if filepath.endswith(".py"):
                diagnostic = _validate_python(filepath, content)
                if diagnostic:
                    report["errors"].append(diagnostic)
                    await self.emit(
                        "log",
                        f"Syntax error in {filepath} line {diagnostic.get('line')}: {diagnostic['issue']}",
                    )
                else:
                    report["passed"].append(filepath)

            elif filepath.endswith((".js", ".jsx", ".ts", ".tsx")):
                diagnostic = _validate_js_basic(filepath, content)
                if diagnostic:
                    report["warnings"].append(diagnostic)
                else:
                    report["passed"].append(filepath)

            elif filepath == "requirements.txt":
                if not content.strip():
                    report["warnings"].append({
                        "file": filepath,
                        "line": None,
                        "issue": "Empty requirements.txt",
                        "likely_cause": "BackendAgent did not generate a requirements section",
                        "suggested_fix": "Add required packages manually (fastapi, uvicorn, etc.)",
                    })
                else:
                    report["passed"].append(filepath)

            else:
                report["passed"].append(filepath)

        passed = len(report["passed"])
        errors = len(report["errors"])
        warnings = len(report["warnings"])

        await self.emit(
            "log",
            f"Validation complete — {passed} passed, {warnings} warnings, {errors} errors",
            {"passed": passed, "warnings": warnings, "errors": errors},
        )

        return {
            "validation_report": report,
            "valid": errors == 0,
        }


# ─── Python validation ────────────────────────────────────────────────────────

def _validate_python(filepath: str, content: str) -> dict | None:
    try:
        ast.parse(content)
        return None
    except SyntaxError as exc:
        line = exc.lineno or 0
        msg = exc.msg or "SyntaxError"
        likely_cause, suggested_fix = _diagnose_python_error(content, line, msg)
        return {
            "file": filepath,
            "line": line,
            "issue": msg,
            "likely_cause": likely_cause,
            "suggested_fix": suggested_fix,
        }


def _diagnose_python_error(content: str, line: int, msg: str) -> tuple[str, str]:
    """Return (likely_cause, suggested_fix) for common Python syntax errors."""
    lines = content.splitlines()
    error_line = lines[line - 1].strip() if 0 < line <= len(lines) else ""
    tail = "\n".join(lines[max(0, line - 3):])

    # Markdown block appended after Python code
    if re.search(r"^(```|#{1,3} )", tail, re.MULTILINE):
        return (
            "Markdown content (code fence or heading) appended after Python code",
            f"Remove markdown starting near line {line}. Strip everything from '```' or '#' onwards.",
        )

    # Unterminated string
    if "EOL while scanning string literal" in msg or "unterminated string" in msg.lower():
        return (
            "Unterminated string literal — a quote was opened but never closed",
            f"Check line {line} for a missing closing quote (\", ', or triple-quote).",
        )

    # Invalid character (often a unicode quote from LLM)
    if "invalid character" in msg.lower() or "invalid syntax" in msg.lower():
        if any(ch in error_line for ch in ["“", "”", "‘", "’"]):
            return (
                "Unicode smart quotes used instead of ASCII quotes",
                f"Replace curly quotes (“”‘’) with straight quotes on line {line}.",
            )
        return (
            "Invalid Python syntax — possibly a template placeholder or truncated output",
            f"Review line {line}: '{error_line[:80]}' for non-Python content.",
        )

    # f-string errors
    if "f-string" in msg.lower():
        return (
            "Malformed f-string expression",
            f"Check f-string on line {line} for unbalanced braces or invalid expressions.",
        )

    return (
        f"Python syntax error: {msg}",
        f"Fix the syntax issue on line {line}.",
    )


# ─── JS/JSX validation ────────────────────────────────────────────────────────

def _validate_js_basic(filepath: str, content: str) -> dict | None:
    opens = content.count("{") + content.count("(") + content.count("[")
    closes = content.count("}") + content.count(")") + content.count("]")
    imbalance = abs(opens - closes)
    if imbalance > 8:
        likely_cause = (
            "Truncated output (LLM hit token limit mid-file)"
            if opens > closes
            else "Extra closing brackets — possibly duplicate or nested block"
        )
        return {
            "file": filepath,
            "line": None,
            "issue": f"Likely unmatched brackets (opens={opens}, closes={closes}, diff={imbalance})",
            "likely_cause": likely_cause,
            "suggested_fix": (
                "Check the end of the file for missing closing braces/brackets"
                if opens > closes
                else "Check for duplicate closing brackets or extra '}}' in the file"
            ),
        }
    return None
