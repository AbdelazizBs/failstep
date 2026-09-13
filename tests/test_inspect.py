from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from failstep.cli import app

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples" / "traces"
GOLDEN = ROOT / "tests" / "goldens" / "inspect-retry-loop.terminal.txt"


def _strip_eol(text: str) -> str:
    return "\n".join(line.rstrip() for line in text.splitlines()) + (
        "\n" if text.endswith("\n") else ""
    )


def test_inspect_retry_loop_matches_golden(runner: CliRunner, monkeypatch) -> None:
    monkeypatch.chdir(ROOT)
    result = runner.invoke(app, ["inspect", "examples/traces/retry-loop.json"])
    assert result.exit_code == 0
    expected = GOLDEN.read_text(encoding="utf-8")
    assert _strip_eol(result.stdout) == _strip_eol(expected)


def test_inspect_shows_run_and_steps(runner: CliRunner, monkeypatch) -> None:
    monkeypatch.chdir(ROOT)
    result = runner.invoke(app, ["inspect", str(EXAMPLES / "success.json")])
    assert result.exit_code == 0
    out = result.stdout
    assert "run          checkout-agent" in out
    assert "status       success" in out
    assert "duration     2100 ms" in out
    assert "get_order" in out
    assert "get_customer" in out
    assert "llm" in out
    assert "tool" in out


def test_inspect_json_matches_golden(runner: CliRunner, monkeypatch) -> None:
    monkeypatch.chdir(ROOT)
    result = runner.invoke(
        app, ["inspect", "examples/traces/retry-loop.json", "--format", "json"]
    )
    assert result.exit_code == 0
    assert "confidence" not in result.stdout
    expected = json.loads(
        (ROOT / "tests" / "goldens" / "inspect-retry-loop.json").read_text(
            encoding="utf-8"
        )
    )
    assert json.loads(result.stdout) == expected
