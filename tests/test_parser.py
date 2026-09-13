from __future__ import annotations

import json
from pathlib import Path

import pytest

from failstep.errors import ParseError
from failstep.models import RunStatus, StepType
from failstep.parser import load_run

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples" / "traces"
FIXTURES = Path(__file__).resolve().parent / "traces"


def test_parse_native_retry_loop() -> None:
    run = load_run(EXAMPLES / "retry-loop.json")
    assert run.id == "checkout-agent"
    assert run.status is RunStatus.failed
    assert run.duration_ms == 14820
    assert run.tokens_in == 4200
    assert run.tokens_out == 800
    assert len(run.steps) == 8
    assert run.steps[0].index == 1
    assert run.steps[0].type is StepType.llm
    assert run.steps[1].name == "get_customer"
    assert run.steps[1].error is None
    assert run.steps[1].input == {"customer_id": "cus_1"}
    assert run.steps[2].name == "search_docs"
    assert run.steps[2].input == {"query": "refund policy"}


def test_parse_success_does_not_invent_error() -> None:
    run = load_run(EXAMPLES / "success.json")
    assert run.status is RunStatus.success
    assert run.error is None
    assert all(step.error is None for step in run.steps)
    assert run.duration_ms == 2100


def test_parse_jsonl() -> None:
    run = load_run(FIXTURES / "minimal.jsonl")
    assert run.id == "jsonl-agent"
    assert run.status is RunStatus.failed
    assert run.duration_ms == 500
    assert len(run.steps) == 2
    assert run.steps[0].name == "ping"
    assert run.steps[0].error == "timeout"
    assert run.steps[1].type is StepType.llm


def test_parse_json_array_of_steps(tmp_path: Path) -> None:
    path = tmp_path / "steps.json"
    path.write_text(
        json.dumps(
            [
                {"type": "tool", "name": "ping", "latency_ms": 3},
                {"type": "llm", "name": "answer"},
            ]
        ),
        encoding="utf-8",
    )
    run = load_run(path)
    assert run.id == "steps"
    assert run.status is RunStatus.unknown
    assert [step.name for step in run.steps] == ["ping", "answer"]
    assert run.steps[0].id == "step_1"


def test_missing_optional_fields_stay_none(tmp_path: Path) -> None:
    path = tmp_path / "sparse.json"
    path.write_text(
        json.dumps({"run_id": "sparse", "steps": [{"type": "llm", "name": "only"}]}),
        encoding="utf-8",
    )
    run = load_run(path)
    assert run.duration_ms is None
    assert run.tokens_in is None
    assert run.steps[0].latency_ms is None
    assert run.steps[0].input is None
    assert run.steps[0].error is None


def test_unknown_fields_go_to_metadata(tmp_path: Path) -> None:
    path = tmp_path / "extra.json"
    path.write_text(
        json.dumps(
            {
                "run_id": "extra",
                "status": "failed",
                "trace_id": "abc",
                "steps": [{"type": "tool", "name": "x", "parent_id": "p1"}],
            }
        ),
        encoding="utf-8",
    )
    run = load_run(path)
    assert run.metadata["trace_id"] == "abc"
    assert run.steps[0].metadata["parent_id"] == "p1"


def test_reject_empty_file(tmp_path: Path) -> None:
    path = tmp_path / "empty.json"
    path.write_text("", encoding="utf-8")
    with pytest.raises(ParseError) as caught:
        load_run(path)
    assert "File is empty" in caught.value.message


def test_reject_invalid_json(tmp_path: Path) -> None:
    path = tmp_path / "bad.json"
    path.write_text("{not json", encoding="utf-8")
    with pytest.raises(ParseError) as caught:
        load_run(path)
    assert "Invalid JSON" in caught.value.message


def test_reject_unknown_shape(tmp_path: Path) -> None:
    path = tmp_path / "openai.json"
    path.write_text(json.dumps({"messages": [{"role": "user"}]}), encoding="utf-8")
    with pytest.raises(ParseError) as caught:
        load_run(path)
    assert "Not a failstep trace" in caught.value.message


