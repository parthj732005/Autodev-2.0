from fastapi.testclient import TestClient

from app.main import app
from app.routes import generate as generate_route
from app.services.orchestrator import Orchestrator


class FakeOrchestrator:
    """Spies on how it was constructed, so tests can assert the resolved
    provider_settings was actually threaded through, and that it's fetched
    exactly once (not re-fetched per agent call)."""

    call_count = 0
    last_provider_settings = None

    def __init__(self, emit, provider_settings, provider_override=None):
        FakeOrchestrator.call_count += 1
        FakeOrchestrator.last_provider_settings = provider_settings
        self._emit = emit

    async def run(self, prompt):
        return {
            "plan": {"project_name": "cfg_test_project", "technologies": {}},
            "files": {"main.py": "print('hi')\n"},
            "validation_report": {"passed": [], "warnings": [], "errors": []},
            "valid": True,
            "consistency_report": {},
            "repair_report": {"attempted": [], "repaired": [], "reverted": []},
        }


def _authenticate(ws):
    ws.send_text('{"type": "authenticate", "token": "good-token"}')
    ack = ws.receive_json()
    assert ack["event"] == "authenticated"


def _patch_auth(monkeypatch):
    async def fake_get_current_user(token):
        return {"id": "u1", "email": "demo@example.com"}

    monkeypatch.setattr(generate_route.platform_client, "get_current_user", fake_get_current_user)


def test_provider_settings_fetched_exactly_once_and_injected_into_orchestrator(monkeypatch, tmp_path):
    FakeOrchestrator.call_count = 0
    monkeypatch.setattr(generate_route, "Orchestrator", FakeOrchestrator)
    monkeypatch.setattr(generate_route, "load_settings", lambda: {"output_directory": str(tmp_path)})
    _patch_auth(monkeypatch)

    fetch_calls = []

    async def fake_get_provider_settings(token):
        fetch_calls.append(token)
        return {"provider": "groq", "groq_api_key": "KEY_XYZ", "groq_model": "model-xyz"}

    async def fake_sync_ok(**kwargs):
        return True

    monkeypatch.setattr(generate_route.platform_client, "get_provider_settings", fake_get_provider_settings)
    monkeypatch.setattr(generate_route.platform_client, "sync_completed_project", fake_sync_ok)

    with TestClient(app) as client:
        with client.websocket_connect("/generate/ws") as ws:
            _authenticate(ws)
            ws.send_text('{"prompt": "Build a todo app with FastAPI and SQLite"}')
            while True:
                data = ws.receive_json()
                if data.get("event") == "completed":
                    break

    assert fetch_calls == ["good-token"]  # fetched exactly once, for this generation's token
    assert FakeOrchestrator.call_count == 1
    assert FakeOrchestrator.last_provider_settings["groq_api_key"] == "KEY_XYZ"
    assert FakeOrchestrator.last_provider_settings["groq_model"] == "model-xyz"


def test_missing_provider_settings_blocks_generation_before_it_starts(monkeypatch, tmp_path):
    FakeOrchestrator.call_count = 0
    monkeypatch.setattr(generate_route, "Orchestrator", FakeOrchestrator)
    monkeypatch.setattr(generate_route, "load_settings", lambda: {"output_directory": str(tmp_path)})
    _patch_auth(monkeypatch)

    async def fake_get_provider_settings_none(token):
        # Simulates: no provider configured yet, OR the platform service being unreachable —
        # both must be treated identically: block generation, never fall back.
        return None

    monkeypatch.setattr(generate_route.platform_client, "get_provider_settings", fake_get_provider_settings_none)

    with TestClient(app) as client:
        with client.websocket_connect("/generate/ws") as ws:
            _authenticate(ws)
            ws.send_text('{"prompt": "Build a todo app with FastAPI and SQLite"}')
            data = ws.receive_json()
            assert data["event"] == "error"
            assert "provider configuration" in data["message"].lower()

    # The pipeline was never even constructed — no LLM call was ever attempted.
    assert FakeOrchestrator.call_count == 0
    assert list(tmp_path.iterdir()) == []


def test_orchestrator_never_falls_back_to_global_settings_json(monkeypatch):
    """Even if a legacy global settings.json still has provider fields on
    disk, Orchestrator must never read it — it only ever uses the
    provider_settings dict it was constructed with."""
    async def noop_emit(event):
        pass

    monkeypatch.setattr(
        "app.config.load_settings",
        lambda: {"provider": "groq", "groq_api_key": "GLOBAL_LEAKED_KEY", "groq_model": "global-model"},
    )

    orchestrator = Orchestrator(
        emit=noop_emit,
        provider_settings={"provider": "groq", "groq_api_key": "PER_USER_KEY", "groq_model": "per-user-model"},
    )

    assert orchestrator.provider.model == "per-user-model"
    assert orchestrator.provider.client.api_key == "PER_USER_KEY"


def test_two_orchestrators_with_different_provider_settings_stay_isolated():
    """Direct proof of the concurrency-isolation guarantee: two Orchestrator
    instances built with different per-user provider configs never share
    state — each carries only its own credentials, regardless of execution
    interleaving, because there is no global/shared provider object."""
    async def noop_emit(event):
        pass

    orchestrator_a = Orchestrator(
        emit=noop_emit,
        provider_settings={"provider": "groq", "groq_api_key": "KEY_A", "groq_model": "model-A"},
    )
    orchestrator_b = Orchestrator(
        emit=noop_emit,
        provider_settings={"provider": "groq", "groq_api_key": "KEY_B", "groq_model": "model-B"},
    )

    assert orchestrator_a.provider is not orchestrator_b.provider
    assert orchestrator_a.provider.model == "model-A"
    assert orchestrator_b.provider.model == "model-B"
    assert orchestrator_a.provider.client.api_key == "KEY_A"
    assert orchestrator_b.provider.client.api_key == "KEY_B"
