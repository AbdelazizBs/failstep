from __future__ import annotations

from pathlib import Path

from failstep.detectors.malformed import detect as detect_malformed
from failstep.detectors.retry import detect as detect_retry
from failstep.detectors.schema import detect as detect_schema
from failstep.detectors.timeout import detect as detect_timeout
from failstep.detectors.tool_error import detect as detect_tool_error
from failstep.diagnose import diagnose
from failstep.parser import load_run

ROOT = Path(__file__).resolve().parents[2]
TRACES = ROOT / "tests" / "traces"
EXAMPLES = ROOT / "examples" / "traces"


def _run(name: str):
    path = TRACES / name
    if not path.exists():
        path = EXAMPLES / name
    return load_run(path)


def _ids(findings) -> list[str]:
    return [item.id for item in findings]


def test_schema_traps_cover_shapes() -> None:
    run = _run("schema-traps.json")
    findings = detect_schema(run)
    assert len(findings) == 1
    finding = findings[0]
    assert finding.id == "FS002"
    assert finding.step_ids == ["step_2", "step_3", "step_4", "step_5", "step_6"]
    keys = {item.key: item.value for item in finding.evidence}
    assert keys["expected required"] == ["customer_id"]
    assert keys["received keys"] == ["email"]
    assert "customer_id" in (run.steps[1].schema_ or {}).get("required", [])
    assert detect_tool_error(run) == []


def test_schema_silent_does_not_invent_fields() -> None:
    run = _run("schema-silent.json")
    findings = detect_schema(run)
    assert findings == []
    report = diagnose(run, "tests/traces/schema-silent.json")
    assert report.root_cause is None
    assert "expected required" not in report.model_dump_json()


def test_retry_interrupted_and_changed_args_are_silent() -> None:
    run = _run("retry-silent.json")
    assert detect_retry(run) == []
    identical = [
        step
        for step in run.steps
        if step.name == "search_docs" and step.input == {"query": "refund policy"}
    ]
    assert len(identical) == 3


def test_retry_two_successes_do_not_meet_threshold() -> None:
    run = _run("retry-silent.json")
    pings = [step for step in run.steps if step.name == "ping"]
    assert len(pings) == 2
    assert detect_retry(run) == []


def test_retry_recovery_is_not_a_loop() -> None:
    run = _run("retry-silent.json")
    orders = [step for step in run.steps if step.name == "get_order"]
    assert orders[0].error
    assert orders[1].error is None
    assert detect_retry(run) == []


def test_tool_http_codes_and_recovered_run() -> None:
    run = _run("tool-http-recovered.json")
    assert run.status.value == "success"
    findings = detect_tool_error(run)
    assert len(findings) == 1
    assert findings[0].id == "FS003"
    assert findings[0].step_ids == ["step_2", "step_3", "step_4", "step_5"]
    keys = {item.key: item.value for item in findings[0].evidence}
    assert keys["http status"] == 400
    assert detect_schema(run) == []
    assert detect_timeout(run) == []


def test_tool_empty_error_payload() -> None:
    findings = detect_tool_error(_run("tool-empty-error.json"))
    assert findings[0].id == "FS003"
    keys = {item.key: item.value for item in findings[0].evidence}
    assert keys["payload"] == "empty error"


def test_malformed_invalid_json() -> None:
    findings = detect_malformed(_run("malformed-invalid.json"))
    assert findings[0].id == "FS001"
    keys = {item.key: item.value for item in findings[0].evidence}
    assert keys["reason"] == "invalid json"
    assert "hits" in keys["output"]


def test_malformed_missing_output_fields() -> None:
    findings = detect_malformed(_run("malformed-output-schema.json"))
    assert findings[0].id == "FS001"
    keys = {item.key: item.value for item in findings[0].evidence}
    assert keys["reason"] == "missing required output fields"


def test_malformed_prose_and_wrong_types_are_silent() -> None:
    run = _run("malformed-silent.json")
    assert detect_malformed(run) == []
    assert detect_retry(run) == []
    assert diagnose(run, "tests/traces/malformed-silent.json").root_cause is None


def test_timeout_llm_step() -> None:
    run = _run("timeout-llm.json")
    findings = detect_timeout(run)
    assert findings[0].id == "FS005"
    assert findings[0].step_ids == ["step_1"]
    assert detect_tool_error(run) == []


