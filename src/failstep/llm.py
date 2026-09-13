from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any

from failstep.evidence import finding
from failstep.models import Finding, Run, Severity, Source, Step
from failstep.redact import contains_secret, redact

CLIP = 400
TIMEOUT_S = 8.0


@dataclass(frozen=True)
class LlmConfig:
    url: str
    token: str | None = None
    timeout: float = TIMEOUT_S


def load_llm_config(
    *,
    url: str | None = None,
    token: str | None = None,
) -> LlmConfig | None:
    resolved = (url or os.environ.get("FAILSTEP_LLM_URL") or "").strip()
    if not resolved:
        return None
    resolved_token = token
    if resolved_token is None:
        resolved_token = (os.environ.get("FAILSTEP_LLM_TOKEN") or "").strip() or None
    return LlmConfig(url=resolved, token=resolved_token)


def leftover_finding(run: Run, config: LlmConfig | None) -> Finding | None:
    if config is None:
        return None
    summary = summarize(run)
    payload = {
        "task": "leftover",
        "instruction": (
            "Return JSON with title, recommendation, step_indexes, "
            "and evidence copied from the summary. No confidence."
        ),
        "summary": summary,
    }
    raw = json.dumps(payload, ensure_ascii=True, default=str)
    if contains_secret(raw):
        return None
    text = _post(config, payload)
    if not text:
        return None
    data = _parse_response(text)
    if data is None:
        return None
    return _finding_from_payload(run, data)


def summarize(run: Run) -> dict[str, Any]:
    steps: list[dict[str, Any]] = []
    for step in run.steps:
        item: dict[str, Any] = {
            "index": step.index,
            "id": step.id,
            "type": step.type.value,
            "name": step.name,
        }
        if step.error:
            item["error"] = _clip(step.error)
        if step.input is not None:
            item["input"] = _clip(step.input)
        if step.output is not None:
            item["output"] = _clip(step.output)
        steps.append(item)
    return redact(
        {
            "run_id": run.id,
            "status": run.status.value,
            "duration_ms": run.duration_ms,
            "error": run.error,
            "step_count": len(run.steps),
            "steps": steps,
        }
    )


def _clip(value: Any) -> Any:
    if isinstance(value, str):
        if len(value) <= CLIP:
            return value
        return value[: CLIP - 3] + "..."
    if isinstance(value, (dict, list)):
        text = json.dumps(value, ensure_ascii=True, default=str)
        if len(text) <= CLIP:
            return value
        return text[: CLIP - 3] + "..."
    return value


def _post(config: LlmConfig, payload: dict[str, Any]) -> str | None:
    try:
        import httpx
    except ImportError:
        return None
    headers = {"Content-Type": "application/json"}
    if config.token:
        headers["X-Failstep-Token"] = config.token
    try:
        response = httpx.post(
            config.url,
            json=payload,
            headers=headers,
            timeout=config.timeout,
            follow_redirects=False,
        )
        response.raise_for_status()
    except Exception:
        return None
    return response.text


def _parse_response(text: str) -> dict[str, Any] | None:
    blob = text.strip()
    if blob.startswith("```"):
        lines = blob.splitlines()
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[1:-1]
        else:
            lines = lines[1:]
        blob = "\n".join(lines).strip()
    try:
        data = json.loads(blob)
    except json.JSONDecodeError:
        return None
    if isinstance(data, dict) and isinstance(data.get("finding"), dict):
        data = data["finding"]
    if not isinstance(data, dict):
        return None
    return data


def _finding_from_payload(run: Run, data: dict[str, Any]) -> Finding | None:
    steps = _steps_for(run, data.get("step_indexes"))
    if not steps:
        return None
    evidence = _evidence_for(run, steps, data.get("evidence"))
    title = data.get("title")
    if not isinstance(title, str) or not title.strip():
        title = "leftover"
    title = title.strip()[:40]
    rec = data.get("recommendation")
    if not isinstance(rec, str) or not rec.strip():
        rec = "Insufficient evidence."
    rec = rec.strip()
    if "confidence" in rec.lower() or "$" in rec:
        rec = "Insufficient evidence."
    return finding(
        code="FS000",
        detector="leftover",
        title=title,
        steps=steps,
        evidence=evidence,
        recommendation=rec,
        severity=Severity.warning,
        source=Source.llm,
    )


def _steps_for(run: Run, raw: Any) -> list[Step]:
    if not isinstance(raw, list) or not raw:
        return []
    wanted: list[int] = []
    for item in raw:
        if isinstance(item, bool):
            continue
        if isinstance(item, int):
            wanted.append(item)
            continue
        if isinstance(item, str) and item.isdigit():
            wanted.append(int(item))
    by_index = {step.index: step for step in run.steps}
    return [by_index[index] for index in wanted if index in by_index]


def _evidence_for(
    run: Run, steps: list[Step], raw: Any
) -> list[tuple[str, Any]]:
    copied: list[tuple[str, Any]] = []
    if isinstance(raw, list):
        for item in raw:
            if not isinstance(item, dict):
                continue
            key = item.get("key")
            value = item.get("value")
            if not isinstance(key, str) or not key or key == "confidence":
                continue
            if _in_run(run, value):
                copied.append((key, value))
    if copied:
        return copied
    step = steps[0]
    evidence: list[tuple[str, Any]] = [("step", step.name)]
    if step.output is not None:
        evidence.append(("output", step.output))
    elif step.error:
        evidence.append(("step error", step.error))
    return evidence


def _in_run(run: Run, value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, bool):
        return True
    if isinstance(value, (int, float)):
        return True
    haystacks: list[str] = []
    for step in run.steps:
        for field in (step.name, step.error, step.input, step.output, step.id):
            haystacks.append(_as_text(field))
    haystacks.append(_as_text(run.error))
    haystacks.append(run.id)
    rendered = _as_text(value)
    return any(rendered in item for item in haystacks if item)


def _as_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=True, default=str)
