import re


# ─── Shared ProjectContext formatting ────────────────────────────────────────

def format_api_routes(plan: dict) -> str:
    """Return a compact, numbered API route list for LLM prompts."""
    routes = plan.get("api_routes", [])
    if not routes:
        return ""
    lines = ["API CONTRACT — implement/consume EXACTLY these routes, no extras:"]
    for r in routes:
        lines.append(f"  {r}")
    return "\n".join(lines)


def format_entities(plan: dict) -> str:
    """Return entity ownership note for LLM prompts."""
    entities = plan.get("entities", [])
    if not entities:
        return ""
    return (
        f"DATABASE MODELS — canonical source is database/models.py.\n"
        f"  Entities: {', '.join(entities)}\n"
        f"  DO NOT redefine these models. Import them: from database.models import ..."
    )


def format_env_vars(plan: dict) -> str:
    """Return env var list for LLM prompts."""
    env_vars = plan.get("environment_variables", [])
    if not env_vars:
        return ""
    return f"ENVIRONMENT VARIABLES — must appear in .env.example: {', '.join(env_vars)}"


def format_shared_context(plan: dict, include: tuple = ("routes", "entities", "env_vars")) -> str:
    """
    Build a compact shared context block to inject into any agent's prompt.
    Only includes sections relevant to the agent (controlled by `include`).
    """
    sections = []
    if "routes" in include:
        s = format_api_routes(plan)
        if s:
            sections.append(s)
    if "entities" in include:
        s = format_entities(plan)
        if s:
            sections.append(s)
    if "env_vars" in include:
        s = format_env_vars(plan)
        if s:
            sections.append(s)
    if not sections:
        return ""
    return "\n\n" + "\n\n".join(sections)


# ─── File parsing ─────────────────────────────────────────────────────────────

def strip_fences(text: str) -> str:
    text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
    text = re.sub(r"\n?```$", "", text)
    return text.strip()


def parse_files(raw: str, fallback: str | None = None) -> dict:
    """Parse LLM output that marks files with '### filename: <path>' headers."""
    files: dict = {}
    pattern = r"###\s*filename:\s*([^\n]+)\n([\s\S]*?)(?=###\s*filename:|$)"
    for filename, content in re.findall(pattern, raw, re.IGNORECASE):
        filename = filename.strip()
        content = strip_fences(content.strip())
        if content:
            files[filename] = content
    if not files and fallback:
        files[fallback] = strip_fences(raw.strip())
    return files
