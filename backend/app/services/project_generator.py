import json
from datetime import datetime
from pathlib import Path


class ProjectGenerator:
    META_FILE = "autodev_meta.json"

    def __init__(self, output_dir: str):
        self.output_dir = Path(output_dir).expanduser()

    def resolve_unique_name(self, project_name: str) -> str:
        """If a folder with this name already exists, append _2, _3, ... until
        finding one that doesn't — so a same-named regeneration always lands in
        a fresh folder instead of silently overwriting or mixing files with a
        previous project. Callers should resolve the name up front (before
        deciding what to track for cleanup-on-failure) rather than letting
        generate() pick a different name internally."""
        candidate = project_name
        suffix = 2
        while (self.output_dir / candidate).exists():
            candidate = f"{project_name}_{suffix}"
            suffix += 1
        return candidate

    def generate(
        self,
        project_name: str,
        files: dict,
        plan: dict,
        validation_report: dict,
        consistency_report: dict | None = None,
        generation_logs: list[dict] | None = None,
        repair_report: dict | None = None,
    ) -> tuple[str, list[str], list[dict]]:
        project_path = self.output_dir / project_name
        project_path.mkdir(parents=True, exist_ok=True)

        resolved_root = project_path.resolve()
        written: list[str] = []
        skipped: list[dict] = []
        for relative_path, content in files.items():
            if not content or not content.strip():
                continue
            # Prevent path traversal: ensure resolved path stays inside project root
            try:
                full_path = (project_path / relative_path).resolve()
            except (OSError, ValueError) as exc:
                skipped.append({"file": relative_path, "reason": str(exc)})
                continue
            if not str(full_path).startswith(str(resolved_root)):
                continue
            try:
                full_path.parent.mkdir(parents=True, exist_ok=True)
                full_path.write_text(content, encoding="utf-8")
            except (OSError, ValueError) as exc:
                # An LLM occasionally emits an invalid filename (e.g. a literal
                # placeholder like "<some_id>.py"). One bad filename should
                # never take down an entire generation — skip it and keep going.
                skipped.append({"file": relative_path, "reason": str(exc)})
                continue
            written.append(relative_path)

        # Save metadata so the Projects page can read it later
        meta = {
            "project_name": project_name,
            "description": plan.get("description", ""),
            "project_type": plan.get("project_type", ""),
            "technologies": plan.get("technologies", {}),
            "agents_required": plan.get("agents_required", []),
            "features": plan.get("features", []),
            "dependencies": plan.get("dependencies", {}),
            "files": written,
            "file_count": len(written),
            "skipped_files": skipped,
            "validation_report": validation_report,
            "consistency_report": consistency_report or {},
            "repair_report": repair_report or {"attempted": [], "repaired": [], "reverted": []},
            "generation_logs": generation_logs or [],
            "generated_at": datetime.utcnow().isoformat(),
        }
        try:
            (project_path / self.META_FILE).write_text(
                json.dumps(meta, indent=2), encoding="utf-8"
            )
        except OSError as exc:
            raise RuntimeError(f"Could not write project metadata: {exc}") from exc

        return str(project_path), written, skipped
