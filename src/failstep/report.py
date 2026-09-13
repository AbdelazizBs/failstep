from __future__ import annotations

import json
from typing import Any

from failstep.compare import CompareResult, FieldDelta
from failstep.errors import ParseError
from failstep.evidence import format_step_range
from failstep.models import Finding, Report, Run, Step

LABEL_W = 12
STEP_W = 4
TYPE_W = 9
NAME_W = 16
LATENCY_W = 7
ERROR_W = 40
EVIDENCE_WRAP = 88


def format_inspect_terminal(run: Run, file_display: str, version: str) -> str:
    lines = _run_header(run, file_display, version, include_tokens=True)
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


def format_diagnose_terminal(report: Report, version: str) -> str:
    run = report.run
    lines = _run_header(run, report.file, version, include_tokens=False)
    lines.append("")
    root = report.root_cause
    lines.append("root cause")
    if root is None:
        lines.append("  none")
        lines.append("")
        lines.append("evidence")
        lines.append("  none")
        lines.append("")
        lines.append("recommendation")
        lines.append("  none")
        lines.append("")
        lines.append("secondary")
        lines.append("  none")
        return "\n".join(lines) + "\n"

    lines.append(f"  {root.id}  {root.title}")
    step_line = f"  steps  {format_step_range(root)}"
    tool = _evidence_value(root, "tool")
    if tool:
        step_line += f"  {tool}"
    lines.append(step_line)
    lines.append("")
    lines.append("evidence")
    if root.evidence:
        width = max(len(_evidence_label(item.key)) for item in root.evidence)
        for item in root.evidence:
            label = _evidence_label(item.key)
            value = _render_value(item.value)
            lines.append(f"  {label:<{width}}  {value}")
    else:
        lines.append("  none")
    lines.append("")
    lines.append("recommendation")
    rec = root.recommendation or "Insufficient evidence."
    for wrapped in _wrap(rec, EVIDENCE_WRAP - 2):
        lines.append(f"  {wrapped}")
    lines.append("")
    lines.append("secondary")
    if report.secondary:
        for item in report.secondary:
            extra = format_step_range(item)
            name = _evidence_value(item, "tool")
            suffix = f"steps {extra}"
            if name:
                suffix += f", {name}"
            lines.append(f"  {item.id}  {item.title}  ({suffix})")
    else:
        lines.append("  none")
    return "\n".join(lines) + "\n"


def format_diagnose_json(report: Report, version: str) -> str:
    root = report.root_cause
    payload = {
        "schema_version": 1,
        "tool": "failstep",
        "tool_version": version,
        "file": report.file,
        "run": _run_summary(report.run),
        "root_cause": _finding_json(root) if root else None,
        "secondary": [_finding_json(item) for item in report.secondary],
        "findings": [_finding_json(item) for item in report.findings],
    }
    return json.dumps(payload, indent=2, ensure_ascii=True) + "\n"


def format_diagnose_markdown(report: Report, version: str) -> str:
    run = report.run
    bits = [f"`{report.file}`", f"run `{run.id}`", run.status.value]
    if run.duration_ms is not None:
        bits.append(f"{run.duration_ms} ms")
    bits.append(f"{len(run.steps)} steps")
    lines = [f"## failstep {version}", " · ".join(bits), ""]
    root = report.root_cause
    lines.append("### Root cause")
    if root is None:
        lines.append("_none_")
        lines.append("")
        lines.append("### Secondary")
        lines.append("_none_")
        return "\n".join(lines) + "\n"
    tool = _evidence_value(root, "tool")
    where = format_step_range(root)
    title = f"**{root.id} {root.title}**"
    if tool:
        title += f" on `{tool}`"
    if where:
        title += f" (steps {where})"
    lines.append(title)
    lines.append("")
    if root.evidence:
        lines.append("| evidence | |")
        lines.append("|---|---|")
        for item in root.evidence:
            value = _render_value(item.value)
            if item.key == "args" or isinstance(item.value, (dict, list)):
                value = f"`{_render_value(item.value)}`"
            lines.append(f"| {_evidence_label(item.key)} | {value} |")
        lines.append("")
    lines.append(f"**Fix:** {root.recommendation}")
    lines.append("")
    lines.append("### Secondary")
    if report.secondary:
        for item in report.secondary:
            extra = format_step_range(item)
            name = _evidence_value(item, "tool")
            bit = f"- **{item.id} {item.title}**"
            if extra:
                bit += f" (steps {extra}"
                if name:
                    bit += f", {name}"
                bit += ")"
            lines.append(bit)
    else:
        lines.append("_none_")
    return "\n".join(lines) + "\n"




