from app.routes.generate import _check_output_dir, _looks_like_project_prompt


def test_rejects_bare_greetings():
    for prompt in ["Hi", "hello", "hey", "yo", "thanks", "thank you", "ok", "okay", "testing"]:
        assert _looks_like_project_prompt(prompt) is False, prompt


def test_rejects_too_short_prompts():
    assert _looks_like_project_prompt("build app") is False  # only 2 words


def test_rejects_empty_and_whitespace():
    assert _looks_like_project_prompt("") is False
    assert _looks_like_project_prompt("   ") is False


def test_accepts_real_project_descriptions():
    assert _looks_like_project_prompt("Build a URL shortener with Docker support") is True
    assert _looks_like_project_prompt("Build a recipe website for indian dishes") is True
    assert _looks_like_project_prompt("Build a full-stack inventory management system with PostgreSQL") is True


def test_check_output_dir_creates_missing_directory(tmp_path):
    target = tmp_path / "brand_new_subfolder" / "nested"
    assert not target.exists()

    error = _check_output_dir(str(target))

    assert error is None
    assert target.exists()


def test_check_output_dir_rejects_path_through_a_file(tmp_path):
    """Portable way to force a real filesystem error: you can't mkdir a
    directory underneath something that's already a plain file, on any OS."""
    blocking_file = tmp_path / "not_a_directory"
    blocking_file.write_text("i am a file, not a directory")
    bad_path = blocking_file / "subdir"

    error = _check_output_dir(str(bad_path))

    assert error is not None
    assert "Cannot create output directory" in error
