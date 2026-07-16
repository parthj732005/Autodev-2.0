import re

from app.agents.base_agent import BaseAgent
from app.agents.utils import format_shared_context

SYSTEM = """You are a technical writer. Generate a comprehensive README.md for a software project.

The README must include:
1. Project title and badges
2. Short description
3. Features list (bulleted)
4. Tech stack table
5. Prerequisites
6. Installation instructions (step-by-step)
7. Environment variables section (table format)
8. How to run (development and production/Docker)
9. Project folder structure (tree format)
10. API endpoints overview — document ONLY the routes provided in the API CONTRACT, exactly as given
11. Contributing guide
12. License

Use clean Markdown. Be specific and accurate to the project's actual tech stack.
Do NOT wrap output in code fences.
Do NOT invent API routes — document only what is listed in the API CONTRACT.
Backend dependencies given to you are the ONLY packages you may mention — do not add others.

If information for any section is unavailable, omit that section entirely rather than guessing.
Never infer routes, folder names, or dependencies that were not explicitly given to you above.
"""


class DocumentationAgent(BaseAgent):
    name = "DocumentationAgent"

    async def execute(self, context: dict) -> dict:
        plan = context["plan"]

        # Routes + entities give documentation accurate knowledge of the system
        shared = format_shared_context(plan, include=("routes", "entities", "env_vars"))

        await self.emit("log", f"Generating README.md | documenting {len(plan.get('api_routes', []))} routes")

        prompt = f"""Generate README.md for:

Project name: {plan['project_name']}
Description: {plan['description']}
Project type: {plan.get('project_type', 'fullstack')}
Backend: {plan['technologies'].get('backend', 'none')}
Frontend: {plan['technologies'].get('frontend', 'none')}
Database: {plan['technologies'].get('database', 'none')}
Features: {plan.get('features', [])}
Backend dependencies: {plan['dependencies'].get('backend', [])}
Frontend dependencies: {plan['dependencies'].get('frontend', [])}
{shared}
"""

        readme = await self.provider.complete(SYSTEM, prompt)
        readme = re.sub(r"^```\w*\n?", "", readme.strip())
        readme = re.sub(r"\n?```$", "", readme)

        await self.emit("log", "README.md generated")
        return {"documentation_files": {"README.md": readme.strip()}}
