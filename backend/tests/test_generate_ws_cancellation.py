import asyncio

from fastapi.testclient import TestClient

from app.main import app
from app.routes import generate as generate_route


class SlowCancellableOrchestrator:
    """Simulates a long-running generation (in place of a real multi-minute
    LLM pipeline) so the existing Stop/cancel race can be verified quickly
    and deterministically. Confirms the auth handshake added in Phase 5
    did not disturb the pre-existing asyncio.wait(FIRST_COMPLETED) racing
    or cancellation semantics in generate.py.
    """

    was_cancelled = False

    def __init__(self, emit, provider_settings, provider_override=None):
        self._emit = emit

    async def run(self, prompt):
        try:
            await asyncio.sleep(5)
            return {
                "plan": {"project_name": "should_not_exist_if_cancelled"},
                "files": {},
                "validation_report": {"passed": [], "warnings": [], "errors": []},
                "valid": True,
                "consistency_report": {},
                "repair_report": {"attempted": [], "repaired": [], "reverted": []},
            }
        except asyncio.CancelledError:
            SlowCancellableOrchestrator.was_cancelled = True
            raise


def test_cancel_message_actually_interrupts_in_flight_generation(monkeypatch, tmp_path):
    SlowCancellableOrchestrator.was_cancelled = False
    monkeypatch.setattr(generate_route, "Orchestrator", SlowCancellableOrchestrator)
    monkeypatch.setattr(generate_route, "load_settings", lambda: {"output_directory": str(tmp_path)})

    async def fake_get_current_user(token):
        return {"id": "u1", "email": "demo@example.com"}

    async def fake_get_provider_settings(token):
        return {"provider": "groq", "groq_api_key": "test-key", "groq_model": "test-model"}

    monkeypatch.setattr(generate_route.platform_client, "get_current_user", fake_get_current_user)
    monkeypatch.setattr(generate_route.platform_client, "get_provider_settings", fake_get_provider_settings)

    with TestClient(app) as client:
        with client.websocket_connect("/generate/ws") as ws:
            ws.send_text('{"type": "authenticate", "token": "good-token"}')
            ack = ws.receive_json()
            assert ack["event"] == "authenticated"

            ws.send_text('{"prompt": "Build a todo app with FastAPI and SQLite"}')
            # Any text received during generation is treated as cancel — matches
            # the existing (untouched) semantics documented in generate.py.
            ws.send_text('{"action": "cancel"}')

            data = ws.receive_json()
            assert data["event"] == "cancelled"
            assert "no project was saved" in data["message"].lower()

    # The in-flight orchestrator task was actually cancelled server-side —
    # not just a client-side socket close while the LLM call kept running.
    assert SlowCancellableOrchestrator.was_cancelled is True

    # Nothing was written to disk — cancellation happened before ProjectGenerator ran.
    assert list(tmp_path.iterdir()) == []
