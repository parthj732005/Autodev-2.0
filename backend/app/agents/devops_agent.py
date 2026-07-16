import re

from app.agents.base_agent import BaseAgent
from app.agents.utils import format_env_vars, parse_files

# Defense-in-depth allow-list: even with an explicit prompt constraint, an LLM
# can still generate application source files it has no business creating
# (confirmed live: a stray "backend/main.py" placeholder shadowed the real
# backend entry point). Rather than relying on the prompt alone, anything
# DevOpsAgent produces that doesn't look like devops/config tooling is
# dropped deterministically before it ever reaches disk.
_ALLOWED_DEVOPS_PATTERNS = (
    re.compile(r"(^|/)dockerfile", re.IGNORECASE),
    re.compile(r"\.ya?ml$", re.IGNORECASE),
    re.compile(r"(^|/)\.gitignore$"),
    re.compile(r"(^|/)\.dockerignore$"),
    re.compile(r"(^|/)\.env\.example$"),
)


def _is_devops_file(path: str) -> bool:
    normalized = path.replace("\\", "/")
    return any(p.search(normalized) for p in _ALLOWED_DEVOPS_PATTERNS)

SYSTEM = """You are a DevOps engineer. Generate Docker and project configuration files.

First determine every file you will generate and each file's responsibility. Then generate them.

Rules:
- Generate a Dockerfile for each service that has a backend.
- Generate docker-compose.yml when multiple services exist.
- Generate .gitignore appropriate for the tech stack.
- Generate .env.example with all required environment variables (no real values).
- Start EVERY file with: ### filename: filename (root-level files use just the filename)
- Content must be valid YAML/Dockerfile/shell syntax.
- Use the EXACT docker entry point specified — do not invent a different module path.
- Include ALL environment variables listed in .env.example — no omissions.
- Never assume filenames, package names, entry points, or environment variables that are not
  explicitly given to you above — use only what's provided.
- You generate ONLY Docker/CI/config files: Dockerfile, docker-compose.yml, .gitignore,
  .env.example. You MUST NEVER generate application source code — no main.py, no routes, no
  models, no package.json, no vite.config.js, no other build/dependency files. Those are owned
  by BackendAgent, FrontendAgent, and DatabaseAgent; generating your own copy of any of them
  creates duplicate, conflicting files elsewhere in the project.

Before returning:
- Verify the Dockerfile CMD uses the exact entry point given, character-for-character.
- Verify every environment variable given above appears in .env.example.
- Verify you have NOT generated any application source file (main.py, routes, models,
  package.json, vite.config.js, etc.) — remove any such file before returning.
- If any mismatch is found, correct it before returning.
"""


class DevOpsAgent(BaseAgent):
    name = "DevOpsAgent"

    async def execute(self, context: dict) -> dict:
        plan = context["plan"]
        has_backend = "backend" in plan.get("agents_required", [])
        has_frontend = "frontend" in plan.get("agents_required", [])
        has_db = plan["technologies"].get("database", "none") != "none"
        backend_fw = plan["technologies"].get("backend", "fastapi")
        db_type = plan["technologies"].get("database", "none")
        docker_entry = plan.get("docker_entry_point", "")
        env_block = format_env_vars(plan)

        await self.emit("log", f"Generating DevOps config | entry: {docker_entry or 'N/A'}")

        entry_instruction = (
            f"Docker CMD must use EXACTLY this uvicorn entry point: {docker_entry}"
            if docker_entry
            else "Determine entry point from the project structure."
        )

        prompt = f"""Generate DevOps configuration for:

Project: {plan['project_name']} — {plan['description']}
Backend: {"yes, " + backend_fw if has_backend else "no"}
Frontend: {"yes, React + Vite" if has_frontend else "no"}
Database: {db_type}

{entry_instruction}
{env_block}

Generate:
- Dockerfile (for backend, if exists)
- docker-compose.yml (if more than one service)
- .gitignore
- .env.example (must include ALL environment variables listed above, empty values)

Start each file with: ### filename: <filename>
"""

        raw = await self.provider.complete(SYSTEM, prompt)
        files = parse_files(raw)

        out_of_scope = [f for f in files if not _is_devops_file(f)]
        for f in out_of_scope:
            del files[f]
        if out_of_scope:
            await self.emit(
                "log",
                f"Dropped {len(out_of_scope)} out-of-scope file(s) DevOpsAgent shouldn't "
                f"have generated: {out_of_scope}",
            )

        await self.emit("log", f"Generated {len(files)} DevOps files: {list(files.keys())}")
        return {"devops_files": files}
