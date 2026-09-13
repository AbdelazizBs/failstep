from __future__ import annotations

import json
from typing import Any

from failstep.evidence import finding
from failstep.models import Finding, Run, Step

_JSON_START = "{["


def detect(run: Run) -> list[Finding]:
    bad: list[Step] = []
    reasons: list[str] = []
    samples: list[str] = []
    for step in run.steps:
        reason = _malformed(step)
        if reason is None:
            continue
        bad.append(step)
        reasons.append(reason)
        samples.append(_sample(step.output))
    if not bad:
        return []
    return [
        finding(
            code="FS001",
            detector="malformed",
            title="malformed output",
            steps=bad,
            evidence=[
                ("steps", len(bad)),
                ("reason", reasons[0]),
                ("output", samples[0]),
                ("tool", bad[0].name),
            ],
            recommendation=(
                "Return complete JSON from the tool. Do not truncate the payload."
            ),
        )
    ]


def _malformed(step: Step) -> str | None:
    output = step.output
    if isinstance(output, str):
        text = output.strip()
        if not text:
            return None
        if text[0] in _JSON_START:
            try:
                json.loads(text)
            except json.JSONDecodeError:
                if text.endswith("...") or not _balanced(text):
                    return "truncated json"
                return "invalid json"
        if text.endswith("...") and len(text) > 3:
            return "truncated payload"
        return None

    schema = _output_schema(step)
    if schema is None or not isinstance(output, dict):
        return None
    required = schema.get("required")
    if not isinstance(required, list):
        return None
    missing = [key for key in required if isinstance(key, str) and key not in output]
    if missing:
        return "missing required output fields"
    return None


def _output_schema(step: Step) -> dict[str, Any] | None:
    raw = step.metadata.get("output_schema")
    if isinstance(raw, dict):
        return raw
    if step.schema_ and isinstance(step.schema_.get("output"), dict):
        return step.schema_["output"]
    return None


def _balanced(text: str) -> bool:
    curly = 0
    square = 0
    in_string = False
    escape = False
    for char in text:
        if in_string:
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "{":
            curly += 1
        elif char == "}":
            curly -= 1
        elif char == "[":
            square += 1
        elif char == "]":
            square -= 1
        if curly < 0 or square < 0:
            return False
    return curly == 0 and square == 0 and not in_string


def _sample(output: Any) -> str:
    if isinstance(output, str):
        text = output.replace("\n", " ")
        return text if len(text) <= 80 else text[:77] + "..."
    return str(output)
