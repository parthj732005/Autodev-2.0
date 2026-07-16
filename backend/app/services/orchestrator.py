from typing import Callable

from app.agents.backend_agent import BackendAgent
from app.agents.database_agent import DatabaseAgent
from app.agents.devops_agent import DevOpsAgent
from app.agents.documentation_agent import DocumentationAgent
from app.agents.frontend_agent import FrontendAgent
from app.agents.planner_agent import PlannerAgent
from app.agents.testing_agent import TestingAgent
from app.agents.base_agent import AgentEvent
from app.agents.validator_agent import ValidatorAgent
from app.services import consistency_checker, repair
from app.services.model_provider import get_provider

AGENT_REGISTRY = {
    "backend": BackendAgent,
    "frontend": FrontendAgent,
    "database": DatabaseAgent,
    "devops": DevOpsAgent,
    "testing": TestingAgent,
    "documentation": DocumentationAgent,
}

# Execution order respects dependencies (database before backend, etc.)
EXECUTION_ORDER = ["database", "backend", "frontend", "devops", "testing", "documentation"]


class Orchestrator:
    def __init__(self, emit: Callable, provider_settings: dict, provider_override: str | None = None):
        """
        provider_settings: this generation's already-resolved, per-user
        provider configuration (see app/services/platform_client.py ::
        get_provider_settings()). Fetched ONCE by the caller before
        construction — never re-fetched per agent call, and never a shared
        global — so concurrent generations for different users can never
        observe each other's credentials.
        """
        self._emit = emit
        settings = provider_settings
        if provider_override:
            settings = {**settings, "provider": provider_override}
        self.provider = get_provider(settings)
        self.settings = settings

    def _make_agent(self, cls):
        return cls(provider=self.provider, emit=self._emit)

    async def run(self, prompt: str) -> dict:
        context: dict = {"prompt": prompt}

        # Phase 1 — Plan
        planner = self._make_agent(PlannerAgent)
        context.update(await planner.run(context))

        plan: dict = context["plan"]
        agents_required: list = plan.get("agents_required", ["backend", "devops", "documentation"])

        # Guarantee devops + documentation always run
        for name in ("devops", "documentation"):
            if name not in agents_required:
                agents_required.append(name)

        # Phase 2 — Run agents in dependency order
        for agent_name in EXECUTION_ORDER:
            if agent_name in agents_required and agent_name in AGENT_REGISTRY:
                agent = self._make_agent(AGENT_REGISTRY[agent_name])
                result = await agent.run(context)
                context.update(result)

        # Phase 3 — Merge all generated files
        all_files: dict = {}
        for key in (
            "database_files",
            "backend_files",
            "frontend_files",
            "devops_files",
            "testing_files",
            "documentation_files",
        ):
            all_files.update(context.get(key, {}))

        context["all_files"] = all_files

        # Phase 4 — Static Validation (syntax / structure)
        validator = self._make_agent(ValidatorAgent)
        context.update(await validator.run(context))

        # Phase 4.5 — Targeted Repair (ONE repair pass, not a loop — see
        # services/repair.py). Only files with a real syntax error get a
        # single LLM fix attempt; a fix is kept only if independently
        # re-verified, otherwise the original file is left untouched.
        async def _repair_emit(event, message, data=None):
            await self._emit(
                AgentEvent(agent="RepairPhase", event=event, message=message, data=data or {})
            )

        repair_report = await repair.run_targeted_repair(
            all_files, context.get("validation_report", {}), self.provider, _repair_emit
        )

        if repair_report["attempted"]:
            # Final Verification — one fresh validation pass reflecting any repairs.
            validator = self._make_agent(ValidatorAgent)
            context.update(await validator.run(context))
            await _repair_emit(
                "log",
                f"Repair Summary — fixed {len(repair_report['repaired'])}, "
                f"reverted {len(repair_report['reverted'])} of {len(repair_report['attempted'])} attempted",
                repair_report,
            )

        # Phase 5 — Deterministic consistency check (pure Python, no LLM)
        consistency_report = consistency_checker.run(all_files, plan)
        if consistency_report["issues"]:
            await self._emit(
                AgentEvent(
                    agent="ConsistencyChecker",
                    event="log",
                    message=consistency_report["summary"],
                    data=consistency_report,
                )
            )

        return {
            "plan": plan,
            "files": all_files,
            "validation_report": context.get("validation_report", {}),
            "valid": context.get("valid", True),
            "consistency_report": consistency_report,
            "repair_report": repair_report,
        }
