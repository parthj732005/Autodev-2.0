from fastapi.testclient import TestClient

from app.main import app
from app.routes import generate as generate_route


class FakeOrchestrator:
    """Stands in for the real multi-agent Orchestrator so these tests only
    exercise the metadata-sync integration point, not the LLM pipeline."""

    def __init__(self, emit, provider_settings, provider_override=None):
        self._emit = emit

    async def run(self, prompt):
        return {
            "plan": {
                "project_name": "demo_project",
                "technologies": {"backend": "fastapi", "frontend": "none", "database": "none"},
            },
            "files": {"main.py": "print('hi')\n"},
            "validation_report": {"passed": ["main.py"], "warnings": [], "errors": []},
            "valid": True,
            "consistency_report": {"issues": [], "checks_run": 0, "summary": "All 0 consistency checks passed"},
            "repair_report": {"attempted": [], "repaired": [], "reverted": []},
        }


def _authenticate(ws):
    ws.send_text('{"type": "authenticate", "token": "good-token"}')
    ack = ws.receive_json()
    assert ack["event"] == "authenticated"


def _run_generation_and_get_completed_event(ws):
    ws.send_text('{"prompt": "Build a todo app with FastAPI and SQLite"}')
    while True:
        data = ws.receive_json()
        if data.get("event") == "completed":
            return data


def _patch_common(monkeypatch, tmp_path):
    monkeypatch.setattr(generate_route, "Orchestrator", FakeOrchestrator)
    monkeypatch.setattr(generate_route, "load_settings", lambda: {"output_directory": str(tmp_path)})

    async def fake_get_current_user(token):
        return {"id": "u1", "email": "demo@example.com"}

    async def fake_get_provider_settings(token):
        return {"provider": "groq", "groq_api_key": "test-key", "groq_model": "test-model"}

    monkeypatch.setattr(generate_route.platform_client, "get_current_user", fake_get_current_user)
    monkeypatch.setattr(generate_route.platform_client, "get_provider_settings", fake_get_provider_settings)


def test_metadata_sync_success_is_silent_and_does_not_alter_completed_message(monkeypatch, tmp_path):
    _patch_common(monkeypatch, tmp_path)
    sync_calls = []

    async def fake_sync_ok(**kwargs):
        sync_calls.append(kwargs)
        return True

    monkeypatch.setattr(generate_route.platform_client, "sync_completed_project", fake_sync_ok)

    with TestClient(app) as client:
        with client.websocket_connect("/generate/ws") as ws:
            _authenticate(ws)
            completed = _run_generation_and_get_completed_event(ws)

    assert "metadata sync failed" not in completed["message"]
    assert completed["data"]["valid"] is True
    assert len(sync_calls) == 1
    assert sync_calls[0]["project_key"] == "demo_project"
    assert (tmp_path / "demo_project" / "main.py").exists()


def test_metadata_sync_failure_does_not_affect_successful_generation_or_disk_output(monkeypatch, tmp_path):
    """The critical failure-isolation guarantee: if the platform service or
    Postgres is down, generation still completes successfully, files are
    still written to disk, and the completion event still fires — only a
    clear note is appended to the message."""
    _patch_common(monkeypatch, tmp_path)

    async def fake_sync_fails(**kwargs):
        return False

    monkeypatch.setattr(generate_route.platform_client, "sync_completed_project", fake_sync_fails)

    with TestClient(app) as client:
        with client.websocket_connect("/generate/ws") as ws:
            _authenticate(ws)
            completed = _run_generation_and_get_completed_event(ws)

    # Generation itself is still reported as completed and valid...
    assert completed["event"] == "completed"
    assert completed["data"]["valid"] is True
    assert "metadata sync failed" in completed["message"]

    # ...and the generated files/metadata are genuinely on disk, untouched.
    assert (tmp_path / "demo_project" / "main.py").exists()
    assert (tmp_path / "demo_project" / "autodev_meta.json").exists()
