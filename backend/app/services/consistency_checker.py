"""
Deterministic cross-agent consistency checker.
Pure Python — no LLM calls, no network, fast.

Checks that the generated files are internally consistent:
- Frontend API calls match backend routes
- README documents the same routes as the backend
- Docker entry point matches an actual file
- requirements.txt includes the main framework
- .env.example covers the expected environment variables
- Test files reference routes that exist in the backend
"""
import re
from typing import NamedTuple


class ConsistencyIssue(NamedTuple):
    check: str
    severity: str      # "error" | "warning" | "info"
    message: str
    suggestion: str


def run(files: dict, plan: dict) -> dict:
    """
    Run all consistency checks.
    Returns {"issues": [...], "summary": str, "checks_run": int}
    """
    issues: list[ConsistencyIssue] = []

    planned_routes = _normalise_routes(plan.get("api_routes", []))
    planned_env_vars = set(plan.get("environment_variables", []))
    docker_entry_point = plan.get("docker_entry_point", "")

    # Extract evidence from generated files
    backend_routes = _extract_backend_routes(files)
    frontend_calls = _extract_frontend_calls(files)
    readme_routes = _extract_readme_routes(files)
    test_routes = _extract_test_routes(files)
    env_example_vars = _extract_env_example_vars(files)
    requirements_pkgs = _extract_requirements(files)
    docker_cmd_entry = _extract_docker_entry(files)
    python_imports = _extract_python_top_imports(files)

    checks_run = 0

    # ── Check 1: Frontend calls → Backend routes ──────────────────────────────
    if frontend_calls and backend_routes:
        checks_run += 1
        for call in frontend_calls:
            if not _route_matches_any(call, backend_routes):
                issues.append(ConsistencyIssue(
                    check="frontend_backend_contract",
                    severity="warning",
                    message=f"Frontend calls '{call}' but no matching backend route found",
                    suggestion=f"Add route '{call}' to the backend or fix the frontend call",
                ))

    # ── Check 2: Test routes → Backend routes ────────────────────────────────
    if test_routes and backend_routes:
        checks_run += 1
        for route in test_routes:
            if not _route_matches_any(route, backend_routes):
                issues.append(ConsistencyIssue(
                    check="test_backend_contract",
                    severity="warning",
                    message=f"Test targets '{route}' but no matching backend route found",
                    suggestion=f"Remove or update test for '{route}', or add the missing backend route",
                ))

    # ── Check 3: README routes → Backend routes ──────────────────────────────
    if readme_routes and backend_routes:
        checks_run += 1
        for route in readme_routes:
            if not _route_matches_any(route, backend_routes):
                issues.append(ConsistencyIssue(
                    check="documentation_contract",
                    severity="info",
                    message=f"README documents '{route}' but no matching backend route found",
                    suggestion="Update README to remove undocumented/non-existent route",
                ))

    # ── Check 4: Backend routes → README ─────────────────────────────────────
    if backend_routes and readme_routes:
        checks_run += 1
        for route in backend_routes:
            if not _route_matches_any(route, readme_routes):
                issues.append(ConsistencyIssue(
                    check="documentation_completeness",
                    severity="info",
                    message=f"Backend route '{route}' is not documented in README",
                    suggestion="Add this endpoint to the README API section",
                ))

    # ── Check 5: Docker entry point → actual files ───────────────────────────
    if docker_cmd_entry and docker_cmd_entry != docker_entry_point and docker_entry_point:
        checks_run += 1
        issues.append(ConsistencyIssue(
            check="docker_entry_point",
            severity="error",
            message=f"Dockerfile uses '{docker_cmd_entry}' but planned entry is '{docker_entry_point}'",
            suggestion=f"Update Dockerfile CMD to: uvicorn {docker_entry_point} --host 0.0.0.0 --port 8000",
        ))

    # Also verify the entry point module file actually exists at EXACTLY that
    # path. A suffix/endswith match here would be satisfied by any stray file
    # sharing the same filename elsewhere in the tree (e.g. a placeholder
    # "backend/main.py" alongside the real entry point at a different path) —
    # confirmed as a real false-negative on a live generation, where neither
    # of two same-named main.py files was actually at the required location.
    if docker_entry_point:
        checks_run += 1
        module_path = docker_entry_point.split(":")[0].replace(".", "/") + ".py"
        normalized_files = {f.replace("\\", "/") for f in files}
        if module_path not in normalized_files:
            issues.append(ConsistencyIssue(
                check="entry_point_exists",
                severity="error",
                message=f"Docker entry point module '{module_path}' not found in generated files",
                suggestion=f"Ensure BackendAgent creates {module_path} or update docker_entry_point in the plan",
            ))

    # ── Check 6: .env.example covers planned env vars ────────────────────────
    if planned_env_vars and env_example_vars is not None:
        checks_run += 1
        missing = planned_env_vars - env_example_vars
        for var in sorted(missing):
            issues.append(ConsistencyIssue(
                check="env_vars_documented",
                severity="warning",
                message=f"Environment variable '{var}' planned but not in .env.example",
                suggestion=f"Add '{var}=' to .env.example",
            ))

    # ── Check 7: requirements.txt includes the main framework ────────────────
    if requirements_pkgs is not None:
        checks_run += 1
        framework = plan.get("technologies", {}).get("backend", "none")
        if framework and framework != "none" and framework not in requirements_pkgs:
            issues.append(ConsistencyIssue(
                check="requirements_framework",
                severity="error",
                message=f"Backend framework '{framework}' not found in requirements.txt",
                suggestion=f"Add '{framework}' to requirements.txt",
            ))

        # Check DB driver
        db = plan.get("technologies", {}).get("database", "none")
        db_drivers = {"postgresql": ["psycopg2", "asyncpg"], "mysql": ["pymysql", "aiomysql"]}
        if db in db_drivers:
            drivers = db_drivers[db]
            if not any(d in requirements_pkgs for d in drivers):
                issues.append(ConsistencyIssue(
                    check="requirements_db_driver",
                    severity="warning",
                    message=f"Database '{db}' selected but no driver found in requirements.txt (expected one of: {drivers})",
                    suggestion=f"Add '{drivers[0]}' or '{drivers[1]}' to requirements.txt",
                ))

    # ── Check 8: Duplicate model definitions ─────────────────────────────────
    checks_run += 1
    model_defs = _find_model_definitions(files)
    seen: dict[str, list[str]] = {}
    for filepath, model_name in model_defs:
        seen.setdefault(model_name, []).append(filepath)
    for model_name, locations in seen.items():
        if len(locations) > 1:
            issues.append(ConsistencyIssue(
                check="duplicate_models",
                # Two conflicting schema definitions for the same entity is a
                # correctness-breaking problem (confirmed live: one generation
                # had a canonical model with a ForeignKey/relationship and a
                # duplicate with different field types and no relationship at
                # all) — not a style nit, so it belongs at "error", not "warning".
                severity="error",
                message=f"Model '{model_name}' defined in multiple files: {locations}",
                suggestion=f"Keep '{model_name}' only in database/models.py and import it everywhere else",
            ))

    return {
        "issues": [i._asdict() for i in issues],
        "checks_run": checks_run,
        "error_count": sum(1 for i in issues if i.severity == "error"),
        "warning_count": sum(1 for i in issues if i.severity == "warning"),
        "info_count": sum(1 for i in issues if i.severity == "info"),
        "summary": (
            f"{len(issues)} consistency issue(s) found across {checks_run} checks"
            if issues
            else f"All {checks_run} consistency checks passed"
        ),
    }


