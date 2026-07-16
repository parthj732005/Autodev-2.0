from app.agents.devops_agent import _is_devops_file


def test_accepts_dockerfile_variants():
    assert _is_devops_file("Dockerfile")
    assert _is_devops_file("Dockerfile-frontend")
    assert _is_devops_file("backend/Dockerfile")


def test_accepts_compose_and_config_files():
    assert _is_devops_file("docker-compose.yml")
    assert _is_devops_file(".gitignore")
    assert _is_devops_file(".dockerignore")
    assert _is_devops_file(".env.example")


def test_rejects_application_source_files():
    """Confirmed live: DevOpsAgent generated a stray 'backend/main.py'
    placeholder that shadowed the real backend entry point, and duplicated
    frontend/package.json + frontend/vite.config.js alongside the real ones
    FrontendAgent already generated at the project root."""
    assert not _is_devops_file("backend/main.py")
    assert not _is_devops_file("frontend/package.json")
    assert not _is_devops_file("frontend/vite.config.js")
    assert not _is_devops_file("future_tech_showcase/database/models.py")
    assert not _is_devops_file("routes/user_routes.py")
