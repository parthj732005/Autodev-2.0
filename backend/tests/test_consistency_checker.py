from app.services import consistency_checker as cc


def test_run_reports_all_clean_when_everything_matches():
    files = {
        "main.py": '@router.get("/todos")\ndef list_todos(): ...\n',
        "requirements.txt": "fastapi\nuvicorn\n",
    }
    plan = {"technologies": {"backend": "fastapi", "database": "none"}, "docker_entry_point": ""}

    result = cc.run(files, plan)

    assert result["issues"] == []
    assert result["error_count"] == 0
    assert "passed" in result["summary"]


def test_frontend_call_with_no_matching_backend_route_is_flagged():
    files = {
        "main.py": '@router.get("/todos")\ndef list_todos(): ...\n',
        "src/App.jsx": 'fetch("/orders")',
    }
    plan = {"technologies": {}, "docker_entry_point": ""}

    result = cc.run(files, plan)

    checks = [i["check"] for i in result["issues"]]
    assert "frontend_backend_contract" in checks


def test_route_param_naming_differences_do_not_false_positive():
    """{id} vs :id vs <id> should all be treated as equivalent."""
    files = {
        "main.py": '@router.get("/todos/{id}")\ndef get_todo(): ...\n',
        "src/App.jsx": 'fetch("/todos/:id")',
    }
    plan = {"technologies": {}, "docker_entry_point": ""}

    result = cc.run(files, plan)

    assert result["issues"] == []


def test_docker_entry_point_mismatch_is_flagged_as_error():
    files = {
        "Dockerfile": 'CMD ["uvicorn", "wrong_module.main:app", "--host", "0.0.0.0"]',
        "todo_api/main.py": "app = FastAPI()",
    }
    plan = {"technologies": {}, "docker_entry_point": "todo_api.main:app"}

    result = cc.run(files, plan)

    checks = [i["check"] for i in result["issues"]]
    assert "docker_entry_point" in checks
    assert result["error_count"] >= 1


def test_missing_entry_point_module_is_flagged():
    """This is the exact bug PlannerAgent used to have: it defaulted
    docker_entry_point to a dotted package path ("todo_api.main:app"), but
    BackendAgent always writes a flat main.py at the project root — so the
    dotted path pointed at a file that never existed. Confirmed live on two
    real generations (url_shortener, maldives_travel_guide) before the
    Planner default was fixed to emit flat "main:app" instead."""
    files = {"main.py": "app = FastAPI()"}
    plan = {"technologies": {}, "docker_entry_point": "todo_api.main:app"}

    result = cc.run(files, plan)

    checks = [i["check"] for i in result["issues"]]
    assert "entry_point_exists" in checks


def test_flat_entry_point_matches_flat_main_file_no_false_positive():
    """Regression test for the fix: with the corrected flat "main:app" format,
    a flat main.py at the project root must NOT be falsely flagged as missing."""
    files = {"main.py": "app = FastAPI()"}
    plan = {"technologies": {}, "docker_entry_point": "main:app"}

    result = cc.run(files, plan)

    checks = [i["check"] for i in result["issues"]]
    assert "entry_point_exists" not in checks
    assert "docker_entry_point" not in checks


def test_entry_point_exists_uses_exact_path_not_suffix_match():
    """Confirmed live false-negative: two files were both named main.py
    ("backend/main.py" — a stray DevOpsAgent-generated placeholder — and
    "future_tech_showcase/main.py" — the real entry point), but NEITHER was
    at the flat "main.py" path the plan actually required. The old
    endswith()-based check missed this entirely because *some* file ending
    in "main.py" existed somewhere in the tree. It must check the exact
    relative path, not merely a matching filename anywhere in the project."""
    files = {
        "backend/main.py": "app = FastAPI()",
        "future_tech_showcase/main.py": "app = FastAPI()",
    }
    plan = {"technologies": {}, "docker_entry_point": "main:app"}

    result = cc.run(files, plan)

    checks = [i["check"] for i in result["issues"]]
    assert "entry_point_exists" in checks


def test_missing_backend_framework_in_requirements_is_flagged():
    files = {"requirements.txt": "uvicorn\npydantic\n"}
    plan = {"technologies": {"backend": "fastapi"}, "docker_entry_point": ""}

    result = cc.run(files, plan)

    checks = [i["check"] for i in result["issues"]]
    assert "requirements_framework" in checks


