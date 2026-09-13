from __future__ import annotations

import re
from typing import Any

from failstep.detectors.schema import looks_like_schema_error
from failstep.evidence import finding
from failstep.models import Finding, Run, Step, StepType

_HTTP_STATUS = re.compile(r"\b(?:HTTP[ /_]?)?([45]\d\d)\b", re.IGNORECASE)
_TIMEOUT_TEXT = re.compile(r"\btime.?out\b", re.IGNORECASE)


def detect(run: Run) -> list[Finding]:
    hits: list[Step] = []
    for step in run.steps:
        if step.type is not StepType.tool:
            continue
        if looks_like_schema_error(step.error):
            continue
        if step.error and _TIMEOUT_TEXT.search(step.error):
            continue
        if _is_failure(step):
            hits.append(step)
    if not hits:
        return []
    first = hits[0]
    status = _http_status(first)
    evidence: list[tuple[str, Any]] = [
        ("tool", first.name),
        ("steps", len(hits)),
    ]
    if first.error:
        evidence.append(("step error", first.error))
    if status is not None:
        evidence.append(("http status", status))
    if _empty_payload(first):
        evidence.append(("payload", "empty error"))
    return [
        finding(
            code="FS003",
            detector="tool_error",
            title="tool failure",
            steps=hits,
            evidence=evidence,
            recommendation=(
                "Handle the tool error. "
                "Do not retry the same failed call without changing arguments."
            ),
        )
    ]


def _is_failure(step: Step) -> bool:
    if step.error and step.error.strip():
        return True
    if _http_status(step) is not None:
        return True
    return _empty_payload(step)


def _http_status(step: Step) -> int | None:
    if step.error:
        match = _HTTP_STATUS.search(step.error)
        if match:
            return int(match.group(1))
    output = step.output
    if isinstance(output, dict):
        for key in ("status", "status_code", "http_status"):
            value = output.get(key)
            if isinstance(value, int) and value >= 400:
                return value
            if isinstance(value, str) and value.isdigit() and int(value) >= 400:
                return int(value)
        error = output.get("error")
        if isinstance(error, str):
            match = _HTTP_STATUS.search(error)
            if match:
                return int(match.group(1))
    return None


def _empty_payload(step: Step) -> bool:
    if step.error is not None and step.error.strip() == "":
        return True
    output = step.output
    if isinstance(output, dict):
        if "error" in output and output.get("error") in (None, ""):
            useful = {
                k: v
                for k, v in output.items()
                if k != "error" and v not in (None, "", [])
            }
            return not useful
    return False
