import json

from app.services.project_generator import ProjectGenerator


def test_generate_writes_files_and_metadata(tmp_path):
    gen = ProjectGenerator(str(tmp_path))
    files = {"main.py": "print(1)", "routes/a.py": "print(2)"}
    plan = {"description": "test", "project_type": "backend_only", "technologies": {}}

    path, written, skipped = gen.generate(
        "myproj", files, plan, {"passed": [], "errors": [], "warnings": []}
    )

    assert sorted(written) == ["main.py", "routes/a.py"]
    assert skipped == []
    meta = json.loads((tmp_path / "myproj" / "autodev_meta.json").read_text())
    assert meta["project_name"] == "myproj"
    assert meta["file_count"] == 2


def test_generate_skips_windows_invalid_filename_but_keeps_the_rest(tmp_path):
    """Reproduces the exact real-world bug: DatabaseAgent occasionally echoes a
    literal Alembic naming placeholder like '<some_random_string>.py', which
    Windows rejects. One bad filename must not take down the whole generation."""
    gen = ProjectGenerator(str(tmp_path))
    files = {
        "main.py": "print(1)",
        "alembic/versions/<some_random_string>.py": "bad content",
        "routes/a.py": "print(2)",
    }
    plan = {"description": "test"}

    path, written, skipped = gen.generate("recipe_website", files, plan, {})

    assert "main.py" in written
    assert "routes/a.py" in written
    assert len(skipped) <= 1  # only fails on platforms where < > are illegal (Windows)
    assert (tmp_path / "recipe_website" / "autodev_meta.json").exists()


def test_generate_skips_null_byte_filename_cross_platform(tmp_path):
    """A null byte in a path raises ValueError (not OSError) on every OS —
    this is the portable equivalent of the Windows-only test above."""
    gen = ProjectGenerator(str(tmp_path))
    files = {
        "main.py": "print(1)",
        "bad\x00name.py": "bad content",
        "routes/a.py": "print(2)",
    }
    plan = {"description": "test"}

    path, written, skipped = gen.generate("proj", files, plan, {})

    assert sorted(written) == ["main.py", "routes/a.py"]
    assert len(skipped) == 1
    assert skipped[0]["file"] == "bad\x00name.py"
    assert (tmp_path / "proj" / "autodev_meta.json").exists()


def test_generate_blocks_path_traversal(tmp_path):
    gen = ProjectGenerator(str(tmp_path))
    files = {"../../evil.py": "print('escaped')"}
    plan = {"description": "test"}

    path, written, skipped = gen.generate("safe_project", files, plan, {})

    assert written == []
    assert not (tmp_path / "evil.py").exists()


def test_generate_skips_empty_or_whitespace_only_files(tmp_path):
    gen = ProjectGenerator(str(tmp_path))
    files = {"empty.py": "", "whitespace.py": "   \n  ", "real.py": "print(1)"}
    plan = {"description": "test"}

    path, written, skipped = gen.generate("proj2", files, plan, {})

    assert written == ["real.py"]


def test_generate_reuses_existing_folder_for_same_project_name(tmp_path):
    """generate() itself is a low-level primitive: given the same name twice,
    it overwrites in place rather than erroring. Collision *avoidance* is a
    separate, opt-in concern handled by resolve_unique_name() (see below) —
    generate.py calls that first and passes the already-resolved name here."""
    gen = ProjectGenerator(str(tmp_path))
    gen.generate("proj3", {"main.py": "v1"}, {"description": "test"}, {})
    path, written, skipped = gen.generate("proj3", {"main.py": "v2"}, {"description": "test"}, {})

    assert (tmp_path / "proj3" / "main.py").read_text() == "v2"


def test_resolve_unique_name_returns_original_when_no_collision(tmp_path):
    gen = ProjectGenerator(str(tmp_path))
    assert gen.resolve_unique_name("brand_new_project") == "brand_new_project"


def test_resolve_unique_name_appends_suffix_on_collision(tmp_path):
    gen = ProjectGenerator(str(tmp_path))
    gen.generate("todo_api", {"main.py": "v1"}, {"description": "test"}, {})

    assert gen.resolve_unique_name("todo_api") == "todo_api_2"


def test_resolve_unique_name_increments_past_multiple_collisions(tmp_path):
    gen = ProjectGenerator(str(tmp_path))
    gen.generate("todo_api", {"main.py": "v1"}, {"description": "test"}, {})
    gen.generate("todo_api_2", {"main.py": "v1"}, {"description": "test"}, {})
    gen.generate("todo_api_3", {"main.py": "v1"}, {"description": "test"}, {})

    assert gen.resolve_unique_name("todo_api") == "todo_api_4"


def test_resolve_then_generate_never_overwrites_a_prior_project(tmp_path):
    """The real end-to-end fix this session: regenerating with a colliding
    name must land in a fresh folder, and the original project's files must
    remain completely untouched."""
    gen = ProjectGenerator(str(tmp_path))
    gen.generate("todo_api", {"main.py": "original content"}, {"description": "first"}, {})

    resolved = gen.resolve_unique_name("todo_api")
    gen.generate(resolved, {"main.py": "second project content"}, {"description": "second"}, {})

    assert resolved == "todo_api_2"
    assert (tmp_path / "todo_api" / "main.py").read_text() == "original content"
    assert (tmp_path / "todo_api_2" / "main.py").read_text() == "second project content"
