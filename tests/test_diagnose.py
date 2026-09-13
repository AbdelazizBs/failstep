from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from failstep.cli import app
from failstep.diagnose import diagnose
from failstep.parser import load_run

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples" / "traces"
GOLDENS = ROOT / "tests" / "goldens"


def _strip_eol(text: str) -> str:
    return "\n".join(line.rstrip() for line in text.splitlines()) + (
        "\n" if text.endswith("\n") else ""
    )


def test_diagnose_retry_loop_terminal(runner: CliRunner, monkeypatch) -> None:
    monkeypatch.chdir(ROOT)
    result = runner.invoke(app, ["diagnose", "examples/traces/retry-loop.json"])
    assert result.exit_code == 1
    expected = (GOLDENS / "retry-loop.terminal.txt").read_text(encoding="utf-8")
    assert _strip_eol(result.stdout) == _strip_eol(expected)
    assert "FS004" in result.stdout
    assert "search_docs" in result.stdout
    assert "Cap identical tool retries at 1" in result.stdout
    assert "confidence" not in result.stdout


def test_diagnose_retry_loop_json(runner: CliRunner, monkeypatch) -> None:
    monkeypatch.chdir(ROOT)
    result = runner.invoke(
        app, ["diagnose", "examples/traces/retry-loop.json", "--format", "json"]
    )
    assert result.exit_code == 1
    payload = json.loads(result.stdout)
    expected = json.loads((GOLDENS / "retry-loop.json").read_text(encoding="utf-8"))
    assert payload == expected
    assert payload["root_cause"]["id"] == "FS004"
    assert "confidence" not in result.stdout


def test_diagnose_retry_loop_markdown(runner: CliRunner, monkeypatch) -> None:
    monkeypatch.chdir(ROOT)
    result = runner.invoke(
        app, ["diagnose", "examples/traces/retry-loop.json", "--format", "markdown"]
    )
    assert result.exit_code == 1
    expected = (GOLDENS / "retry-loop.md").read_text(encoding="utf-8")
    assert _strip_eol(result.stdout) == _strip_eol(expected)


def test_diagnose_success_exit_0(runner: CliRunner, monkeypatch) -> None:
    monkeypatch.chdir(ROOT)
    result = runner.invoke(app, ["diagnose", "examples/traces/success.json"])
    assert result.exit_code == 0
    assert "root cause" in result.stdout
    assert "  none" in result.stdout
    assert "All good" not in result.stdout
    expected = (GOLDENS / "success.terminal.txt").read_text(encoding="utf-8")
    assert _strip_eol(result.stdout) == _strip_eol(expected)


def test_diagnose_schema_mismatch(runner: CliRunner, monkeypatch) -> None:
    monkeypatch.chdir(ROOT)
    result = runner.invoke(
        app, ["diagnose", "examples/traces/schema-mismatch.json", "--format", "json"]
    )
    assert result.exit_code == 1
    payload = json.loads(result.stdout)
    assert payload["root_cause"]["id"] == "FS002"


def test_fail_on_warning_timeout(runner: CliRunner, monkeypatch) -> None:
    monkeypatch.chdir(ROOT)
    result = runner.invoke(app, ["diagnose", "examples/traces/timeout.json"])
    assert result.exit_code == 1
    payload_ok = runner.invoke(
        app, ["diagnose", "examples/traces/success.json", "--fail-on", "warning"]
    )
    assert payload_ok.exit_code == 0


def test_root_cause_order() -> None:
    run = load_run(EXAMPLES / "retry-loop.json")
    report = diagnose(run, "examples/traces/retry-loop.json")
    assert report.root_cause is not None
    assert report.root_cause.id == "FS004"
    assert report.findings[0].id == "FS004"
