from __future__ import annotations

import json
from pathlib import Path

from failstep.parser import load_run

ROOT = Path(__file__).resolve().parents[1]
GOLDENS = ROOT / "tests" / "goldens"
EXAMPLES = ROOT / "examples" / "traces"
TRACES = ROOT / "tests" / "traces"

COUNTED_KEYS = {
    "identical_calls",
    "identical calls",
    "steps",
    "latency_ms",
    "latency ms",
    "run_duration_ms",
    "run duration ms",
    "http_status",
    "http status",
    "outputs",
    "reason",
    "received_keys",
    "received keys",
    "expected_required",
    "expected required",
    "schema_required",
    "schema required",
    "payload",
    "hits",
    "chunks",
    "copies",
    "values",
}

ALLOWED_STRINGS = {"unchanged", "changed", "null", "true", "false"}


def _fixture_for(golden: Path) -> Path | None:
    name = golden.name
    if name.startswith("compare-") or name.startswith("fix-"):
        return None
    if name.startswith("inspect-"):
        name = name.removeprefix("inspect-")
    stem = Path(name).stem
    for folder in (EXAMPLES, TRACES):
        candidate = folder / f"{stem}.json"
        if candidate.exists():
            return candidate
    return None


def _findings(payload: dict) -> list[dict]:
    found: list[dict] = []
    if payload.get("root_cause"):
        found.append(payload["root_cause"])
    found.extend(payload.get("secondary") or [])
    extra = payload.get("findings") or []
    if extra:
        found = extra
    return [item for item in found if isinstance(item, dict)]


def test_goldens_have_no_confidence() -> None:
    for path in GOLDENS.glob("*.json"):
        text = path.read_text(encoding="utf-8")
        assert "confidence" not in text
        payload = json.loads(text)
        if "root_cause" in payload and payload["root_cause"]:
            assert "confidence" not in payload["root_cause"]


def test_goldens_have_no_cost() -> None:
    for path in GOLDENS.glob("*.json"):
        payload = json.loads(path.read_text(encoding="utf-8"))
        blob = json.dumps(payload)
        assert "cost_usd" not in blob
        assert "grade" not in blob
        for finding in _findings(payload):
            rec = finding.get("recommendation") or ""
            if "$" in rec:
                fixture = _fixture_for(path)
                assert fixture is not None
                assert "$" in fixture.read_text(encoding="utf-8")


def test_every_golden_finding_is_in_the_fixture() -> None:
    json_goldens = list(GOLDENS.glob("*.json"))
    assert json_goldens
    for path in json_goldens:
        payload = json.loads(path.read_text(encoding="utf-8"))
        findings = _findings(payload)
        if not findings:
            continue
        fixture_path = _fixture_for(path)
        assert fixture_path is not None, path.name
        fixture = fixture_path.read_text(encoding="utf-8")
        run = load_run(fixture_path)
        ids = {step.id for step in run.steps}
        for finding in findings:
            for step_id in finding.get("step_ids") or []:
                assert step_id in ids
            for item in finding.get("evidence") or []:
                _assert_evidence(item, fixture, run)


def _assert_evidence(item: dict, fixture: str, run) -> None:
    key = item["key"]
    value = item["value"]
    if key in COUNTED_KEYS:
        if key in {"identical calls", "identical_calls", "steps"}:
            assert isinstance(value, int)
            assert value >= 1
        if key in {"latency_ms", "run_duration_ms"} and value is not None:
            assert isinstance(value, int)
            if key == "latency_ms":
                assert value in {step.latency_ms for step in run.steps}
            if key == "run_duration_ms":
                assert value == run.duration_ms
        if key in {"http status", "http_status"}:
            assert isinstance(value, int)
            assert str(value) in fixture
        return
    if value is None:
        return
    if isinstance(value, (int, float)):
        return
    if isinstance(value, (dict, list)):
        for token in _tokens(value):
            assert token in fixture
        return
        if isinstance(value, str):
            if value in ALLOWED_STRINGS:
                return
            if value in fixture:
                return
            for step in run.steps:
                for field in (step.output, step.input, step.error, step.name):
                    if field is None:
                        continue
                    if value == field or (isinstance(field, str) and value in field):
                        return
                    rendered = json.dumps(field, ensure_ascii=True, default=str)
                    if value in rendered:
                        return
            raise AssertionError(f"{key}={value!r} missing from fixture")


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