# ─── Extractors ───────────────────────────────────────────────────────────────

def _extract_backend_routes(files: dict) -> set[str]:
    """Find route decorators in Python files."""
    routes = set()
    pattern = re.compile(
        r'@(?:router|app)\.(get|post|put|patch|delete|options|head)\s*\(\s*["\']([^"\']+)["\']',
        re.IGNORECASE,
    )
    for filepath, content in files.items():
        if not filepath.endswith(".py"):
            continue
        for method, path in pattern.findall(content):
            routes.add(f"{method.upper()} {path}")
    return routes


def _extract_frontend_calls(files: dict) -> set[str]:
    """Find API calls in JS/JSX files, tagged with an HTTP method so they can
    be compared against backend routes (which are always "METHOD /path").
    fetch()/request() calls don't reliably expose their method via regex, so
    they default to GET — the actual default HTTP method when none is given."""
    calls = set()
    # fetch("/path") or fetch(`${BASE}/path`) or axios.get("/path")
    fetch_pattern = re.compile(r'fetch\s*\(\s*["`\'](?:\$\{[^}]+\})?(/[^"\'`\s]+)', re.IGNORECASE)
    axios_pattern = re.compile(
        r'axios\s*\.\s*(get|post|put|patch|delete)\s*\(\s*["`\'](?:\$\{[^}]+\})?(/[^"\'`\s]+)', re.IGNORECASE
    )
    request_pattern = re.compile(r'request\s*\(\s*["`\']([^"\'`\s]+)["`\']', re.IGNORECASE)

    for filepath, content in files.items():
        if not filepath.endswith((".js", ".jsx", ".ts", ".tsx")):
            continue
        for m in fetch_pattern.finditer(content):
            path = m.group(1)
            if path.startswith("/") and not path.startswith("//"):
                calls.add(f"GET {path}")
        for m in axios_pattern.finditer(content):
            method, path = m.groups()
            if path.startswith("/") and not path.startswith("//"):
                calls.add(f"{method.upper()} {path}")
        for m in request_pattern.finditer(content):
            path = m.group(1)
            if path.startswith("/") and not path.startswith("//"):
                calls.add(f"GET {path}")
    return calls


