import json
import re

from app.agents.base_agent import BaseAgent

SYSTEM = """You are an expert software architect. Analyze the user's project description and return a structured JSON plan.

IMPORTANT: Return ONLY the raw JSON object. No markdown, no code fences, no explanation before or after.

Use this exact structure:
{
  "project_name": "snake_case_name",
  "description": "one-line description",
  "project_type": "backend_only | frontend_only | fullstack | cli | library",
  "technologies": {
    "backend": "fastapi | flask | none",
    "frontend": "react | none",
    "database": "sqlite | postgresql | mysql | none",
    "css": "tailwind | none"
  },
  "agents_required": ["backend", "frontend", "database", "devops", "testing", "documentation"],
  "features": ["feature 1", "feature 2"],
  "entities": ["ModelName1", "ModelName2"],
  "api_routes": ["GET /items", "POST /items", "PUT /items/{id}", "DELETE /items/{id}"],
  "environment_variables": ["DATABASE_URL", "SECRET_KEY"],
  "docker_entry_point": "main:app",
  "backend_package_name": "todo_api",
  "orm": "sqlalchemy | none",
  "test_framework": "pytest | none",
  "python_version": "3.11",
  "folder_structure": {
    "description": "brief description of layout"
  },
  "dependencies": {
    "backend": ["fastapi", "uvicorn", "sqlalchemy"],
    "frontend": ["react", "react-router-dom", "axios"]
  }
}

Rules:
- Only include agents that are genuinely needed.
- Always include "devops" and "documentation" in agents_required.
- For backend-only projects, omit "frontend" from agents_required.
- For frontend-only projects, omit "backend" and "database".
- If no database is needed, set database to "none" and omit "database" from agents_required.
- entities: list ONLY the core database model class names (e.g. ["User", "Todo"]). Use [] if no database.
- api_routes: list ALL API endpoints as "METHOD /path" strings (e.g. ["GET /todos", "POST /todos/{id}"]). Use [] if no backend.
- environment_variables: list all required env var names (e.g. ["DATABASE_URL", "SECRET_KEY"]). Always include DATABASE_URL if using a database.
- docker_entry_point: uvicorn entry string for the main app file. BackendAgent always writes its
  entry file as a flat "main.py" at the project root (never nested inside a package folder), so
  this must always be "main:app" — never a dotted package path like "todo_api.main:app". Use "" if no backend.
- backend_package_name: the top-level Python package/folder name the backend code will live under. Use "" if no backend.
- dependencies.backend is the ONE authoritative dependency list — every other agent (Backend, DevOps, Documentation) must use it verbatim for requirements.txt, never invent additional or different packages.
- Never assume filenames, package names, routes, imports, environment variables, or dependencies beyond what you output here — this plan is the single source of truth every other agent will follow exactly.
"""

RETRY_SYSTEM = """You are a JSON formatter. The user will give you text that contains a JSON object.
Extract and return ONLY the valid JSON object, with no other text, markdown, or explanation.
Fix any minor JSON syntax errors (trailing commas, missing quotes) if needed."""


def _extract_json(raw: str) -> dict | None:
    """Try multiple strategies to extract a valid JSON object from raw text."""
    # Strategy 1: direct parse
    try:
        return json.loads(raw.strip())
    except json.JSONDecodeError:
        pass

    # Strategy 2: extract first {...} block
    match = re.search(r"\{[\s\S]*\}", raw)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    # Strategy 3: strip markdown fences and retry
    cleaned = re.sub(r"^```(?:json)?\s*", "", raw.strip(), flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    match = re.search(r"\{[\s\S]*\}", cleaned)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    # Strategy 4: fix trailing commas before } or ]
    if match:
        fixed = re.sub(r",\s*([}\]])", r"\1", match.group())
        try:
            return json.loads(fixed)
        except json.JSONDecodeError:
            pass

    return None


def _validate_plan(plan: dict) -> list[str]:
    """Return list of missing required fields."""
    errors = []
    for field in ("project_name", "description", "project_type", "technologies", "agents_required"):
        if field not in plan:
            errors.append(f"Missing field: {field}")
    return errors


def _apply_defaults(plan: dict) -> None:
    """Ensure all coordination fields exist with safe defaults."""
    plan.setdefault("entities", [])
    plan.setdefault("api_routes", [])
    plan.setdefault("environment_variables", [])
    plan.setdefault("docker_entry_point", "")
    plan.setdefault("dependencies", {"backend": [], "frontend": []})
    plan["dependencies"].setdefault("backend", [])
    plan["dependencies"].setdefault("frontend", [])
    plan.setdefault("backend_package_name", "")
    plan.setdefault("orm", "none")
    plan.setdefault("test_framework", "pytest")
    plan.setdefault("python_version", "3.11")

    # Derive docker_entry_point / backend_package_name from project_name if missing.
    # BackendAgent always writes its entry file as a flat "main.py" at the project
    # root, never nested under a package folder — so the entry point must be the
    # flat "main:app", not a dotted package path (confirmed by two independent
    # live generations where a dotted path pointed at a file that doesn't exist).
    if not plan["docker_entry_point"] and plan["technologies"].get("backend") not in (None, "none"):
        plan["docker_entry_point"] = "main:app"
    if not plan["backend_package_name"] and plan["technologies"].get("backend") not in (None, "none"):
        plan["backend_package_name"] = plan.get("project_name", "app")

    # Ensure DATABASE_URL in env vars when using a database
    db = plan["technologies"].get("database", "none")
    if db and db != "none" and "DATABASE_URL" not in plan["environment_variables"]:
        plan["environment_variables"].insert(0, "DATABASE_URL")


class PlannerAgent(BaseAgent):
    name = "PlannerAgent"
    max_retries = 3

    async def execute(self, context: dict) -> dict:
        prompt = context["prompt"]
        await self.emit("log", f'Analyzing: "{prompt[:120]}"')

        raw = await self.provider.complete(SYSTEM, f"Project: {prompt}")

        plan = _extract_json(raw)

        # If extraction failed, ask the model to clean its own output
        if plan is None:
            await self.emit("log", "JSON extraction failed — asking model to reformat...")
            raw2 = await self.provider.complete(RETRY_SYSTEM, f"Extract JSON from this:\n\n{raw}")
            plan = _extract_json(raw2)

        if plan is None:
            raise ValueError(
                f"PlannerAgent could not produce valid JSON after cleanup.\n"
                f"Raw output (first 300 chars): {raw[:300]}"
            )

        errors = _validate_plan(plan)
        if errors:
            raise ValueError(f"Plan is missing required fields: {errors}")

        # Ensure required agents are always present
        agents = plan.setdefault("agents_required", [])
        for required_agent in ("devops", "documentation"):
            if required_agent not in agents:
                agents.append(required_agent)

        # Apply safe defaults for all coordination fields
        _apply_defaults(plan)

        await self.emit(
            "log",
            f"Plan ready: {plan.get('project_type')} | agents: {plan['agents_required']} "
            f"| routes: {len(plan['api_routes'])} | entities: {plan['entities']}",
        )

        return {"plan": plan}
