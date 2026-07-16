from app.agents.backend_agent import _drop_database_ownership_violations, _flatten_nested_layout


def test_flatten_leaves_already_flat_layout_untouched():
    files = {"main.py": "app", "routes/a.py": "x"}
    assert _flatten_nested_layout(dict(files)) == files


def test_flatten_strips_project_name_prefix_when_main_py_is_nested():
    """Confirmed live: BackendAgent nested its entire output under
    'future_tech_showcase/' instead of writing a flat main.py, causing the
    real Docker entry point ("main:app") to point at a file that doesn't exist."""
    files = {
        "future_tech_showcase/main.py": "app",
        "future_tech_showcase/routes/a.py": "x",
        "future_tech_showcase/schemas/b.py": "y",
        "future_tech_showcase/requirements.txt": "fastapi",
    }

    flattened = _flatten_nested_layout(files)

    assert flattened == {
        "main.py": "app",
        "routes/a.py": "x",
        "schemas/b.py": "y",
        "requirements.txt": "fastapi",
    }


def test_flatten_leaves_ambiguous_layout_alone():
    """If there's no single common prefix (or main.py isn't under it), don't
    guess — leave the files as-is rather than risk mangling a legitimate
    structure the LLM produced for a reason we don't understand."""
    files = {"foo/main.py": "app", "bar/other.py": "x"}
    assert _flatten_nested_layout(dict(files)) == files


def test_flatten_does_nothing_without_a_nested_main_py():
    files = {"routes/a.py": "x", "schemas/b.py": "y"}
    assert _flatten_nested_layout(dict(files)) == files


def test_drop_database_ownership_violations_removes_database_folder():
    """Confirmed live: BackendAgent generated its own database/models.py with
    a different Base and different field types than DatabaseAgent's canonical
    version — a direct violation of the "DatabaseAgent owns all models" rule
    that survived despite an explicit prompt instruction against it."""
    files = {
        "main.py": "app",
        "database/models.py": "class Technology(Base): pass",
        "database/__init__.py": "",
    }

    result, violations = _drop_database_ownership_violations(files)

    assert result == {"main.py": "app"}
    assert sorted(violations) == ["database/__init__.py", "database/models.py"]


def test_drop_database_ownership_violations_noop_when_none_present():
    files = {"main.py": "app", "routes/a.py": "x"}
    result, violations = _drop_database_ownership_violations(dict(files))
    assert result == files
    assert violations == []


def test_flatten_then_drop_database_violations_reproduces_full_fix():
    """Integration of both backstops against the exact real project layout
    that surfaced this bug — main.py ends up flat, and BackendAgent's
    conflicting database/ duplicate never reaches the final file set."""
    files = {
        "future_tech_showcase/.env.example": "X=1",
        "future_tech_showcase/main.py": "app",
        "future_tech_showcase/requirements.txt": "fastapi",
        "future_tech_showcase/routes/technology_routes.py": "router",
        "future_tech_showcase/database/models.py": "class Technology(Base): pass",
    }

    flattened = _flatten_nested_layout(files)
    final, violations = _drop_database_ownership_violations(flattened)

    assert "main.py" in final
    assert "database/models.py" not in final
    assert violations == ["database/models.py"]
