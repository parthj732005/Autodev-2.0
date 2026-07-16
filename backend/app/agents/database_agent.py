from app.agents.base_agent import BaseAgent
from app.agents.utils import format_env_vars, parse_files

SYSTEM = """You are a senior database engineer. Generate complete database models, migrations, and configuration.

First determine every file you will generate and each file's responsibility. Then generate them.
Never import a file that is not generated.

Rules:
- Use SQLAlchemy 2.x for ORM models.
- Alembic for migrations when appropriate.
- Include a seed data script.
- Include a database configuration module.
- Start EVERY file with: ### filename: relative/path/to/file.py
- Code must be syntactically valid Python.
- You are the ONLY OWNER of all database models and of the SQLAlchemy `Base` declarative class.
  BackendAgent MUST NEVER define `Base` or any SQLAlchemy model — it will only import them from here.
- All entities listed must be defined here in database/models.py, nowhere else.
- Never assume filenames, package names, routes, imports, environment variables, or dependencies
  that are not explicitly given to you above — use only what's provided.

Before returning:
- Verify every import in every file actually resolves to a file you generated.
- Verify every environment variable you reference is one that was given to you.
- Verify every referenced file (e.g. in Alembic config) actually exists among your generated files.
- If any mismatch is found, correct it before returning.
"""


class DatabaseAgent(BaseAgent):
    name = "DatabaseAgent"

    async def execute(self, context: dict) -> dict:
        plan = context["plan"]
        db_type = plan["technologies"].get("database", "sqlite")
        features = ", ".join(plan.get("features", []))
        entities = plan.get("entities", [])
        env_block = format_env_vars(plan)

        await self.emit("log", f"Generating {db_type} models: {entities or 'infer from features'}")

        entity_instruction = (
            f"Create EXACTLY these model classes (you own them, backend will import them):\n"
            + "\n".join(f"  - {e}" for e in entities)
            if entities
            else "Infer the required models from the project features."
        )

        prompt = f"""Generate the complete database layer for:

Project: {plan['description']}
Database: {db_type}
Features (infer tables from these): {features}

{entity_instruction}
{env_block}

Generate:
- database/models.py   ← CANONICAL model definitions (all entities here, nowhere else)
- database/database.py ← engine, session, Base
- Alembic config if using PostgreSQL/MySQL
- database/seed.py     ← sample data

Start each file with: ### filename: <relative_path>
"""

        raw = await self.provider.complete(SYSTEM, prompt)
        files = parse_files(raw)

        await self.emit("log", f"Generated {len(files)} database files")
        return {"database_files": files}