def test_timeout_then_recovery_still_reports_timeout() -> None:
    run = _run("timeout-recovered.json")
    assert run.status.value == "success"
    findings = detect_timeout(run)
    assert findings[0].step_ids == ["step_2"]
    assert detect_tool_error(run) == []


def test_timeout_missing_duration_is_not_invented() -> None:
    run = _run("timeout-missing-duration.json")
    assert run.duration_ms is None
    assert run.steps[0].latency_ms is None
    findings = detect_timeout(run)
    assert len(findings) == 1
    keys = {item.key: item.value for item in findings[0].evidence}
    assert keys["latency_ms"] is None
    assert "run_duration_ms" not in keys


def test_timeout_multiple_reports_slowest_only() -> None:
    findings = detect_timeout(_run("timeout-multiple.json"))
    assert len(findings) == 1
    assert findings[0].step_ids == ["step_2"]
    keys = {item.key: item.value for item in findings[0].evidence}
    assert keys["latency_ms"] == 19000


def test_timeout_dominate_is_warning() -> None:
    findings = detect_timeout(_run("timeout-dominate.json"))
    assert findings[0].id == "FS005"
    assert findings[0].severity.value == "warning"
    keys = {item.key: item.value for item in findings[0].evidence}
    assert keys["reason"] == "step dominates duration"
    assert keys["latency_ms"] == 8000


def test_retrieval_empty_and_duplicates_are_not_hallucinations() -> None:
    run = _run("retrieval-silent.json")
    report = diagnose(run, "tests/traces/retrieval-silent.json")
    assert report.root_cause is not None
    assert report.root_cause.id == "FS006"
    assert _ids(report.findings) == ["FS006", "FS007"]
    assert report.findings[0].step_ids == ["step_1"]
    assert report.findings[1].step_ids == ["step_2"]
    dumped = report.model_dump_json()
    assert "hallucin" not in dumped.lower()
    assert "confidence" not in dumped


def test_retrieval_then_diagnosable_tool_failure() -> None:
    run = _run("retrieval-then-fail.json")
    report = diagnose(run, "tests/traces/retrieval-then-fail.json")
    assert report.root_cause is not None
    assert report.root_cause.id == "FS003"
    assert _ids(report.findings) == ["FS003"]


def test_healthy_busy_is_silent() -> None:
    run = _run("healthy-busy.json")
    assert detect_malformed(run) == []
    assert detect_schema(run) == []
    assert detect_tool_error(run) == []
    assert detect_retry(run) == []
    assert detect_timeout(run) == []
    assert diagnose(run, "tests/traces/healthy-busy.json").root_cause is None


def test_success_example_stays_clean() -> None:
    run = _run("success.json")
    assert diagnose(run, "examples/traces/success.json").findings == []


def test_multi_failure_keeps_evidence_apart() -> None:
    run = _run("multi-failure.json")
    report = diagnose(run, "tests/traces/multi-failure.json")
    assert report.root_cause is not None
    assert report.root_cause.id == "FS001"
    assert _ids(report.findings) == [
        "FS001",
        "FS002",
        "FS003",
        "FS004",
        "FS005",
        "FS007",
    ]
    by_id = {item.id: item for item in report.findings}
    assert by_id["FS001"].step_ids == ["step_16"]
    assert by_id["FS002"].step_ids == ["step_3", "step_4", "step_6"]
    assert by_id["FS003"].step_ids == ["step_18"]
    assert by_id["FS004"].step_ids == ["step_13", "step_14", "step_15"]
    assert by_id["FS005"].step_ids == ["step_8"]
    assert by_id["FS007"].step_ids == ["step_10"]
    duplicate = {item.key: item.value for item in by_id["FS007"].evidence}
    assert duplicate["copies"] == 2
    assert duplicate["source"] == "help://refund"
    retry = {item.key: item.value for item in by_id["FS004"].evidence}
    assert retry["identical calls"] == 3
    assert retry["args"] == {"query": "refund policy"}
    timeout = {item.key: item.value for item in by_id["FS005"].evidence}
    assert timeout["latency_ms"] == 16000
    assert timeout["run_duration_ms"] == 18500
    schema = {item.key: item.value for item in by_id["FS002"].evidence}
    assert schema["expected required"] == ["customer_id"]
    dumped = report.model_dump_json()
    assert "confidence" not in dumped
    assert "$" not in by_id["FS001"].recommendation
