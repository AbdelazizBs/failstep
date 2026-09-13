from __future__ import annotations

import json
from pathlib import Path

from failstep.diagnose import diagnose
from failstep.errors import ParseError
from failstep.models import StepType
from failstep.parser import load_run

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples" / "traces"
FIXTURES = ROOT / "tests" / "traces"


def test_otel_retry_loop_maps_and_skips_wrapper_timeout() -> None:
    run = load_run(EXAMPLES / "otel-retry-loop.json")
    assert run.id == "checkout-agent"
    assert run.duration_ms == 14820
    assert len(run.steps) == 5
    wrapper = run.steps[0]
    assert wrapper.type is StepType.other
    assert wrapper.name == "checkout-agent"
    assert wrapper.latency_ms is None
    assert wrapper.error == "failed"
    tools = [step for step in run.steps if step.type is StepType.tool]
    assert len(tools) == 3
    assert tools[0].name == "search_docs"
    assert tools[0].input == {"query": "refund policy"}
    report = diagnose(run, "examples/traces/otel-retry-loop.json")
    assert report.root_cause is not None
    assert report.root_cause.id == "FS004"
    assert [item.id for item in report.findings] == ["FS004"]


def test_otel_tool_error_is_not_dropped() -> None:
    run = load_run(FIXTURES / "otel-tool-error.json")
    failed = [step for step in run.steps if step.name == "get_order"]
    assert len(failed) == 1
    assert failed[0].type is StepType.tool
    assert failed[0].error == "HTTP 500 Internal Server Error"
    report = diagnose(run, "tests/traces/otel-tool-error.json")
    assert report.root_cause is not None
    assert report.root_cause.id == "FS003"
    assert failed[0].id in report.root_cause.step_ids


def test_otel_schema_mismatch() -> None:
    run = load_run(FIXTURES / "otel-schema.json")
    assert run.steps[0].name == "get_customer"
    assert run.steps[0].input == {"email": "user@example.test"}
    report = diagnose(run, "tests/traces/otel-schema.json")
    assert report.root_cause is not None
    assert report.root_cause.id == "FS002"
    keys = {item.key: item.value for item in report.root_cause.evidence}
    assert keys["expected required"] == ["customer_id"]
    assert keys["received keys"] == ["email"]


def test_otel_python_export_retry() -> None:
    run = load_run(FIXTURES / "otel-python-export.json")
    tools = [step for step in run.steps if step.type is StepType.tool]
    assert len(tools) == 3
    assert tools[0].input == {"query": "refund policy"}
    report = diagnose(run, "tests/traces/otel-python-export.json")
    assert report.root_cause is not None
    assert report.root_cause.id == "FS004"


def test_otel_success_silent() -> None:
    run = load_run(FIXTURES / "otel-success.json")
    types = [step.type for step in run.steps]
    assert StepType.other in types
    assert StepType.llm in types
    assert StepType.tool in types
    assert StepType.retrieval in types
    retrieval = next(step for step in run.steps if step.type is StepType.retrieval)
    assert retrieval.input == {"query": "refund policy"}
    report = diagnose(run, "tests/traces/otel-success.json")
    assert report.root_cause is None
    assert report.findings == []


def test_otel_http_only_is_unknown_shape() -> None:
    try:
        load_run(FIXTURES / "otel-http-only.json")
    except ParseError as exc:
        assert "Not a failstep trace" in exc.message
    else:
        raise AssertionError("expected ParseError")


def test_native_step_array_is_not_otel(tmp_path: Path) -> None:
    path = tmp_path / "native-array.json"
    path.write_text(
        json.dumps(
            [
                {
                    "type": "tool",
                    "name": "search_docs",
                    "input": {"query": "refund policy"},
                    "output": {"hits": 0},
                }
            ]
        ),
        encoding="utf-8",
    )
    run = load_run(path)
    assert len(run.steps) == 1
    assert run.steps[0].type is StepType.tool
    assert run.steps[0].name == "search_docs"
