from fastapi.testclient import TestClient

from app.main import app
from app.routes import generate as generate_route


def _mock_current_user(monkeypatch, user):
    async def fake_get_current_user(token):
        return user
    monkeypatch.setattr(generate_route.platform_client, "get_current_user", fake_get_current_user)


def test_ws_rejects_first_message_without_authenticate_type(monkeypatch):
    with TestClient(app) as client:
        with client.websocket_connect("/generate/ws") as ws:
            ws.send_text('{"prompt": "Build a todo app with FastAPI"}')
            data = ws.receive_json()
            assert data["event"] == "error"
            assert "Authentication required" in data["message"]


def test_ws_rejects_missing_token_in_authenticate_message(monkeypatch):
    with TestClient(app) as client:
        with client.websocket_connect("/generate/ws") as ws:
            ws.send_text('{"type": "authenticate"}')
            data = ws.receive_json()
            assert data["event"] == "error"
            assert "Authentication required" in data["message"]


def test_ws_rejects_invalid_or_expired_token(monkeypatch):
    _mock_current_user(monkeypatch, None)  # platform service says: not a valid session
    with TestClient(app) as client:
        with client.websocket_connect("/generate/ws") as ws:
            ws.send_text('{"type": "authenticate", "token": "bad-token"}')
            data = ws.receive_json()
            assert data["event"] == "error"
            assert "Authentication failed" in data["message"]


def test_ws_accepts_valid_token_and_sends_authenticated_event(monkeypatch):
    _mock_current_user(monkeypatch, {"id": "u1", "email": "demo@example.com"})
    with TestClient(app) as client:
        with client.websocket_connect("/generate/ws") as ws:
            ws.send_text('{"type": "authenticate", "token": "good-token"}')
            data = ws.receive_json()
            assert data["event"] == "authenticated"
            assert "demo@example.com" in data["message"]
