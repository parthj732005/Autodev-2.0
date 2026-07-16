from app.agents.base_agent import BaseAgent
from app.agents.utils import format_shared_context, parse_files

SYSTEM = """You are a senior frontend engineer. Generate a complete React + Vite + TailwindCSS project.

First determine every file you will generate and each file's responsibility. Then generate them.
Never import a file that is not generated.

Rules:
- React 18 with functional components and hooks only.
- TailwindCSS for all styling. Dark mode preferred.
- react-router-dom v6 for routing.
- Use fetch or axios for API calls.
- Start EVERY file with: ### filename: relative/path/to/file.jsx
- Always generate: src/App.jsx, src/main.jsx, index.html, package.json, vite.config.js,
  tailwind.config.js, postcss.config.js, src/index.css, and all page/component files.
- Code must be syntactically valid JavaScript/JSX.
- If an API CONTRACT is provided, call EXACTLY those endpoints — no invented routes.
- Backend API base URL is always http://localhost:8000.
- Never assume filenames, package names, routes, imports, environment variables, or dependencies
  that are not explicitly given to you above — use only what's provided.

Before returning:
- Verify every import resolves to a file you generated.
- Verify every API call targets a route from the API CONTRACT above, if one was given.
- Verify every dependency you use is listed in package.json.
- If any mismatch is found, correct it before returning.
"""


class FrontendAgent(BaseAgent):
    name = "FrontendAgent"

    async def execute(self, context: dict) -> dict:
        plan = context["plan"]
        features = ", ".join(plan.get("features", []))
        deps = ", ".join(plan["dependencies"].get("frontend", []))

        # Shared coordination context — routes only (frontend doesn't need entity ownership note)
        shared = format_shared_context(plan, include=("routes",))

        await self.emit("log", f"Generating React frontend | consuming {len(plan.get('api_routes', []))} backend routes")

        prompt = f"""Generate a complete React frontend project.

Project name: {plan['project_name']}
Description: {plan['description']}
Features: {features}
Backend API base URL: http://localhost:8000
npm dependencies: {deps}
{shared}

Generate ALL necessary files:
- src/App.jsx (with router)
- src/main.jsx
- src/index.css (Tailwind directives)
- index.html
- package.json
- vite.config.js
- tailwind.config.js
- postcss.config.js
- All page components under src/pages/
- Reusable components under src/components/

Dark theme. Professional design.
Start each file with: ### filename: <relative_path>
"""

        raw = await self.provider.complete(SYSTEM, prompt)
        files = parse_files(raw, fallback="src/App.jsx")

        await self.emit("log", f"Generated {len(files)} frontend files")
        return {"frontend_files": files}
