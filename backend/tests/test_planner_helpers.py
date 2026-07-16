from app.agents.planner_agent import _apply_defaults, _extract_json, _validate_plan


def test_extract_json_parses_clean_json():
    raw = '{"project_name": "todo_api", "description": "x"}'
    assert _extract_json(raw) == {"project_name": "todo_api", "description": "x"}


def test_extract_json_strips_markdown_fences():
    raw = '```json\n{"project_name": "todo_api"}\n```'
    assert _extract_json(raw) == {"project_name": "todo_api"}


def test_extract_json_finds_object_embedded_in_prose():
    raw = 'Sure, here is the plan:\n{"project_name": "todo_api"}\nLet me know if you need changes.'
    assert _extract_json(raw) == {"project_name": "todo_api"}


def test_extract_json_fixes_trailing_commas():
    raw = '{"a": 1, "b": [1, 2, 3,],}'
    result = _extract_json(raw)
    assert result == {"a": 1, "b": [1, 2, 3]}


def test_extract_json_returns_none_for_garbage():
    assert _extract_json("this is not json at all") is None


def test_validate_plan_reports_missing_required_fields():
    errors = _validate_plan({"project_name": "x"})
    assert any("description" in e for e in errors)
    assert any("technologies" in e for e in errors)


def test_validate_plan_passes_when_complete():
    plan = {
        "project_name": "x",
        "description": "x",
        "project_type": "backend_only",
        "technologies": {},
        "agents_required": [],
    }
    assert _validate_plan(plan) == []


def test_apply_defaults_fills_missing_coordination_fields():
    plan = {"project_name": "app", "technologies": {"backend": "fastapi", "database": "postgresql"}}
    _apply_defaults(plan)

    assert plan["entities"] == []
    assert plan["api_routes"] == []
    assert plan["dependencies"] == {"backend": [], "frontend": []}


def test_apply_defaults_derives_docker_entry_point_when_backend_present():
    # BackendAgent always writes a flat main.py at the project root, never nested
    # under a package folder — so the derived entry point must be flat "main:app",
    # not a dotted package path (confirmed by two live generations that showed a
    # dotted path pointing at a file that doesn't actually exist).
    plan = {"project_name": "myapp", "technologies": {"backend": "fastapi"}}
    _apply_defaults(plan)
    assert plan["docker_entry_point"] == "main:app"


def test_apply_defaults_skips_docker_entry_point_when_no_backend():
    plan = {"project_name": "myapp", "technologies": {"backend": "none"}}
    _apply_defaults(plan)
    assert plan["docker_entry_point"] == ""


def test_apply_defaults_injects_database_url_when_database_present():
    plan = {"project_name": "myapp", "technologies": {"database": "postgresql"}}
    _apply_defaults(plan)
    assert "DATABASE_URL" in plan["environment_variables"]


def test_apply_defaults_does_not_duplicate_database_url():
    plan = {
        "project_name": "myapp",
        "technologies": {"database": "postgresql"},
        "environment_variables": ["DATABASE_URL", "SECRET_KEY"],
    }
    _apply_defaults(plan)
    assert plan["environment_variables"].count("DATABASE_URL") == 1
