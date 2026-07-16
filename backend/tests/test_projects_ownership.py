import json

from fastapi.testclient import TestClient

from app.main import app
from app.routes import projects as projects_route


def _auth_headers():
    return {"Authorization": "Bearer good-token"}


def _mock_user(monkeypatch):
    async def fake_get_current_user(token):
        return {"id": "u1", "email": "demo@example.com"}

    monkeypatch.setattr(projects_route.platform_client, "get_current_user", fake_get_current_user)


def _write_disk_project(tmp_path, name, **meta_overrides):
    project_dir = tmp_path / name
    project_dir.mkdir()
    meta = {
        "project_name": name,
        "description": "test",
        "technologies": {},
        "files": ["main.py"],
        "file_count": 1,
        "validation_report": {"passed": [], "warnings": [], "errors": []},
    }
    meta.update(meta_overrides)
    (project_dir / "main.py").write_text("print('hi')\n")
    (project_dir / projects_route.META_FILE).write_text(json.dumps(meta))
    return project_dir


def test_unauthenticated_access_is_rejected(tmp_path):
    with TestClient(app) as client:
        resp = client.get("/projects/generated/anything")
    assert resp.status_code == 401


def test_owned_project_detail_access_succeeds(monkeypatch, tmp_path):
    _mock_user(monkeypatch)
    monkeypatch.setattr(projects_route, "load_settings", lambda: {"output_directory": str(tmp_path)})
    project_dir = _write_disk_project(tmp_path, "owned_proj")

    async def fake_get_owned_project(token, project_key):
        return {"projectKey": "owned_proj", "outputPath": str(project_dir)}

    monkeypatch.setattr(projects_route.platform_client, "get_owned_project", fake_get_owned_project)

    with TestClient(app) as client:
        resp = client.get("/projects/generated/owned_proj", headers=_auth_headers())

    assert resp.status_code == 200
    assert resp.json()["project_name"] == "owned_proj"


def test_cross_user_project_detail_access_is_rejected(monkeypatch, tmp_path):
    _mock_user(monkeypatch)
    monkeypatch.setattr(projects_route, "load_settings", lambda: {"output_directory": str(tmp_path)})
    _write_disk_project(tmp_path, "someone_elses_proj")

    async def fake_get_owned_project(token, project_key):
        # Platform service says: not found / not yours — same response either way.
        return None

    monkeypatch.setattr(projects_route.platform_client, "get_owned_project", fake_get_owned_project)

    with TestClient(app) as client:
        resp = client.get("/projects/generated/someone_elses_proj", headers=_auth_headers())

    assert resp.status_code == 404


def test_cross_user_setup_instructions_access_is_rejected(monkeypatch, tmp_path):
    _mock_user(monkeypatch)
    monkeypatch.setattr(projects_route, "load_settings", lambda: {"output_directory": str(tmp_path)})
    _write_disk_project(tmp_path, "someone_elses_proj2")

    async def fake_get_owned_project(token, project_key):
        return None

    monkeypatch.setattr(projects_route.platform_client, "get_owned_project", fake_get_owned_project)

    with TestClient(app) as client:
        resp = client.post(
            "/projects/generated/someone_elses_proj2/setup-instructions", headers=_auth_headers()
        )

    assert resp.status_code == 404


def test_cross_user_open_vscode_access_is_rejected(monkeypatch, tmp_path):
    _mock_user(monkeypatch)
    monkeypatch.setattr(projects_route, "load_settings", lambda: {"output_directory": str(tmp_path)})
    _write_disk_project(tmp_path, "someone_elses_proj3")

    async def fake_get_owned_project(token, project_key):
        return None

    monkeypatch.setattr(projects_route.platform_client, "get_owned_project", fake_get_owned_project)

    with TestClient(app) as client:
        resp = client.post("/projects/generated/someone_elses_proj3/open-vscode", headers=_auth_headers())

    assert resp.status_code == 404


def test_ownerless_legacy_projects_excluded_from_normal_listing(monkeypatch, tmp_path):
    _mock_user(monkeypatch)
    monkeypatch.setattr(projects_route, "load_settings", lambda: {"output_directory": str(tmp_path)})
    # A legacy project exists on disk but platform-service has no ownership record for it.
    _write_disk_project(tmp_path, "legacy_orphan_proj")

    async def fake_list_owned_projects(token):
        return []

    monkeypatch.setattr(projects_route.platform_client, "list_owned_projects", fake_list_owned_projects)

    with TestClient(app) as client:
        resp = client.get("/projects/generated", headers=_auth_headers())

    assert resp.status_code == 200
    assert resp.json() == []


def test_listing_shows_only_owned_projects_not_legacy_ones(monkeypatch, tmp_path):
    _mock_user(monkeypatch)
    monkeypatch.setattr(projects_route, "load_settings", lambda: {"output_directory": str(tmp_path)})
    owned_dir = _write_disk_project(tmp_path, "my_owned_proj")
    _write_disk_project(tmp_path, "legacy_orphan_proj")

    async def fake_list_owned_projects(token):
        return [{"projectKey": "my_owned_proj", "outputPath": str(owned_dir)}]

    monkeypatch.setattr(projects_route.platform_client, "list_owned_projects", fake_list_owned_projects)

    with TestClient(app) as client:
        resp = client.get("/projects/generated", headers=_auth_headers())

    assert resp.status_code == 200
    names = [p["project_name"] for p in resp.json()]
    assert names == ["my_owned_proj"]


def test_output_path_dotdot_traversal_is_rejected(monkeypatch, tmp_path):
    _mock_user(monkeypatch)
    monkeypatch.setattr(projects_route, "load_settings", lambda: {"output_directory": str(tmp_path)})

    escaping_path = str(tmp_path / "sub" / ".." / ".." / "escaped_via_traversal")

    async def fake_get_owned_project(token, project_key):
        return {"projectKey": "sneaky", "outputPath": escaping_path}

    monkeypatch.setattr(projects_route.platform_client, "get_owned_project", fake_get_owned_project)

    with TestClient(app) as client:
        resp = client.get("/projects/generated/sneaky", headers=_auth_headers())

    assert resp.status_code == 500
    assert "outside the configured output directory" in resp.json()["detail"]


def test_output_path_absolute_escape_is_rejected(monkeypatch, tmp_path):
    _mock_user(monkeypatch)
    monkeypatch.setattr(projects_route, "load_settings", lambda: {"output_directory": str(tmp_path)})

    # A wholly different absolute directory, nowhere near the configured output root.
    escaping_path = str(tmp_path.parent / "totally_different_directory")

    async def fake_get_owned_project(token, project_key):
        return {"projectKey": "escape-abs", "outputPath": escaping_path}

    monkeypatch.setattr(projects_route.platform_client, "get_owned_project", fake_get_owned_project)

    with TestClient(app) as client:
        resp = client.get("/projects/generated/escape-abs", headers=_auth_headers())

    assert resp.status_code == 500
    assert "outside the configured output directory" in resp.json()["detail"]
