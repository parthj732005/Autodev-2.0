from app.agents.base_agent import BaseAgent
from app.agents.utils import format_shared_context, parse_files

# Subfolder names BackendAgent is legitimately expected to nest files under.
# Anything else showing up as a single common top-level prefix across every
# file it generated means it wrapped its whole output in a project-name
# folder instead of writing main.py flat at the root, as instructed.
_EXPECTED_SUBFOLDERS = {
    "routes", "schemas", "services", "models", "tests", "static", "templates", "utils", "core", "api",
}


def _flatten_nested_layout(files: dict) -> dict:
    """Deterministic backstop: prompt instructions alone didn't reliably stop
    BackendAgent from nesting its entire output under a folder named after
    the project (confirmed live — "future_tech_showcase/main.py" instead of
    a flat "main.py"), so if that happens anyway, strip the common prefix
    here rather than trusting the LLM to have followed the rule."""
    normalized_keys = {p.replace("\\", "/") for p in files}
    if "main.py" in normalized_keys:
        return files  # already flat, nothing to do

    prefixes = set()
    for path in normalized_keys:
        parts = path.split("/")
        if len(parts) > 1 and parts[0].lower() not in _EXPECTED_SUBFOLDERS:
            prefixes.add(parts[0])

    if len(prefixes) != 1:
        return files  # ambiguous — leave alone rather than guess

    prefix = next(iter(prefixes))
    if f"{prefix}/main.py" not in normalized_keys:
        return files  # no main.py under that prefix — nothing to fix

    flattened = {}
    for path, content in files.items():
        normalized = path.replace("\\", "/")
        if normalized.startswith(f"{prefix}/"):
            flattened[normalized[len(prefix) + 1:]] = content
        else:
            flattened[path] = content
    return flattened


def _drop_database_ownership_violations(files: dict) -> tuple[dict, list[str]]:
    """DatabaseAgent is the sole owner of database/ — confirmed live that
    BackendAgent can still generate its own conflicting database/models.py
    despite an explicit prompt rule against it. Drop anything BackendAgent
    tries to put under database/ so it can never clobber (or duplicate) the
    canonical models when files are merged in orchestrator.py."""
    violations = [f for f in files if f.replace("\\", "/").startswith("database/")]
    for f in violations:
        del files[f]
    return files, violations

SYSTEM = """You are a senior backend engineer generating a Python backend.

Priority order (highest first) — when in doubt, satisfy an earlier priority even at the
expense of a later one:
1. The code must compile / parse without syntax errors.
2. Every import must resolve to a file that actually exists.
3. The API contract must be implemented exactly as given.
4. General code quality and completeness.

First determine every file you will generate and each file's responsibility. Then generate them.
Never import a file that is not generated.

Rules:
- Use the specified framework (FastAPI or Flask).
- Include CORS configuration.
- Use environment variables for all sensitive config (never hardcode secrets).
- Include proper error handling with HTTP status codes.
- Use Pydantic models for request/response validation (FastAPI).
- Structure code in separate files: main app, routes, models, schemas, services.
- Start EVERY file with: ### filename: relative/path/to/file.py
- requirements.txt MUST list EXACTLY the backend dependencies given below — do not add, remove,
  or invent packages beyond that list.
- Always include .env.example.
- Code must be syntactically valid Python.
- If a shared API CONTRACT is provided, implement EXACTLY those routes — no extra, no missing.
- DatabaseAgent is the ONLY owner of database models and the SQLAlchemy `Base` class. You MUST
  NEVER define `Base` or any SQLAlchemy model yourself — only import them from database.models.
- If ENVIRONMENT VARIABLES are provided, include all of them in .env.example.
- Never assume filenames, package names, routes, imports, environment variables, or dependencies
  that are not explicitly given to you above — use only what's provided.
- Your main application entry file MUST be a flat "main.py" at the project root — filename
  "main.py" exactly, NOT nested inside any subfolder (never "your_project_name/main.py" or
  similar). All other files (routes/, schemas/, services/) are relative to that same root.

Before returning:
- Verify every import in every file resolves to a file you generated or to database.models.
- Verify every route in the API CONTRACT is implemented, and no extra routes were added.
- Verify every dependency you use is listed in requirements.txt.
- Verify every environment variable you reference is in .env.example.
- Verify your entry file is named exactly "main.py" at the project root, not nested in a subfolder.
- If any mismatch is found, correct it before returning.
"""


class BackendAgent(BaseAgent):
    name = "BackendAgent"

    async def execute(self, context: dict) -> dict:
        plan = context["plan"]
        framework = plan["technologies"].get("backend", "fastapi")
        db = plan["technologies"].get("database", "none")
        features = ", ".join(plan.get("features", []))
        deps = ", ".join(plan["dependencies"].get("backend", []))

        # Shared coordination context from PlannerAgent
        shared = format_shared_context(plan, include=("routes", "entities", "env_vars"))

        await self.emit("log", f"Generating {framework} backend | database: {db} | routes: {len(plan.get('api_routes', []))}")

        prompt = f"""Generate a complete {framework} backend project.

Project name: {plan['project_name']}
Description: {plan['description']}
Features: {features}
Database: {db}
Backend dependencies (use EXACTLY this list for requirements.txt, verbatim, no additions): {deps}
{shared}

Generate ALL necessary files:
- Main application file — MUST be named exactly "main.py" at the project root, never nested
  inside a subfolder
- Route handlers (follow the API CONTRACT above exactly)
- Pydantic schemas
- Service layer
- requirements.txt
- .env.example (include all ENVIRONMENT VARIABLES listed above)

Start each file with: ### filename: <relative_path>
"""

        raw = await self.provider.complete(SYSTEM, prompt)
        files = parse_files(raw, fallback="main.py")
        files = _flatten_nested_layout(files)
        files, db_violations = _drop_database_ownership_violations(files)
        if db_violations:
            await self.emit(
                "log",
                f"Dropped {len(db_violations)} file(s) BackendAgent tried to put under "
                f"database/, which DatabaseAgent already owns: {db_violations}",
            )

        await self.emit("log", f"Generated {len(files)} backend files: {list(files.keys())[:5]}")
        return {"backend_files": files}
