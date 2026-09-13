from __future__ import annotations

from collections import defaultdict
from typing import Any

from failstep.evidence import finding
from failstep.models import Finding, Run, Severity, Step, StepType

_CHUNK_KEYS = ("chunks", "documents", "docs", "results", "items")
_ID_KEYS = ("id", "doc_id", "chunk_id", "document_id")
_SOURCE_KEYS = ("source", "uri", "url")
_TEXT_KEYS = ("text", "content", "snippet", "page_content")
_SKIP_FIELDS = {
    "id",
    "doc_id",
    "chunk_id",
    "document_id",
    "source",
    "uri",
    "url",
    "text",
    "content",
    "snippet",
    "page_content",
    "score",
    "rank",
    "index",
    "metadata",
}


def detect(run: Run) -> list[Finding]:
    return detect_empty(run) + detect_duplicates(run) + detect_conflict(run)


def detect_empty(run: Run) -> list[Finding]:
    hits: list[Step] = []
    for step in run.steps:
        if step.type is not StepType.retrieval:
            continue
        if _is_empty(step):
            hits.append(step)
    if not hits:
        return []
    first = hits[0]
    query = _query(first)
    evidence: list[tuple[str, Any]] = [
        ("tool", first.name),
        ("steps", len(hits)),
        ("hits", _hits(first)),
        ("chunks", 0),
    ]
    if query is not None:
        evidence.append(("query", query))
    return [
        finding(
            code="FS006",
            detector="empty_retrieval",
            title="empty retrieval",
            steps=hits,
            evidence=evidence,
            recommendation=(
                "Do not answer from an empty retrieval. "
                "Retry the query or tell the user nothing was found."
            ),
        )
    ]


def detect_duplicates(run: Run) -> list[Finding]:
    findings: list[Finding] = []
    for step in run.steps:
        if step.type is not StepType.retrieval:
            continue
        chunks = _chunks(step)
        if not chunks:
            continue
        groups: dict[str, list[Any]] = defaultdict(list)
        for chunk in chunks:
            groups[_identity(chunk)].append(chunk)
        dupes = {key: items for key, items in groups.items() if len(items) >= 2}
        if not dupes:
            continue
        items = max(dupes.values(), key=len)
        sample = items[0]
        evidence: list[tuple[str, Any]] = [
            ("tool", step.name),
            ("copies", len(items)),
            ("chunks", len(chunks)),
        ]
        source = _source(sample)
        if source:
            evidence.append(("source", source))
        text = _text(sample)
        if text is not None:
            evidence.append(("text", text))
        findings.append(
            finding(
                code="FS007",
                detector="duplicate_chunks",
                title="duplicate chunks",
                steps=[step],
                evidence=evidence,
                recommendation=(
                    "Deduplicate retrieval chunks by id before sending them "
                    "to the model."
                ),
                severity=Severity.warning,
            )
        )
    return findings


def detect_conflict(run: Run) -> list[Finding]:
    findings: list[Finding] = []
    for step in run.steps:
        if step.type is not StepType.retrieval:
            continue
        chunks = _chunks(step) or []
        by_field: dict[str, list[tuple[Any, Any]]] = defaultdict(list)
        for chunk in chunks:
            if not isinstance(chunk, dict):
                continue
            source = _source(chunk) or _id(chunk)
            for field, value in _scalars(chunk).items():
                by_field[field].append((source, value))
        chosen: tuple[str, list[tuple[Any, Any]]] | None = None
        for field, pairs in by_field.items():
            values = [value for _source_id, value in pairs]
            unique = _unique(values)
            if len(unique) < 2:
                continue
            chosen = (field, pairs)
            break
        if chosen is None:
            continue
        field, pairs = chosen
        values = _unique([value for _source_id, value in pairs])
        sources = [
            source
            for source, _value in pairs
            if isinstance(source, str) and source
        ]
        evidence: list[tuple[str, Any]] = [
            ("tool", step.name),
            ("field", field),
            ("values", values),
        ]
        if sources:
            evidence.append(("sources", sources))
        findings.append(
            finding(
                code="FS008",
                detector="conflict",
                title="conflicting sources",
                steps=[step],
                evidence=evidence,
                recommendation=(
                    f"Do not merge sources that disagree on {field}. "
                    "Surface both values."
                ),
            )
        )
    return findings


def _is_empty(step: Step) -> bool:
    chunks = _chunks(step)
    if chunks is not None:
        return len(chunks) == 0
    return _hits(step) == 0


def _chunks(step: Step) -> list[Any] | None:
    output = step.output
    if output is None:
        return []
    if isinstance(output, list):
        return output
    if isinstance(output, str):
        return [] if not output.strip() else None
    if not isinstance(output, dict):
        return None
    for key in _CHUNK_KEYS:
        value = output.get(key)
        if isinstance(value, list):
            return value
    return None


def _hits(step: Step) -> int | None:
    output = step.output
    if not isinstance(output, dict):
        return None
    for key in ("hits", "count"):
        value = output.get(key)
        if isinstance(value, bool) or value is None:
            continue
        if isinstance(value, int):
            return value
        if isinstance(value, str) and value.isdigit():
            return int(value)
    return None


def _query(step: Step) -> Any:
    incoming = step.input
    if isinstance(incoming, dict):
        for key in ("query", "text", "q"):
            if key in incoming:
                return incoming[key]
        return incoming
    if isinstance(incoming, str) and incoming.strip():
        return incoming
    return None


def _identity(chunk: Any) -> str:
    if isinstance(chunk, str):
        return "text:" + chunk.strip().lower()
    if not isinstance(chunk, dict):
        return repr(chunk)
    ident = _id(chunk)
    if ident:
        return "id:" + ident
    source = _source(chunk)
    text = _text(chunk)
    if source and text is not None:
        return f"src:{source}|text:{str(text).strip().lower()}"
    if text is not None:
        return "text:" + str(text).strip().lower()
    if source:
        return "src:" + source
    return repr(sorted(chunk.items()))


def _id(chunk: dict[str, Any]) -> str | None:
    for key in _ID_KEYS:
        value = chunk.get(key)
        if isinstance(value, str) and value.strip():
            return value
    return None


def _source(chunk: Any) -> str | None:
    if not isinstance(chunk, dict):
        return None
    for key in _SOURCE_KEYS:
        value = chunk.get(key)
        if isinstance(value, str) and value.strip():
            return value
    return _id(chunk)


def _text(chunk: Any) -> Any:
    if isinstance(chunk, str):
        return chunk
    if not isinstance(chunk, dict):
        return None
    for key in _TEXT_KEYS:
        if key in chunk:
            return chunk[key]
    return None


def _scalars(chunk: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    _pull_scalars(chunk, out)
    meta = chunk.get("metadata")
    if isinstance(meta, dict):
        _pull_scalars(meta, out)
    return out


def _pull_scalars(data: dict[str, Any], out: dict[str, Any]) -> None:
    for key, value in data.items():
        if key in _SKIP_FIELDS or key in out:
            continue
        if isinstance(value, bool):
            out[key] = value
        elif isinstance(value, (int, float)) and not isinstance(value, bool):
            out[key] = value
        elif isinstance(value, str) and value.strip() and len(value) <= 40:
            out[key] = value


def _unique(values: list[Any]) -> list[Any]:
    seen: list[Any] = []
    for value in values:
        if value not in seen:
            seen.append(value)
    return seen
