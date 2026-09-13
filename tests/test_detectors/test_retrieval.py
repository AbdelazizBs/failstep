from __future__ import annotations

from pathlib import Path

from failstep.detectors.retrieval import (
    detect_conflict,
    detect_duplicates,
    detect_empty,
)
from failstep.diagnose import diagnose
from failstep.models import Severity
from failstep.parser import load_run

ROOT = Path(__file__).resolve().parents[2]
TRACES = ROOT / "tests" / "traces"
EXAMPLES = ROOT / "examples" / "traces"


def _run(name: str):
    path = TRACES / name
    if not path.exists():
        path = EXAMPLES / name
    return load_run(path)


def test_empty_retrieval_fires() -> None:
    run = _run("empty-retrieval.json")
    findings = detect_empty(run)
    assert len(findings) == 1
    finding = findings[0]
    assert finding.id == "FS006"
    assert finding.step_ids == ["step_1"]
    keys = {item.key: item.value for item in finding.evidence}
    assert keys["query"] == "refund policy"
    assert keys["hits"] == 0
    assert keys["chunks"] == 0
    assert detect_duplicates(run) == []
    assert detect_conflict(run) == []


def test_duplicate_chunks_are_warning() -> None:
    run = _run("retrieval-silent.json")
    empty = detect_empty(run)
    assert empty[0].id == "FS006"
    assert empty[0].step_ids == ["step_1"]
    dupes = detect_duplicates(run)
    assert len(dupes) == 1
    finding = dupes[0]
    assert finding.id == "FS007"
    assert finding.severity is Severity.warning
    assert finding.step_ids == ["step_2"]
    keys = {item.key: item.value for item in finding.evidence}
    assert keys["copies"] == 2
    assert keys["source"] == "help://refund"
    assert keys["text"] == "30 days"
    assert detect_conflict(run) == []


def test_structured_conflict_fires() -> None:
    run = _run("retrieval-conflict.json")
    assert detect_empty(run) == []
    assert detect_duplicates(run) == []
    findings = detect_conflict(run)
    assert len(findings) == 1
    finding = findings[0]
    assert finding.id == "FS008"
    assert finding.step_ids == ["step_1"]
    keys = {item.key: item.value for item in finding.evidence}
    assert keys["field"] == "refunds"
    assert keys["values"] == [True, False]
    assert keys["sources"] == ["help://refund", "help://returns"]


def test_different_texts_are_not_conflicts() -> None:
    run = _run("retrieval-conflict-silent.json")
    assert detect_empty(run) == []
    assert detect_duplicates(run) == []
    assert detect_conflict(run) == []
    report = diagnose(run, "tests/traces/retrieval-conflict-silent.json")
    assert report.findings == []


def test_healthy_retrieval_is_silent() -> None:
    run = _run("retrieval-healthy.json")
    assert detect_empty(run) == []
    assert detect_duplicates(run) == []
    assert detect_conflict(run) == []
    report = diagnose(run, "tests/traces/retrieval-healthy.json")
    assert report.findings == []


def test_tool_empty_search_is_not_empty_retrieval() -> None:
    run = load_run(EXAMPLES / "retry-loop.json")
    assert detect_empty(run) == []
    assert detect_duplicates(run) == []
    assert detect_conflict(run) == []


def test_retrieval_then_fail_stays_tool_failure() -> None:
    run = _run("retrieval-then-fail.json")
    assert detect_empty(run) == []
    assert detect_duplicates(run) == []
    assert detect_conflict(run) == []
    report = diagnose(run, "tests/traces/retrieval-then-fail.json")
    assert report.root_cause is not None
    assert report.root_cause.id == "FS003"
    assert [item.id for item in report.findings] == ["FS003"]
