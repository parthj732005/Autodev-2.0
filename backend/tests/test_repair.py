from app.services import repair


class FakeProvider:
    """Returns a scripted response per call, in order."""

    def __init__(self, responses):
        self._responses = list(responses)
        self.calls = []

    async def complete(self, system, prompt):
        self.calls.append(prompt)
        return self._responses.pop(0)


async def _noop_emit(event, message, data=None):
    pass


async def test_repair_fixes_a_real_syntax_error():
    all_files = {"main.py": "def foo(:\n    pass\n"}
    validation_report = {
        "errors": [
            {"file": "main.py", "line": 1, "issue": "invalid syntax", "likely_cause": "x", "suggested_fix": "y"}
        ],
        "warnings": [],
    }
    provider = FakeProvider(["def foo():\n    pass\n"])

    report = await repair.run_targeted_repair(all_files, validation_report, provider, _noop_emit)

    assert report["attempted"] == ["main.py"]
    assert report["repaired"] == ["main.py"]
    assert report["reverted"] == []
    assert all_files["main.py"].strip() == "def foo():\n    pass"


async def test_repair_reverts_when_fix_still_broken():
    original = "def foo(:\n    pass\n"
    all_files = {"main.py": original}
    validation_report = {
        "errors": [
            {"file": "main.py", "line": 1, "issue": "invalid syntax", "likely_cause": "x", "suggested_fix": "y"}
        ],
        "warnings": [],
    }
    # The "fix" is still broken — repair must not accept it.
    provider = FakeProvider(["def foo(:\n    still broken\n"])

    report = await repair.run_targeted_repair(all_files, validation_report, provider, _noop_emit)

    assert report["attempted"] == ["main.py"]
    assert report["repaired"] == []
    assert report["reverted"] == ["main.py"]
    assert all_files["main.py"] == original  # untouched


async def test_repair_strips_markdown_fences_from_llm_response():
    all_files = {"main.py": "def foo(:\n    pass\n"}
    validation_report = {
        "errors": [{"file": "main.py", "line": 1, "issue": "invalid syntax", "likely_cause": "x", "suggested_fix": "y"}],
        "warnings": [],
    }
    provider = FakeProvider(["```python\ndef foo():\n    pass\n```"])

    report = await repair.run_targeted_repair(all_files, validation_report, provider, _noop_emit)

    assert report["repaired"] == ["main.py"]
    assert all_files["main.py"] == "def foo():\n    pass"


async def test_repair_reverts_on_provider_exception():
    original = "def foo(:\n    pass\n"
    all_files = {"main.py": original}
    validation_report = {
        "errors": [{"file": "main.py", "line": 1, "issue": "invalid syntax", "likely_cause": "x", "suggested_fix": "y"}],
        "warnings": [],
    }

    class BrokenProvider:
        async def complete(self, system, prompt):
            raise RuntimeError("provider down")

    report = await repair.run_targeted_repair(all_files, validation_report, BrokenProvider(), _noop_emit)

    assert report["reverted"] == ["main.py"]
    assert all_files["main.py"] == original


async def test_repair_only_attempts_one_call_per_file_never_a_loop():
    all_files = {"main.py": "def foo(:\n    pass\n"}
    validation_report = {
        "errors": [{"file": "main.py", "line": 1, "issue": "invalid syntax", "likely_cause": "x", "suggested_fix": "y"}],
        "warnings": [],
    }
    provider = FakeProvider(["still broken(:"])

    await repair.run_targeted_repair(all_files, validation_report, provider, _noop_emit)

    assert len(provider.calls) == 1  # exactly one attempt, never retried


async def test_repair_skips_low_stakes_warnings():
    all_files = {"empty.py": ""}
    validation_report = {
        "errors": [],
        "warnings": [{"file": "empty.py", "line": None, "issue": "Empty file", "likely_cause": "x", "suggested_fix": "y"}],
    }
    provider = FakeProvider([])

    report = await repair.run_targeted_repair(all_files, validation_report, provider, _noop_emit)

    assert report["attempted"] == []
    assert provider.calls == []


async def test_repair_includes_js_bracket_imbalance_warnings():
    """JS bracket imbalance is filed as a 'warning' by ValidatorAgent, but it's
    a real syntax problem worth repairing — not a style/formatting nit."""
    broken_js = "function App() {\n  return <div>{items.map(i => (\n"  # heavily unbalanced
    all_files = {"App.jsx": broken_js}
    validation_report = {
        "errors": [],
        "warnings": [
            {
                "file": "App.jsx",
                "line": None,
                "issue": "Likely unmatched brackets (opens=10, closes=2, diff=8)",
                "likely_cause": "Truncated output",
                "suggested_fix": "y",
            }
        ],
    }
    fixed_js = "function App() {\n  return <div>{items.map(i => (<span>{i}</span>))}</div>;\n}\n"
    provider = FakeProvider([fixed_js])

    report = await repair.run_targeted_repair(all_files, validation_report, provider, _noop_emit)

    assert report["attempted"] == ["App.jsx"]
    assert report["repaired"] == ["App.jsx"]


async def test_repair_does_nothing_when_no_candidates():
    all_files = {"main.py": "print(1)"}
    validation_report = {"errors": [], "warnings": []}
    provider = FakeProvider([])

    report = await repair.run_targeted_repair(all_files, validation_report, provider, _noop_emit)

    assert report == {"attempted": [], "repaired": [], "reverted": []}
    assert provider.calls == []


async def test_repair_disabled_flag_short_circuits(monkeypatch):
    monkeypatch.setattr(repair, "REPAIR_ENABLED", False)
    all_files = {"main.py": "def foo(:\n    pass\n"}
    validation_report = {
        "errors": [{"file": "main.py", "line": 1, "issue": "invalid syntax", "likely_cause": "x", "suggested_fix": "y"}],
        "warnings": [],
    }
    provider = FakeProvider(["def foo():\n    pass\n"])

    report = await repair.run_targeted_repair(all_files, validation_report, provider, _noop_emit)

    assert report == {"attempted": [], "repaired": [], "reverted": []}
    assert provider.calls == []
