import httpx

from app.services import platform_client


class FakeResponse:
    def __init__(self, status_code, json_data=None, text=""):
        self.status_code = status_code
        self._json = json_data or {}
        self.text = text

    def json(self):
        return self._json


class FakeAsyncClient:
    """Scripts a sequence of responses (or exceptions) for successive
    get/post/patch calls, in the order platform_client makes them."""

    def __init__(self, responses):
        self._responses = list(responses)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    async def _next(self):
        item = self._responses.pop(0)
        if isinstance(item, Exception):
            raise item
        return item

    async def get(self, *args, **kwargs):
        return await self._next()

    async def post(self, *args, **kwargs):
        return await self._next()

    async def patch(self, *args, **kwargs):
        return await self._next()


def _script(monkeypatch, responses):
    monkeypatch.setattr(platform_client.httpx, "AsyncClient", lambda **kw: FakeAsyncClient(responses))


async def test_get_current_user_returns_none_when_token_missing():
    assert await platform_client.get_current_user("") is None
    assert await platform_client.get_current_user(None) is None


async def test_get_current_user_returns_user_on_200(monkeypatch):
    _script(monkeypatch, [FakeResponse(200, {"id": "u1", "email": "a@b.com"})])
    user = await platform_client.get_current_user("sometoken")
    assert user == {"id": "u1", "email": "a@b.com"}


async def test_get_current_user_returns_none_on_401(monkeypatch):
    _script(monkeypatch, [FakeResponse(401)])
    assert await platform_client.get_current_user("badtoken") is None


async def test_get_current_user_returns_none_when_platform_service_unreachable(monkeypatch):
    monkeypatch.setattr(
        platform_client.httpx,
        "AsyncClient",
        lambda **kw: FakeAsyncClient([httpx.ConnectError("connection refused")]),
    )
    assert await platform_client.get_current_user("sometoken") is None


async def test_sync_completed_project_succeeds_when_both_calls_ok(monkeypatch):
    _script(monkeypatch, [
        FakeResponse(201, {"id": "proj-1"}),
        FakeResponse(200, {"status": "COMPLETED"}),
    ])
    ok = await platform_client.sync_completed_project(
        token="tok", project_key="demo", name="Demo", tech_stack="fastapi+react", output_path="/tmp/demo"
    )
    assert ok is True


async def test_sync_completed_project_fails_when_create_returns_error(monkeypatch):
    _script(monkeypatch, [FakeResponse(500, text="internal error")])
    ok = await platform_client.sync_completed_project(
        token="tok", project_key="demo", name="Demo", tech_stack="x", output_path="/tmp/demo"
    )
    assert ok is False


async def test_sync_completed_project_fails_when_status_update_returns_error(monkeypatch):
    _script(monkeypatch, [
        FakeResponse(201, {"id": "proj-1"}),
        FakeResponse(500, text="internal error"),
    ])
    ok = await platform_client.sync_completed_project(
        token="tok", project_key="demo", name="Demo", tech_stack="x", output_path="/tmp/demo"
    )
    assert ok is False


async def test_sync_completed_project_fails_when_platform_service_unreachable(monkeypatch):
    monkeypatch.setattr(
        platform_client.httpx,
        "AsyncClient",
        lambda **kw: FakeAsyncClient([httpx.ConnectError("connection refused")]),
    )
    ok = await platform_client.sync_completed_project(
        token="tok", project_key="demo", name="Demo", tech_stack="x", output_path="/tmp/demo"
    )
    assert ok is False
