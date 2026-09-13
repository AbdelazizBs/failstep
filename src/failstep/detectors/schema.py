from __future__ import annotations

import re
from typing import Any

from failstep.evidence import finding
from failstep.models import Finding, Run, Step, StepType

SCHEMA_ERROR = re.compile(
    r"(is required|required property|missing required|field required|"
    r"validation error|invalid argument|schema|unexpected keyword|"
    r"unexpected argument|extra fields? not permitted|got an unexpected)",
    re.IGNORECASE,
)

_JSON_TYPES: dict[str, type | tuple[type, ...]] = {
    "string": str,
    "number": (int, float),
    "integer": int,
    "boolean": bool,
    "object": dict,
    "array": list,
    "null": type(None),
}


def detect(run: Run) -> list[Finding]:
    hits: list[tuple[Step, list[str]]] = []
    for step in run.steps:
        if step.type is not StepType.tool:
            continue
        missing, extras, mismatch, via_error = _inspect(step)
        if missing or extras or mismatch or via_error:
            hits.append((step, missing))
    if not hits:
        return []

    first, missing = hits[0]
    received = _received_keys(first.input)
    evidence: list[tuple[str, Any]] = [
        ("tool", first.name),
        ("steps", len(hits)),
    ]
    if missing:
        evidence.append(("expected required", missing))
    if received is not None:
        evidence.append(("received keys", received))
    if first.error:
        evidence.append(("step error", first.error))
    if first.schema_ and first.schema_.get("required"):
        evidence.append(("schema required", first.schema_["required"]))

    rec = _recommendation(missing, first)
    return [
        finding(
            code="FS002",
            detector="schema",
            title="tool schema",
            steps=[step for step, _missing in hits],
            evidence=evidence,
            recommendation=rec,
        )
    ]


def looks_like_schema_error(text: str | None) -> bool:
    if not text:
        return False
    return SCHEMA_ERROR.search(text) is not None


def _inspect(step: Step) -> tuple[list[str], list[str], list[str], str | None]:
    missing: list[str] = []
    extras: list[str] = []
    mismatch: list[str] = []
    via_error: str | None = None
    schema = step.schema_
    args = step.input if isinstance(step.input, dict) else None

    if schema:
        required = [
            key for key in schema.get("required") or [] if isinstance(key, str)
        ]
        properties = schema.get("properties")
        props = properties if isinstance(properties, dict) else {}
        if args is None and required and step.input is not None:
            mismatch.append("input")
        if args is not None:
            missing = [key for key in required if key not in args]
            if props:
                extras = [key for key in args if key not in props]
            for key, spec in props.items():
                if key not in args or not isinstance(spec, dict):
                    continue
                expected = spec.get("type")
                if isinstance(expected, str) and not _type_ok(args[key], expected):
                    mismatch.append(f"{key}:{expected}")
        elif required and step.input is None:
            missing = required

    if looks_like_schema_error(step.error) and not (missing or extras or mismatch):
        via_error = step.error
    return missing, extras, mismatch, via_error


def _type_ok(value: Any, expected: str) -> bool:
    if expected == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    match = _JSON_TYPES.get(expected)
    if match is None:
        return True
    return isinstance(value, match)


def _received_keys(value: Any) -> list[str] | None:
    if isinstance(value, dict):
        return list(value.keys())
    return None


def _recommendation(missing: list[str], step: Step) -> str:
    if missing:
        return (
            "Validate tool arguments against the schema before execution. "
            f"Pass {', '.join(missing)}."
        )
    if step.error:
        return (
            "Validate tool arguments against the schema before execution. "
            "The step error names the missing field."
        )
    return "Validate tool arguments against the schema before execution."