def test_missing_db_driver_in_requirements_is_flagged():
    files = {"requirements.txt": "fastapi\nuvicorn\n"}
    plan = {"technologies": {"backend": "fastapi", "database": "postgresql"}, "docker_entry_point": ""}

    result = cc.run(files, plan)

    checks = [i["check"] for i in result["issues"]]
    assert "requirements_db_driver" in checks


def test_present_db_driver_does_not_flag():
    files = {"requirements.txt": "fastapi\nuvicorn\npsycopg2==2.9.9\n"}
    plan = {"technologies": {"backend": "fastapi", "database": "postgresql"}, "docker_entry_point": ""}

    result = cc.run(files, plan)

    checks = [i["check"] for i in result["issues"]]
    assert "requirements_db_driver" not in checks


def test_missing_env_var_in_env_example_is_flagged():
    files = {".env.example": "SECRET_KEY=\n"}
    plan = {"technologies": {}, "environment_variables": ["DATABASE_URL", "SECRET_KEY"], "docker_entry_point": ""}

    result = cc.run(files, plan)

    checks = [i["check"] for i in result["issues"]]
    assert "env_vars_documented" in checks
    messages = " ".join(i["message"] for i in result["issues"])
    assert "DATABASE_URL" in messages


def test_duplicate_model_definition_is_flagged():
    files = {
        "database/models.py": "class User(Base):\n    id = Column(Integer)\n",
        "routes/user_routes.py": "class User(Base):\n    id = Column(Integer)\n",
    }
    plan = {"technologies": {}, "docker_entry_point": ""}

    result = cc.run(files, plan)

    checks = [i["check"] for i in result["issues"]]
    assert "duplicate_models" in checks


def test_duplicate_model_definition_is_severity_error_not_warning():
    """Two conflicting schema definitions for the same entity is a real
    correctness problem, confirmed live (a canonical model with a proper
    ForeignKey/relationship vs. a duplicate with different field types and
    no relationship at all) — it must surface as an error, not a warning."""
    files = {
        "database/models.py": "class User(Base):\n    id = Column(Integer)\n",
        "routes/user_routes.py": "class User(Base):\n    id = Column(Integer)\n",
    }
    plan = {"technologies": {}, "docker_entry_point": ""}

    result = cc.run(files, plan)

    dup_issues = [i for i in result["issues"] if i["check"] == "duplicate_models"]
    assert dup_issues and all(i["severity"] == "error" for i in dup_issues)
    assert result["error_count"] >= 1


def test_readme_documents_nonexistent_route_is_flagged_as_info():
    files = {
        "main.py": '@router.get("/todos")\ndef list_todos(): ...\n',
        "README.md": "## API\nGET /todos\nPOST /todos\n",  # POST /todos doesn't exist in the backend
    }
    plan = {"technologies": {}, "docker_entry_point": ""}

    result = cc.run(files, plan)

    checks = [i["check"] for i in result["issues"]]
    assert "documentation_contract" in checks
    contract_issues = [i for i in result["issues"] if i["check"] == "documentation_contract"]
    assert all(i["severity"] == "info" for i in contract_issues)


def test_backend_route_missing_from_readme_is_flagged_as_info():
    files = {
        "main.py": '@router.get("/todos")\ndef list_todos(): ...\n@router.post("/todos")\ndef create_todo(): ...\n',
        "README.md": "## API\nGET /todos\n",  # POST /todos exists in backend but isn't documented
    }
    plan = {"technologies": {}, "docker_entry_point": ""}

    result = cc.run(files, plan)

    checks = [i["check"] for i in result["issues"]]
    assert "documentation_completeness" in checks
    completeness_issues = [i for i in result["issues"] if i["check"] == "documentation_completeness"]
    assert all(i["severity"] == "info" for i in completeness_issues)


def test_route_matches_any_ignores_path_param_style_differences():
    assert cc._route_matches_any("GET /todos/{id}", {"GET /todos/:id"})
    assert cc._route_matches_any("GET /todos/<id>", {"GET /todos/{item_id}"})
    assert not cc._route_matches_any("GET /todos", {"POST /todos"})


def test_extract_requirements_strips_version_specifiers():
    files = {"requirements.txt": "fastapi==0.115.0\nuvicorn>=0.30\n# comment\n\n"}
    pkgs = cc._extract_requirements(files)
    assert pkgs == {"fastapi", "uvicorn"}


def test_extract_requirements_none_when_file_absent():
    assert cc._extract_requirements({}) is None