def format_fix_terminal(report: Report, version: str) -> str:
    lines = [
        f"failstep {version}",
        _label("file", report.file),
        _label("run", report.run.id),
        "",
        "patch",
    ]
    root = report.root_cause
    if root is None:
        lines.append("  none")
        lines.append("")
        lines.append("also")
        lines.append("  none")
        return "\n".join(lines) + "\n"
    lines.extend(_patch_lines(root))
    lines.append("")
    lines.append("also")
    if report.secondary:
        for item in report.secondary:
            lines.extend(_patch_lines(item))
    else:
        lines.append("  none")
    return "\n".join(lines) + "\n"


def format_fix_json(report: Report, version: str) -> str:
    root = report.root_cause
    payload = {
        "schema_version": 1,
        "tool": "failstep",
        "tool_version": version,
        "file": report.file,
        "run": _run_summary(report.run),
        "patch": _patch_json(root) if root else None,
        "also": [_patch_json(item) for item in report.secondary],
    }
    return json.dumps(payload, indent=2, ensure_ascii=True) + "\n"


def format_fix_markdown(report: Report, version: str) -> str:
    lines = [
        f"## failstep {version}",
        f"`{report.file}` · run `{report.run.id}`",
        "",
        "### Patch",
    ]
    root = report.root_cause
    if root is None:
        lines.append("_none_")
        lines.append("")
        lines.append("### Also")
        lines.append("_none_")
        return "\n".join(lines) + "\n"
    lines.extend(_patch_md(root))
    lines.append("")
    lines.append("### Also")
    if report.secondary:
        for item in report.secondary:
            lines.extend(_patch_md(item, bullet=True))
    else:
        lines.append("_none_")
    return "\n".join(lines) + "\n"


def format_compare_terminal(result: CompareResult, version: str) -> str:
    lines = [
        f"failstep {version}",
        _label("old", result.old_file),
        _label("new", result.new_file),
        "",
        "root cause",
        f"  old  {_root_line(result.old_root)}",
        f"  new  {_root_line(result.new_root)}",
        "",
        "findings",
    ]
    width = max(len("gone"), len("added"), len("same"))
    lines.append(f"  {'gone':<{width}}  {_id_list(result.gone)}")
    lines.append(f"  {'added':<{width}}  {_id_list(result.added)}")
    lines.append(f"  {'same':<{width}}  {_id_list(result.same)}")
    lines.append("")
    lines.append("run")
    if not result.run:
        lines.append("  none")
    else:
        field_w = max(len(_evidence_label(item.key)) for item in result.run)
        for item in result.run:
            label = _evidence_label(item.key)
            lines.append(f"  {label:<{field_w}}  {_delta_text(item)}")
    return "\n".join(lines) + "\n"


def format_compare_json(result: CompareResult, version: str) -> str:
    payload = {
        "schema_version": 1,
        "tool": "failstep",
        "tool_version": version,
        "old": _compare_side(
            result.old_file, result.old_run, result.old_root, result.old_ids
        ),
        "new": _compare_side(
            result.new_file, result.new_run, result.new_root, result.new_ids
        ),
        "diff": {
            "findings": {
                "gone": list(result.gone),
                "added": list(result.added),
                "same": list(result.same),
            },
            "root_cause": {
                "old": result.old_root.id if result.old_root else None,
                "new": result.new_root.id if result.new_root else None,
            },
            "run": [_delta_json(item) for item in result.run],
        },
    }
    return json.dumps(payload, indent=2, ensure_ascii=True) + "\n"


def format_compare_markdown(result: CompareResult, version: str) -> str:
    lines = [
        f"## failstep {version}",
        f"`{result.old_file}` -> `{result.new_file}`",
        "",
        "### Root cause",
        f"old {_root_md(result.old_root)} · new {_root_md(result.new_root)}",
        "",
        "### Findings",
        "| | |",
        "|---|---|",
        f"| gone | {_id_list(result.gone)} |",
        f"| added | {_id_list(result.added)} |",
        f"| same | {_id_list(result.same)} |",
        "",
        "### Run",
    ]
    if not result.run:
        lines.append("_none_")
    else:
        lines.append("| field | old | new | delta |")
        lines.append("|---|---:|---:|---:|")
        for item in result.run:
            delta = "" if item.delta is None else str(item.delta)
            lines.append(
                f"| {_evidence_label(item.key)} | {_render_value(item.old)} | "
                f"{_render_value(item.new)} | {delta} |"
            )
    return "\n".join(lines) + "\n"


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


def format_internal_terminal() -> str:
    return "Internal error.\n"


