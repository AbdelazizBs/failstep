from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from failstep.cli import app

ROOT = Path(__file__).resolve().parents[1]


def test_version(runner: CliRunner) -> None:
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert result.stdout.strip() == "failstep 0.1.0"


def test_missing_file_exit_2(runner: CliRunner, tmp_path: Path) -> None:
    missing = tmp_path / "nope.json"
    result = runner.invoke(app, ["inspect", str(missing)])
    assert result.exit_code == 2
    assert "File not found" in result.stdout
    assert "Traceback" not in result.stdout


def test_empty_file_exit_2(runner: CliRunner, tmp_path: Path) -> None:
    empty = tmp_path / "empty.json"
    empty.write_text("", encoding="utf-8")
    result = runner.invoke(app, ["inspect", str(empty)])
    assert result.exit_code == 2
    assert "File is empty" in result.stdout


def test_invalid_json_exit_2(runner: CliRunner, tmp_path: Path) -> None:
    bad = tmp_path / "bad.json"
    bad.write_text("{not json", encoding="utf-8")
    result = runner.invoke(app, ["inspect", str(bad)])
    assert result.exit_code == 2
    assert "Invalid JSON" in result.stdout


def test_unknown_shape_exit_2(runner: CliRunner, tmp_path: Path) -> None:
    path = tmp_path / "nope.json"
    path.write_text('{"foo": 1}', encoding="utf-8")
    result = runner.invoke(app, ["inspect", str(path)])
    assert result.exit_code == 2
    assert "Not a failstep trace" in result.stdout
    assert "docs/TRACE_FORMAT.md" in result.stdout


def test_json_format_on_bad_file(runner: CliRunner, tmp_path: Path) -> None:
    path = tmp_path / "nope.txt"
    path.write_text("hello", encoding="utf-8")
    result = runner.invoke(app, ["inspect", str(path), "--format", "json"])
    assert result.exit_code == 2
    payload = json.loads(result.stdout)
    assert payload["schema_version"] == 1
    assert payload["tool"] == "failstep"
    assert payload["error"]["code"] == "invalid_input"
    assert "confidence" not in payload
    assert "Traceback" not in result.stdout


def test_diagnose_finding_exit_1(runner: CliRunner, monkeypatch) -> None:
    monkeypatch.chdir(ROOT)
    result = runner.invoke(app, ["diagnose", "examples/traces/retry-loop.json"])
    assert result.exit_code == 1
    assert "FS004" in result.stdout
    assert "Traceback" not in result.stdout


def test_diagnose_garbage_exit_2(runner: CliRunner, tmp_path: Path) -> None:
    path = tmp_path / "nope.json"
    path.write_text("[]", encoding="utf-8")
    result = runner.invoke(app, ["diagnose", str(path)])
    assert result.exit_code == 2
    assert "Not a failstep trace" in result.stdout


def test_success_inspect_exit_0(runner: CliRunner, monkeypatch) -> None:
    monkeypatch.chdir(ROOT)
    result = runner.invoke(app, ["inspect", "examples/traces/success.json"])
    assert result.exit_code == 0


def test_internal_error_exit_3(runner: CliRunner, monkeypatch) -> None:
    monkeypatch.chdir(ROOT)

    def boom(*_args, **_kwargs):
        raise RuntimeError("forced")

    monkeypatch.setattr("failstep.cli.diagnose_run", boom)
    result = runner.invoke(app, ["diagnose", "examples/traces/success.json"])
    assert result.exit_code == 3
    assert "Internal error." in result.stdout
    assert "Traceback" not in result.stdout
