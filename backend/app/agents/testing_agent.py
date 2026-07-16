from app.agents.base_agent import BaseAgent
from app.agents.utils import format_shared_context, parse_files

SYSTEM = """You are a QA engineer. Generate comprehensive tests for a Python backend project.

First determine every test file you will generate and what it covers. Then generate them.

Rules:
- Use pytest and httpx (AsyncClient) for FastAPI tests.
- Use pytest and Flask test client for Flask tests.
- Write tests for each route/endpoint.
- Include at least one integration test per resource.
- Start EVERY file with: ### filename: relative/path/to/test_file.py
- Code must be syntactically valid Python.
- If an API CONTRACT is provided, write tests for EXACTLY those routes — no invented endpoints.
- Import models from database.models (do not redefine them).
- Never assume filenames, routes, imports, or dependencies that are not explicitly given to you
  above — use only what's provided.
- Output ONLY valid Python code in each file. Never append markdown, headings, or prose after
  the code in the same file block.

Before returning:
- Verify every test targets a route that actually exists in the API CONTRACT above.
- Verify every import resolves to a real module (database.models, the app's own files, or a
  standard test library).
- If any mismatch is found, correct it before returning.
"""


class TestingAgent(BaseAgent):
    name = "TestingAgent"

    async def execute(self, context: dict) -> dict:
        plan = context["plan"]
        features = ", ".join(plan.get("features", []))
        framework = plan["technologies"].get("backend", "fastapi")

        # Routes + entities give tests full knowledge of the contract
        shared = format_shared_context(plan, include=("routes", "entities"))

        await self.emit("log", f"Generating {framework} test suite | {len(plan.get('api_routes', []))} routes to cover")

        prompt = f"""Generate a complete test suite for:

Project: {plan['description']}
Framework: {framework}
Features: {features}
{shared}

Generate pytest tests covering:
- Every route in the API CONTRACT above (one test per route minimum)
- Input validation (422 responses)
- Error cases (404, 400, etc.)
- Basic happy-path integration scenario

Place tests under tests/ directory.
Start each file with: ### filename: <relative_path>
"""

        raw = await self.provider.complete(SYSTEM, prompt)
        files = parse_files(raw)

        await self.emit("log", f"Generated {len(files)} test files")
        return {"testing_files": files}