def format_internal_json(version: str) -> str:
    payload = {
        "schema_version": 1,
        "tool": "failstep",
        "tool_version": version,
        "error": {"code": "internal", "message": "Internal error."},
    }
    return json.dumps(payload, indent=2, ensure_ascii=True) + "\n"


def _run_header(
    run: Run, file_display: str, version: str, *, include_tokens: bool
) -> list[str]:
    lines = [
        f"failstep {version}",
        _label("file", file_display),
        _label("run", run.id),
        _label("status", run.status.value),
    ]
    if run.duration_ms is not None:
        lines.append(_label("duration", f"{run.duration_ms} ms"))
    lines.append(_label("steps", str(len(run.steps))))
    if include_tokens and (run.tokens_in is not None or run.tokens_out is not None):
        tin = _num(run.tokens_in)
        tout = _num(run.tokens_out)
        lines.append(_label("tokens", f"{tin} in / {tout} out"))
    return lines


def _run_summary(run: Run) -> dict[str, Any]:
    return {
        "id": run.id,
        "status": run.status.value,
        "duration_ms": run.duration_ms,
        "step_count": len(run.steps),
        "tokens_in": run.tokens_in,
        "tokens_out": run.tokens_out,
    }


def _finding_json(finding: Finding) -> dict[str, Any]:
    return {
        "id": finding.id,
        "detector": finding.detector,
        "title": finding.title,
        "severity": finding.severity.value,
        "step_ids": finding.step_ids,
        "step_indexes": finding.step_indexes,
        "evidence": [
            {"key": item.key, "value": item.value} for item in finding.evidence
        ],
        "recommendation": finding.recommendation,
        "source": finding.source.value,
    }


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


def _evidence_label(key: str) -> str:
    return key.replace("_", " ")


def _evidence_value(finding: Finding, key: str) -> Any:
    for item in finding.evidence:
        if item.key == key:
            return item.value
    return None


def _render_value(value: Any) -> str:
    if isinstance(value, (dict, list)):
        return json.dumps(value, sort_keys=True, ensure_ascii=True, default=str)
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return "null"
    return str(value)


def _wrap(text: str, width: int) -> list[str]:
    if len(text) <= width:
        return [text]
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        trial = word if not current else f"{current} {word}"
        if len(trial) <= width:
            current = trial
            continue
        if current:
            lines.append(current)
        current = word
    if current:
        lines.append(current)
    return lines or [text]


def _compare_side(
    file_display: str,
    run: Run,
    root: Finding | None,
    ids: tuple[str, ...],
) -> dict[str, Any]:
    return {
        "file": file_display,
        "run": _run_summary(run),
        "root_cause": root.id if root else None,
        "findings": list(ids),
    }


def _root_line(finding: Finding | None) -> str:
    if finding is None:
        return "none"
    return f"{finding.id}  {finding.title}"


def _root_md(finding: Finding | None) -> str:
    if finding is None:
        return "_none_"
    return f"**{finding.id} {finding.title}**"


def _id_list(ids: tuple[str, ...]) -> str:
    return ", ".join(ids) if ids else "none"


def _delta_text(item: FieldDelta) -> str:
    body = f"{_render_value(item.old)} -> {_render_value(item.new)}"
    if item.delta is None:
        return body
    return f"{body}  ({item.delta:+d})"


def _delta_json(item: FieldDelta) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "key": item.key,
        "old": item.old,
        "new": item.new,
    }
    if item.delta is not None:
        payload["delta"] = item.delta
    return payload


def _patch_json(finding: Finding) -> dict[str, Any]:
    return {
        "id": finding.id,
        "title": finding.title,
        "step_ids": finding.step_ids,
        "step_indexes": finding.step_indexes,
        "recommendation": finding.recommendation,
    }


def _patch_lines(finding: Finding) -> list[str]:
    lines = [f"  {finding.id}  {finding.title}"]
    step_line = f"  steps  {format_step_range(finding)}"
    tool = _evidence_value(finding, "tool")
    if tool:
        step_line += f"  {tool}"
    lines.append(step_line)
    rec = finding.recommendation or "Insufficient evidence."
    for wrapped in _wrap(rec, EVIDENCE_WRAP - 2):
        lines.append(f"  {wrapped}")
    return lines


def _patch_md(finding: Finding, *, bullet: bool = False) -> list[str]:
    tool = _evidence_value(finding, "tool")
    where = format_step_range(finding)
    title = f"**{finding.id} {finding.title}**"
    if tool:
        title += f" on `{tool}`"
    if where:
        title += f" (steps {where})"
    if bullet:
        return [f"- {title}: {finding.recommendation}"]
    return [title, "", finding.recommendation]
