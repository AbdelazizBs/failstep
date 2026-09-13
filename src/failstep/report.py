from __future__ import annotations

import json
from typing import Any

from failstep.errors import ParseError
from failstep.models import Run, Step

LABEL_W = 12
STEP_W = 4
TYPE_W = 9
NAME_W = 16
LATENCY_W = 7
ERROR_W = 40


def format_inspect_terminal(run: Run, file_display: str, version: str) -> str:
    lines = [
        f"failstep {version}",
        _label("file", file_display),
        _label("run", run.id),
        _label("status", run.status.value),
    ]
    if run.duration_ms is not None:
        lines.append(_label("duration", f"{run.duration_ms} ms"))
    lines.append(_label("steps", str(len(run.steps))))
    if run.tokens_in is not None or run.tokens_out is not None:
        tin = _num(run.tokens_in)
        tout = _num(run.tokens_out)
        lines.append(_label("tokens", f"{tin} in / {tout} out"))
    lines.append("")
    lines.append(
        f"{'step':>{STEP_W}}  "
        f"{'type':<{TYPE_W}}  "
        f"{'name':<{NAME_W}}  "
        f"{'latency':>{LATENCY_W}}  error"
    )
    for step in run.steps:
        lines.append(_step_row(step))
    return "\n".join(lines) + "\n"


def format_inspect_markdown(run: Run, file_display: str, version: str) -> str:
    extras: list[str] = []
    if run.duration_ms is not None:
        extras.append(f"{run.duration_ms} ms")
    extras.append(f"{len(run.steps)} steps")
    header = (
        f"## failstep {version}\n"
        f"`{file_display}` · run `{run.id}` · {run.status.value} · "
        + " · ".join(extras)
        + "\n"
    )
    lines = [
        header,
        "| step | type | name | latency | error |",
        "|---:|---|---|---:|---|",
    ]
    for step in run.steps:
        latency = "" if step.latency_ms is None else f"{step.latency_ms}ms"
        error = (step.error or "").replace("|", "\\|")
        name = (step.name or "").replace("|", "\\|")
        lines.append(
            f"| {step.index} | {step.type.value} | `{name}` | {latency} | {error} |"
        )
    return "\n".join(lines) + "\n"


def format_inspect_json(run: Run, file_display: str, version: str) -> str:
    payload = {
        "schema_version": 1,
        "tool": "failstep",
        "tool_version": version,
        "file": file_display,
        "run": _run_json(run),
    }
    return json.dumps(payload, indent=2, ensure_ascii=True) + "\n"


def format_error_terminal(error: ParseError) -> str:
    return error.message + "\n"


def format_error_json(error: ParseError, version: str) -> str:
    payload = {
        "schema_version": 1,
        "tool": "failstep",
        "tool_version": version,
        "error": {
            "code": error.code,
            "message": error.message,
            "file": error.file,
        },
    }
    return json.dumps(payload, indent=2, ensure_ascii=True) + "\n"


def format_phase1_diagnose(file_display: str, version: str, output_format: str) -> str:
    message = "No detectors shipped yet. Use inspect, or wait for Phase 2."
    if output_format == "json":
        payload = {
            "schema_version": 1,
            "tool": "failstep",
            "tool_version": version,
            "file": file_display,
            "message": message,
        }
        return json.dumps(payload, indent=2, ensure_ascii=True) + "\n"
    if output_format == "markdown":
        return f"## failstep {version}\n`{file_display}`\n\n{message}\n"
    return message + "\n"


def _run_json(run: Run) -> dict[str, Any]:
    data: dict[str, Any] = {
        "id": run.id,
        "status": run.status.value,
        "duration_ms": run.duration_ms,
        "error": run.error,
        "tokens_in": run.tokens_in,
        "tokens_out": run.tokens_out,
        "step_count": len(run.steps),
        "steps": [_step_json(step) for step in run.steps],
    }
    if run.name is not None:
        data["name"] = run.name
    if run.metadata:
        data["metadata"] = run.metadata
    return data


def _step_json(step: Step) -> dict[str, Any]:
    data: dict[str, Any] = {
        "index": step.index,
        "id": step.id,
        "type": step.type.value,
        "name": step.name,
        "input": step.input,
        "output": step.output,
        "error": step.error,
        "latency_ms": step.latency_ms,
    }
    if step.tokens_in is not None:
        data["tokens_in"] = step.tokens_in
    if step.tokens_out is not None:
        data["tokens_out"] = step.tokens_out
    if step.schema_ is not None:
        data["schema"] = step.schema_
    if step.metadata:
        data["metadata"] = step.metadata
    return data


def _step_row(step: Step) -> str:
    name = _truncate(step.name or "-", NAME_W)
    if step.latency_ms is None:
        latency = f"{'-':>{LATENCY_W}}"
    else:
        latency = f"{f'{step.latency_ms}ms':>{LATENCY_W}}"
    error = _truncate(step.error or "", ERROR_W)
    row = (
        f"{step.index:>{STEP_W}}  "
        f"{step.type.value:<{TYPE_W}}  "
        f"{name:<{NAME_W}}  "
        f"{latency}  {error}"
    )
    return row.rstrip()


def _label(key: str, value: str) -> str:
    return f"{key:<{LABEL_W}} {value}"


def _num(value: int | None) -> str:
    return "-" if value is None else str(value)


def _truncate(text: str, width: int) -> str:
    if len(text) <= width:
        return text
    if width <= 3:
        return text[:width]
    return text[: width - 3] + "..."
