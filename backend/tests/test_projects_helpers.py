import pytest
from fastapi import HTTPException

from app.routes.projects import _SAFE_PROJECT_NAME, _detect_frontend_dir, _load_meta


def test_detect_frontend_dir_at_project_root():
    assert _detect_frontend_dir(["main.py", "src/App.jsx", "package.json", "index.html"]) == "(project root)"


def test_detect_frontend_dir_in_subfolder():
    files = ["backend/main.py", "frontend/package.json", "frontend/src/App.jsx"]
    assert _detect_frontend_dir(files) == "frontend"


def test_detect_frontend_dir_handles_windows_backslashes():
    files = ["backend\\main.py", "client\\package.json", "client\\src\\index.jsx"]
    assert _detect_frontend_dir(files) == "client"


def test_detect_frontend_dir_falls_back_when_no_package_json():
    assert _detect_frontend_dir(["main.py"]) == "(project root)"


def test_safe_project_name_allows_normal_names():
    assert _SAFE_PROJECT_NAME.match("url_shortener")
    assert _SAFE_PROJECT_NAME.match("todo-api-2")


def test_safe_project_name_rejects_shell_injection_attempt():
    # The exact case found and fixed this session: a project name that could
    # break out of a shell=True subprocess.Popen() quoting.
    malicious = 'foo" & calc.exe & "'
    assert not _SAFE_PROJECT_NAME.match(malicious)


def test_safe_project_name_rejects_path_traversal():
    assert not _SAFE_PROJECT_NAME.match("../../etc/passwd")
    assert not _SAFE_PROJECT_NAME.match("..\\..\\windows")


def test_load_meta_rejects_invalid_project_name():
    with pytest.raises(HTTPException) as exc_info:
        _load_meta('foo" & calc.exe & "')
    assert exc_info.value.status_code == 400


def test_load_meta_404s_for_nonexistent_project():
    with pytest.raises(HTTPException) as exc_info:
        _load_meta("a_project_that_definitely_does_not_exist_12345")
    assert exc_info.value.status_code == 404
