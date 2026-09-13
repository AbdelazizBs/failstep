from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from failstep.adapters import adapt
from failstep.errors import ParseError
from failstep.models import Run
from failstep.normalize import normalize

UNKNOWN_SHAPE = (
    "Not a failstep trace. Expected a JSON object with a steps array. "
    "See docs/TRACE_FORMAT.md."
)


def load_run(path: Path) -> Run:
    return normalize(parse_file(path), path)


def parse_file(path: Path) -> dict[str, Any]:
    shown = _display(path)
    if not path.exists():
        raise ParseError(f"File not found: {shown}", shown)
    if path.is_dir():
        raise ParseError(f"Not a file: {shown}", shown)

    text = path.read_text(encoding="utf-8-sig")
    if not text.strip():
        raise ParseError(f"File is empty: {shown}", shown)

    if path.suffix.lower() == ".jsonl":
        return _parse_jsonl(text, path)

    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        if _looks_like_jsonl(text):
            return _parse_jsonl(text, path)
        raise ParseError(f"Invalid JSON at {shown}: {exc.msg}", shown) from exc

    return _coerce_payload(data, path)


def _display(path: Path) -> str:
    return path.as_posix()


def _looks_like_jsonl(text: str) -> bool:
    lines = [ln for ln in text.splitlines() if ln.strip()]
    if len(lines) < 2:
        return False
    try:
        json.loads(lines[0])
        json.loads(lines[1])
    except json.JSONDecodeError:
        return False
    return True


def _parse_jsonl(text: str, path: Path) -> dict[str, Any]:
    shown = _display(path)
    objects: list[Any] = []
    for i, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if not line:
            continue
        try:
            objects.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise ParseError(
                f"Invalid JSON at {shown}: {exc.msg} (line {i})",
                shown,
            ) from exc

    if not objects:
        raise ParseError(f"File is empty: {shown}", shown)

    first = objects[0]
    if isinstance(first, dict) and isinstance(first.get("steps"), list):
        if len(objects) > 1:
            raise ParseError(UNKNOWN_SHAPE, shown)
        return _coerce_payload(first, path)

    header: dict[str, Any] = {}
    steps: list[Any]
    if isinstance(first, dict) and _is_run_header(first):
        header = first
        steps = objects[1:]
    else:
        steps = objects

    if not steps or not all(isinstance(item, dict) for item in steps):
        raise ParseError(UNKNOWN_SHAPE, shown)

    payload = dict(header)
    payload["steps"] = steps
    return payload


def _is_run_header(obj: dict[str, Any]) -> bool:
    if "type" in obj or "name" in obj:
        return False
    return any(key in obj for key in ("run_id", "status", "duration_ms", "tokens_in"))


def _coerce_payload(data: Any, path: Path) -> dict[str, Any]:
    shown = _display(path)
    native = _as_native(data)
    if native is not None:
        return native
    adapted = adapt(data)
    if adapted is not None and _as_native(adapted) is not None:
        return adapted
    raise ParseError(UNKNOWN_SHAPE, shown)


def _as_native(data: Any) -> dict[str, Any] | None:
    if isinstance(data, list):
        if not data or not all(isinstance(item, dict) for item in data):
            return None
        return {"steps": data}

    if not isinstance(data, dict):
        return None

    steps = data.get("steps")
    if not isinstance(steps, list):
        return None
    if not all(isinstance(item, dict) for item in steps):
        return None
    return data
