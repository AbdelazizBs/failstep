from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from failstep.cli import app

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples" / "traces"
GOLDENS = ROOT / "tests" / "goldens"


def _strip_eol(text: str) -> str:
    return "\n".join(line.rstrip() for line in text.splitlines()) + (
        "\n" if text.endswith("\n") else ""
    )


def test_fix_retry_loop_goldens(runner: CliRunner, monkeypatch) -> None:
    monkeypatch.chdir(ROOT)
    args = ["fix", "examples/traces/retry-loop.json"]
    term = runner.invoke(app, args)
    assert term.exit_code == 1
    expected_term = (GOLDENS / "fix-retry-loop.terminal.txt").read_text(
        encoding="utf-8"
    )
    assert _strip_eol(term.stdout) == _strip_eol(expected_term)
    assert "FS004" in term.stdout
    assert "Cap identical tool retries at 1" in term.stdout
    assert "confidence" not in term.stdout
    assert "$" not in term.stdout

    js = runner.invoke(app, [*args, "--format", "json"])
    assert js.exit_code == 1
    payload = json.loads(js.stdout)
    expected = json.loads((GOLDENS / "fix-retry-loop.json").read_text(encoding="utf-8"))
    assert payload == expected
    assert payload["patch"]["id"] == "FS004"
    assert payload["also"] == []
    assert "confidence" not in js.stdout

    md = runner.invoke(app, [*args, "--format", "markdown"])
    assert md.exit_code == 1
    expected_md = (GOLDENS / "fix-retry-loop.md").read_text(encoding="utf-8")
    assert _strip_eol(md.stdout) == _strip_eol(expected_md)


def test_fix_success_is_silent(runner: CliRunner, monkeypatch) -> None:
    monkeypatch.chdir(ROOT)
    result = runner.invoke(app, ["fix", "examples/traces/success.json"])
    assert result.exit_code == 0
    expected = (GOLDENS / "fix-success.terminal.txt").read_text(encoding="utf-8")
    assert _strip_eol(result.stdout) == _strip_eol(expected)
    assert "FS00" not in result.stdout
    assert "All good" not in result.stdout


def test_fix_does_not_write_the_trace(runner: CliRunner, tmp_path: Path) -> None:
    source = EXAMPLES / "retry-loop.json"
    copy = tmp_path / "retry-loop.json"
    copy.write_bytes(source.read_bytes())
    before = copy.read_bytes()
    names = {path.name for path in tmp_path.iterdir()}
    result = runner.invoke(app, ["fix", str(copy)])
    assert result.exit_code == 1
    assert copy.read_bytes() == before
    assert {path.name for path in tmp_path.iterdir()} == names
    assert "patch" in result.stdout
    assert "Cap identical tool retries at 1" in result.stdout


def test_fix_never_calls_leftover(runner: CliRunner, monkeypatch) -> None:
    monkeypatch.chdir(ROOT)
    monkeypatch.setenv("FAILSTEP_LLM_URL", "http://127.0.0.1:1/leftover")
    monkeypatch.setenv("FAILSTEP_LLM_TOKEN", "sk-test-example")
    result = runner.invoke(app, ["fix", "tests/traces/leftover-secret.json"])
    assert result.exit_code == 0
    assert "FS000" not in result.stdout
    assert "Internal error" not in result.stdout
    assert "patch" in result.stdout
    assert "none" in result.stdout


def test_fix_garbage_exit_2(runner: CliRunner, tmp_path: Path) -> None:
    path = tmp_path / "nope.json"
    path.write_text('{"hello": "world"}\n', encoding="utf-8")
    result = runner.invoke(app, ["fix", str(path)])
    assert result.exit_code == 2
    assert "Not a failstep trace" in result.stdout
    assert "Traceback" not in result.stdout


def test_fix_multi_failure_keeps_patches_apart(
    runner: CliRunner, monkeypatch
) -> None:
    monkeypatch.chdir(ROOT)
    result = runner.invoke(app, ["fix", "tests/traces/multi-failure.json"])
    assert result.exit_code == 1
    assert "FS001" in result.stdout
    assert "Return complete JSON from the tool" in result.stdout
    assert "FS002" in result.stdout
    assert "FS007" in result.stdout
    assert "confidence" not in result.stdout
    assert "hallucin" not in result.stdout.lower()
