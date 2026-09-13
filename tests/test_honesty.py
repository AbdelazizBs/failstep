from __future__ import annotations

import json
from pathlib import Path

from failstep.parser import load_run

ROOT = Path(__file__).resolve().parents[1]
GOLDENS = ROOT / "tests" / "goldens"
EXAMPLES = ROOT / "examples" / "traces"

COUNTED_KEYS = {
    "identical_calls",
    "steps",
    "latency_ms",
    "run_duration_ms",
    "http_status",
    "outputs",
    "reason",
    "received_keys",
    "expected_required",
    "schema_required",
    "payload",
}


def test_goldens_have_no_confidence() -> None:
    for path in GOLDENS.glob("*.json"):
        text = path.read_text(encoding="utf-8")
        assert "confidence" not in text
        payload = json.loads(text)
        if "root_cause" in payload and payload["root_cause"]:
            assert "confidence" not in payload["root_cause"]


def test_finding_evidence_is_in_the_fixture() -> None:
    retry = json.loads((GOLDENS / "retry-loop.json").read_text(encoding="utf-8"))
    fixture = (EXAMPLES / "retry-loop.json").read_text(encoding="utf-8")
    run = load_run(EXAMPLES / "retry-loop.json")
    ids = {step.id for step in run.steps}
    finding = retry["root_cause"]
    for step_id in finding["step_ids"]:
        assert step_id in ids
    for item in finding["evidence"]:
        key = item["key"]
        value = item["value"]
        if key in COUNTED_KEYS or isinstance(value, (int, float)):
            continue
        if isinstance(value, (dict, list)):
            for token in _tokens(value):
                assert token in fixture
            continue
        if isinstance(value, str):
            assert value in fixture or value in {"unchanged", "changed"}


def _tokens(value: object) -> list[str]:
    if isinstance(value, dict):
        out: list[str] = []
        for key, inner in value.items():
            out.append(str(key))
            out.extend(_tokens(inner))
        return out
    if isinstance(value, list):
        nested: list[str] = []
        for inner in value:
            nested.extend(_tokens(inner))
        return nested
    return [str(value)]
