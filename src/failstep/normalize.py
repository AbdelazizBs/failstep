from __future__ import annotations

from pathlib import Path
from typing import Any

from failstep.models import Run, RunStatus, Step, StepType

_STEP_KEYS = {
    "id",
    "type",
    "name",
    "input",
    "output",
    "error",
    "latency_ms",
    "tokens_in",
    "tokens_out",
    "schema",
    "metadata",
    "index",
}

_RUN_KEYS = {
    "run_id",
    "id",
    "name",
    "status",
    "duration_ms",
    "error",
    "tokens_in",
    "tokens_out",
    "steps",
    "schema_version",
    "metadata",
}


def normalize(payload: dict[str, Any], source: Path) -> Run:
    raw_steps = payload.get("steps") or []
    steps = [_step(raw, index) for index, raw in enumerate(raw_steps, start=1)]

    run_id = payload.get("run_id") or payload.get("id")
    if not isinstance(run_id, str) or not run_id:
        run_id = source.stem

    status = _status(payload.get("status"))
    extra = {k: v for k, v in payload.items() if k not in _RUN_KEYS}
    metadata = _as_dict(payload.get("metadata"))
    metadata.update(extra)

    return Run(
        id=run_id,
        name=payload.get("name") if isinstance(payload.get("name"), str) else None,
        status=status,
        duration_ms=_int(payload.get("duration_ms")),
        error=_error(payload.get("error")),
        tokens_in=_int(payload.get("tokens_in")),
        tokens_out=_int(payload.get("tokens_out")),
        steps=steps,
        metadata=metadata,
    )


def _step(raw: dict[str, Any], index: int) -> Step:
    step_id = raw.get("id")
    if not isinstance(step_id, str) or not step_id:
        step_id = f"step_{index}"

    extra = {k: v for k, v in raw.items() if k not in _STEP_KEYS}
    metadata = _as_dict(raw.get("metadata"))
    metadata.update(extra)

    raw_type = raw.get("type")
    step_type = _type(raw_type)
    known_types = {item.value for item in StepType}
    if isinstance(raw_type, str) and raw_type.lower() not in known_types:
        metadata.setdefault("raw_type", raw_type)

    name = raw.get("name")
    if not isinstance(name, str):
        name = ""

    schema = raw.get("schema")
    if schema is not None and not isinstance(schema, dict):
        metadata.setdefault("raw_schema", schema)
        schema = None

    return Step.model_validate(
        {
            "index": index,
            "id": step_id,
            "type": step_type,
            "name": name,
            "input": raw.get("input"),
            "output": raw.get("output"),
            "error": _error(raw.get("error")),
            "latency_ms": _int(raw.get("latency_ms")),
            "tokens_in": _int(raw.get("tokens_in")),
            "tokens_out": _int(raw.get("tokens_out")),
            "schema": schema,
            "metadata": metadata,
        }
    )


def _type(value: Any) -> StepType:
    if isinstance(value, str):
        lowered = value.lower()
        try:
            return StepType(lowered)
        except ValueError:
            if lowered in {"function", "tool_call"}:
                return StepType.tool
    return StepType.other


def _status(value: Any) -> RunStatus:
    if isinstance(value, str):
        try:
            return RunStatus(value.lower())
        except ValueError:
            return RunStatus.unknown
    return RunStatus.unknown


def _int(value: Any) -> int | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return None


def _error(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    return str(value)


def _as_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    return {}