def test_reject_missing_file(tmp_path: Path) -> None:
    path = tmp_path / "nope.json"
    with pytest.raises(ParseError) as caught:
        load_run(path)
    assert "File not found" in caught.value.message


def test_reject_whitespace_only_file(tmp_path: Path) -> None:
    path = tmp_path / "blank.json"
    path.write_text("  \n\t\n", encoding="utf-8")
    with pytest.raises(ParseError) as caught:
        load_run(path)
    assert "File is empty" in caught.value.message


def test_reject_wrong_root_types(tmp_path: Path) -> None:
    cases = ['"hello"', "42", "null", '{"foo": 1}', '{"steps": null}']
    for raw in cases:
        path = tmp_path / "root.json"
        path.write_text(raw, encoding="utf-8")
        with pytest.raises(ParseError) as caught:
            load_run(path)
        assert "Not a failstep trace" in caught.value.message


def test_reject_truncated_object(tmp_path: Path) -> None:
    path = tmp_path / "cut.json"
    path.write_text('{"run_id": "cut", "steps": [', encoding="utf-8")
    with pytest.raises(ParseError) as caught:
        load_run(path)
    assert "Invalid JSON" in caught.value.message


def test_empty_steps_are_a_run_not_healthy_invention(tmp_path: Path) -> None:
    path = tmp_path / "empty-steps.json"
    path.write_text(json.dumps({"run_id": "empty", "steps": []}), encoding="utf-8")
    run = load_run(path)
    assert run.id == "empty"
    assert run.steps == []
    assert run.status is RunStatus.unknown
    assert run.duration_ms is None
    assert run.tokens_in is None


def test_missing_step_id_is_generated(tmp_path: Path) -> None:
    path = tmp_path / "noid.json"
    path.write_text(
        json.dumps({"run_id": "noid", "steps": [{"type": "llm", "name": "plan"}]}),
        encoding="utf-8",
    )
    run = load_run(path)
    assert run.steps[0].id == "step_1"


def test_duplicate_step_ids_keep_unique_indexes(tmp_path: Path) -> None:
    path = tmp_path / "dup.json"
    path.write_text(
        json.dumps(
            {
                "run_id": "dup",
                "steps": [
                    {"id": "same", "type": "llm", "name": "a"},
                    {"id": "same", "type": "llm", "name": "b"},
                ],
            }
        ),
        encoding="utf-8",
    )
    run = load_run(path)
    assert [step.id for step in run.steps] == ["same", "same"]
    assert [step.index for step in run.steps] == [1, 2]


def test_wrong_duration_type_is_not_invented(tmp_path: Path) -> None:
    path = tmp_path / "dur.json"
    path.write_text(
        json.dumps(
            {
                "run_id": "dur",
                "duration_ms": "14820",
                "tokens_in": "4200",
                "steps": [{"type": "llm", "name": "plan", "latency_ms": "210"}],
            }
        ),
        encoding="utf-8",
    )
    run = load_run(path)
    assert run.duration_ms is None
    assert run.tokens_in is None
    assert run.steps[0].latency_ms is None


def test_null_optional_fields_stay_none(tmp_path: Path) -> None:
    path = tmp_path / "nulls.json"
    path.write_text(
        json.dumps(
            {
                "run_id": "nulls",
                "duration_ms": None,
                "error": None,
                "steps": [
                    {
                        "type": "tool",
                        "name": "ping",
                        "input": None,
                        "output": None,
                        "error": None,
                        "latency_ms": None,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    run = load_run(path)
    assert run.duration_ms is None
    assert run.error is None
    assert run.steps[0].input is None
    assert run.steps[0].error is None
    assert run.steps[0].latency_ms is None


def test_large_string_still_parses(tmp_path: Path) -> None:
    blob = "x" * 50_000
    path = tmp_path / "huge.json"
    path.write_text(
        json.dumps(
            {
                "run_id": "huge",
                "steps": [{"type": "llm", "name": "plan", "output": blob}],
            }
        ),
        encoding="utf-8",
    )
    run = load_run(path)
    assert run.steps[0].output == blob
