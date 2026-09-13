from __future__ import annotations

from pathlib import Path

from failstep.detectors.malformed import detect as detect_malformed
from failstep.detectors.retry import detect as detect_retry
from failstep.detectors.schema import detect as detect_schema
from failstep.detectors.timeout import detect as detect_timeout
from failstep.detectors.tool_error import detect as detect_tool_error
from failstep.parser import load_run

ROOT = Path(__file__).resolve().parents[2]
EXAMPLES = ROOT / "examples" / "traces"


def _run(name: str):
    return load_run(EXAMPLES / name)


def test_malformed_fires() -> None:
    findings = detect_malformed(_run("malformed-json.json"))
    assert len(findings) == 1
    finding = findings[0]
    assert finding.id == "FS001"
    assert finding.step_ids == ["step_1"]
    keys = {item.key for item in finding.evidence}
    assert "reason" in keys
    assert "output" in keys


def test_malformed_silent_on_success() -> None:
    assert detect_malformed(_run("success.json")) == []


def test_schema_fires() -> None:
    findings = detect_schema(_run("schema-mismatch.json"))
    assert len(findings) == 1
    finding = findings[0]
    assert finding.id == "FS002"
    assert "step_2" in finding.step_ids
    keys = {item.key: item.value for item in finding.evidence}
    assert keys["expected required"] == ["customer_id"]
    assert "email" in keys["received keys"]


def test_schema_silent_on_success() -> None:
    assert detect_schema(_run("success.json")) == []


def test_tool_failure_fires() -> None:
    findings = detect_tool_error(_run("tool-failure.json"))
    assert len(findings) == 1
    finding = findings[0]
    assert finding.id == "FS003"
    assert finding.step_ids == ["step_1"]
    keys = {item.key for item in finding.evidence}
    assert "step error" in keys or "http status" in keys


def test_tool_failure_skips_schema_error() -> None:
    assert detect_tool_error(_run("schema-mismatch.json")) == []


def test_tool_failure_silent_on_success() -> None:
    assert detect_tool_error(_run("success.json")) == []


def test_retry_fires() -> None:
    findings = detect_retry(_run("retry-loop.json"))
    assert len(findings) == 1
    finding = findings[0]
    assert finding.id == "FS004"
    assert finding.step_ids == ["step_3", "step_4", "step_5"]
    keys = {item.key: item.value for item in finding.evidence}
    assert keys["identical calls"] == 3
    assert keys["tool"] == "search_docs"
    assert keys["args"] == {"query": "refund policy"}
    assert keys["outputs"] == "unchanged"


def test_retry_silent_on_success() -> None:
    assert detect_retry(_run("success.json")) == []


def test_timeout_fires() -> None:
    findings = detect_timeout(_run("timeout.json"))
    assert len(findings) == 1
    finding = findings[0]
    assert finding.id == "FS005"
    assert "step_2" in finding.step_ids
    keys = {item.key for item in finding.evidence}
    assert "latency_ms" in keys


def test_timeout_silent_on_success() -> None:
    assert detect_timeout(_run("success.json")) == []
