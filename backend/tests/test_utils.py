from app.agents.utils import (
    format_api_routes,
    format_entities,
    format_env_vars,
    format_shared_context,
    parse_files,
    strip_fences,
)


def test_format_api_routes_empty_when_no_routes():
    assert format_api_routes({"api_routes": []}) == ""


def test_format_api_routes_lists_every_route():
    out = format_api_routes({"api_routes": ["GET /todos", "POST /todos"]})
    assert "GET /todos" in out
    assert "POST /todos" in out
    assert "API CONTRACT" in out


def test_format_entities_points_to_canonical_source():
    out = format_entities({"entities": ["User", "Todo"]})
    assert "database/models.py" in out
    assert "User" in out and "Todo" in out


def test_format_entities_empty_when_no_entities():
    assert format_entities({"entities": []}) == ""


def test_format_env_vars_empty_when_none():
    assert format_env_vars({"environment_variables": []}) == ""


def test_format_env_vars_lists_all():
    out = format_env_vars({"environment_variables": ["DATABASE_URL", "SECRET_KEY"]})
    assert "DATABASE_URL" in out
    assert "SECRET_KEY" in out


def test_format_shared_context_respects_include_filter():
    plan = {
        "api_routes": ["GET /x"],
        "entities": ["X"],
        "environment_variables": ["DATABASE_URL"],
    }
    routes_only = format_shared_context(plan, include=("routes",))
    assert "GET /x" in routes_only
    assert "DATABASE MODELS" not in routes_only
    assert "ENVIRONMENT VARIABLES" not in routes_only


def test_format_shared_context_empty_when_plan_has_nothing():
    assert format_shared_context({}) == ""


def test_strip_fences_removes_markdown_code_fence():
    raw = "```python\nprint(1)\n```"
    assert strip_fences(raw) == "print(1)"


def test_strip_fences_noop_on_plain_text():
    assert strip_fences("print(1)") == "print(1)"


def test_parse_files_splits_multiple_file_blocks():
    raw = "### filename: a.py\nprint(1)\n### filename: b.py\nprint(2)\n"
    files = parse_files(raw)
    assert files["a.py"].strip() == "print(1)"
    assert files["b.py"].strip() == "print(2)"


def test_parse_files_falls_back_to_single_file_when_no_headers():
    files = parse_files("print(1)", fallback="main.py")
    assert files == {"main.py": "print(1)"}


def test_parse_files_returns_empty_when_no_headers_and_no_fallback():
    assert parse_files("print(1)") == {}