def _extract_readme_routes(files: dict) -> set[str]:
    """Find route definitions in README.md."""
    routes = set()
    readme = files.get("README.md") or files.get("readme.md") or ""
    if not readme:
        return routes
    pattern = re.compile(
        r'\b(GET|POST|PUT|PATCH|DELETE)\b\s+(/[^\s|`\n]+)',
        re.IGNORECASE,
    )
    for method, path in pattern.findall(readme):
        routes.add(f"{method.upper()} {path.rstrip('|').strip()}")
    return routes


def _extract_test_routes(files: dict) -> set[str]:
    """Find route strings referenced in test files."""
    routes = set()
    pattern = re.compile(r'client\.(get|post|put|patch|delete)\s*\(\s*["\']([^"\']+)["\']', re.IGNORECASE)
    for filepath, content in files.items():
        if "test" not in filepath.lower() or not filepath.endswith(".py"):
            continue
        for method, path in pattern.findall(content):
            routes.add(f"{method.upper()} {path}")
    return routes


def _extract_env_example_vars(files: dict) -> set[str] | None:
    """Return set of var names from .env.example, or None if file absent."""
    content = files.get(".env.example")
    if content is None:
        return None
    vars_ = set()
    for line in content.splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            vars_.add(line.split("=")[0].strip())
    return vars_


def _extract_requirements(files: dict) -> set[str] | None:
    """Return set of package names from requirements.txt, or None if absent."""
    content = files.get("requirements.txt")
    if content is None:
        return None
    pkgs = set()
    for line in content.splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            # Strip version specifiers: fastapi==0.115.0 → fastapi
            pkg = re.split(r"[>=<!~\[]", line)[0].strip().lower()
            if pkg:
                pkgs.add(pkg)
    return pkgs


def _extract_docker_entry(files: dict) -> str:
    """Find the uvicorn entry point string in Dockerfile.

    Handles both shell form (CMD uvicorn main:app --host 0.0.0.0) and the far
    more common exec/JSON form (CMD ["uvicorn", "main:app", "--host", ...]) —
    the previous regex only matched shell form and silently never matched any
    real DevOpsAgent-generated Dockerfile, which always uses exec form."""
    dockerfile = files.get("Dockerfile") or files.get("dockerfile") or ""
    if not dockerfile:
        return ""
    m = re.search(r'uvicorn["\s,]+([^\s"\',\]]+)', dockerfile)
    return m.group(1).strip() if m else ""


def _extract_python_top_imports(files: dict) -> dict[str, list[str]]:
    """Return {filepath: [imported_packages]} for Python files."""
    result: dict[str, list[str]] = {}
    pattern = re.compile(r'^(?:import|from)\s+([a-zA-Z_][a-zA-Z0-9_]*)', re.MULTILINE)
    for filepath, content in files.items():
        if filepath.endswith(".py"):
            result[filepath] = pattern.findall(content)
    return result


def _find_model_definitions(files: dict) -> list[tuple[str, str]]:
    """Find SQLAlchemy model class definitions (Base subclasses)."""
    defs: list[tuple[str, str]] = []
    # class Foo(Base): or class Foo(DeclarativeBase):
    pattern = re.compile(r'^class\s+(\w+)\s*\(\s*(?:Base|DeclarativeBase|db\.Model)\s*\)', re.MULTILINE)
    for filepath, content in files.items():
        if not filepath.endswith(".py"):
            continue
        for m in pattern.finditer(content):
            defs.append((filepath, m.group(1)))
    return defs


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _normalise_routes(routes: list[str]) -> set[str]:
    return {r.strip().upper() for r in routes}


def _route_matches_any(route: str, candidates: set[str]) -> bool:
    """
    Fuzzy path match: ignore path parameters ("{id}" == ":id" == "{item_id}").
    Match is on (method, normalised_path_segments).
    """
    parts = route.upper().split(None, 1)
    if len(parts) != 2:
        return route.upper() in {c.upper() for c in candidates}
    method, path = parts
    norm_path = _normalise_path(path)

    for candidate in candidates:
        cparts = candidate.upper().split(None, 1)
        if len(cparts) != 2:
            continue
        cmethod, cpath = cparts
        if cmethod == method and _normalise_path(cpath) == norm_path:
            return True
    return False


def _normalise_path(path: str) -> str:
    """Replace any path parameter placeholder with '{param}'."""
    # {id}, {item_id}, :id, <id> → {param}
    path = re.sub(r"\{[^}]+\}", "{param}", path)
    path = re.sub(r":[a-zA-Z_][a-zA-Z0-9_]*", "{param}", path)
    path = re.sub(r"<[^>]+>", "{param}", path)
    return path.rstrip("/")
