from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from failstep.cli import app
from failstep.compare import compare_runs
from failstep.parser import load_run

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples" / "traces"
GOLDENS = ROOT / "tests" / "goldens"
TRACES = ROOT / "tests" / "traces"


def _strip_eol(text: str) -> str:
    return "\n".join(line.rstrip() for line in text.splitlines()) + (
        "\n" if text.endswith("\n") else ""
    )


def test_compare_retry_to_success_goldens(runner: CliRunner, monkeypatch) -> None:
    monkeypatch.chdir(ROOT)
    args = [
        "compare",
        "examples/traces/retry-loop.json",
        "examples/traces/success.json",
    ]
    term = runner.invoke(app, args)
    assert term.exit_code == 1
    expected_term = (GOLDENS / "compare-retry-loop.terminal.txt").read_text(
        encoding="utf-8"
    )
    assert _strip_eol(term.stdout) == _strip_eol(expected_term)
    assert "FS004" in term.stdout
    assert "confidence" not in term.stdout
    assert "$" not in term.stdout

    js = runner.invoke(app, [*args, "--format", "json"])
    assert js.exit_code == 1
    payload = json.loads(js.stdout)
    expected = json.loads(
        (GOLDENS / "compare-retry-loop.json").read_text(encoding="utf-8")
    )
    assert payload == expected
    assert payload["diff"]["findings"]["gone"] == ["FS004"]
    assert payload["diff"]["findings"]["added"] == []
    assert payload["diff"]["root_cause"]["old"] == "FS004"
    assert payload["diff"]["root_cause"]["new"] is None
    assert "confidence" not in js.stdout

    md = runner.invoke(app, [*args, "--format", "markdown"])
    assert md.exit_code == 1
    expected_md = (GOLDENS / "compare-retry-loop.md").read_text(encoding="utf-8")
    assert _strip_eol(md.stdout) == _strip_eol(expected_md)


def test_compare_identical_success_is_silent(runner: CliRunner, monkeypatch) -> None:
    monkeypatch.chdir(ROOT)
    result = runner.invoke(
        app,
        [
            "compare",
            "examples/traces/success.json",
            "examples/traces/success.json",
        ],
    )
    assert result.exit_code == 0
    assert "gone" in result.stdout
    assert "none" in result.stdout
    assert "FS00" not in result.stdout


def test_compare_counts_run_fields() -> None:
    old = load_run(EXAMPLES / "retry-loop.json")
    new = load_run(EXAMPLES / "success.json")
    result = compare_runs(
        old,
        new,
        "examples/traces/retry-loop.json",
        "examples/traces/success.json",
    )
    assert result.gone == ("FS004",)
    assert result.added == ()
    keys = {item.key: item for item in result.run}
    assert keys["status"].old == "failed"
    assert keys["status"].new == "success"
    assert keys["status"].delta is None
    assert keys["steps"].old == 8
    assert keys["steps"].new == 4
    assert keys["steps"].delta == -4
    assert keys["duration_ms"].old == 14820
    assert keys["duration_ms"].new == 2100
    assert keys["duration_ms"].delta == 2100 - 14820
    assert keys["tokens_in"].old == 4200
    assert keys["tokens_in"].new == 800
    assert keys["tokens_out"].old == 800
    assert keys["tokens_out"].new == 120


def test_compare_missing_duration_is_not_invented() -> None:
    old = load_run(TRACES / "timeout-missing-duration.json")
    new = load_run(EXAMPLES / "success.json")
    result = compare_runs(
        old,
        new,
        "tests/traces/timeout-missing-duration.json",
        "examples/traces/success.json",
    )
    keys = {item.key for item in result.run}
    assert "duration_ms" not in keys
    assert "tokens_in" not in keys
    assert "status" in keys
    assert "steps" in keys


def test_compare_never_calls_leftover(runner: CliRunner, monkeypatch) -> None:
    monkeypatch.chdir(ROOT)
    monkeypatch.setenv("FAILSTEP_LLM_URL", "http://127.0.0.1:1/leftover")
    monkeypatch.setenv("FAILSTEP_LLM_TOKEN", "sk-test-example")
    result = runner.invoke(
        app,
        [
            "compare",
            "tests/traces/leftover-secret.json",
            "tests/traces/leftover-secret.json",
        ],
    )
    assert result.exit_code == 0
    assert "FS000" not in result.stdout
    assert "Internal error" not in result.stdout


def test_compare_garbage_exit_2(runner: CliRunner, tmp_path: Path) -> None:
    path = tmp_path / "nope.json"
    path.write_text('{"hello": "world"}\n', encoding="utf-8")
    other = tmp_path / "ok.json"
    other.write_text(
        (EXAMPLES / "success.json").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    result = runner.invoke(app, ["compare", str(path), str(other)])
    assert result.exit_code == 2
    assert "Not a failstep trace" in result.stdout
    assert "Traceback" not in result.stdout
