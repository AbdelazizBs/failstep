from __future__ import annotations

import json
from pathlib import Path

from failstep.diagnose import diagnose
from failstep.errors import ParseError
from failstep.models import StepType
from failstep.parser import load_run

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "traces"


def test_openai_messages_sniff() -> None:
    run = load_run(FIXTURES / "openai-messages.json")
    assert run.id == "openai-run"
    tools = [step for step in run.steps if step.type is StepType.tool]
    assert len(tools) == 3
    assert tools[0].name == "search_docs"
    assert tools[0].input == {"query": "refund policy"}
    assert tools[0].output == {"hits": 0, "chunks": []}
    report = diagnose(run, "tests/traces/openai-messages.json")
    assert report.root_cause is not None
    assert report.root_cause.id == "FS004"


def test_langchain_intermediate_steps_sniff() -> None:
    run = load_run(FIXTURES / "langchain-steps.json")
    assert run.id == "langchain-run"
    tools = [step for step in run.steps if step.type is StepType.tool]
    assert len(tools) == 3
    assert tools[0].name == "search_docs"
    assert tools[0].input == {"query": "refund policy"}
    report = diagnose(run, "tests/traces/langchain-steps.json")
    assert report.root_cause is not None
    assert report.root_cause.id == "FS004"


def test_unknown_shape_still_rejected(tmp_path: Path) -> None:
    path = tmp_path / "nope.json"
    path.write_text(json.dumps({"foo": 1}), encoding="utf-8")
    try:
        load_run(path)
    except ParseError as exc:
        assert "Not a failstep trace" in exc.message
    else:
        raise AssertionError("expected ParseError")
