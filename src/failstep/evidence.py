from __future__ import annotations

import json
from typing import Any

from failstep.models import EvidenceItem, Finding, Severity, Source, Step

DETECTOR_ORDER = ("FS001", "FS002", "FS003", "FS004", "FS005")


def canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, default=str, ensure_ascii=True)


def indexes_for(steps: list[Step]) -> list[int]:
    idxs = [step.index for step in steps]
    if len(idxs) >= 2 and idxs == list(range(idxs[0], idxs[-1] + 1)):
        return [idxs[0], idxs[-1]]
    return idxs


def format_step_range(finding: Finding) -> str:
    idxs = finding.step_indexes
    count = len(finding.step_ids)
    if not idxs:
        return ""
    if count == 1:
        return str(idxs[0])
    if len(idxs) == 2 and idxs[1] - idxs[0] + 1 == count:
        return f"{idxs[0]}-{idxs[1]}"
    return ", ".join(str(i) for i in idxs)


def finding(
    *,
    code: str,
    detector: str,
    title: str,
    steps: list[Step],
    evidence: list[tuple[str, Any]],
    recommendation: str,
    severity: Severity = Severity.error,
    source: Source = Source.deterministic,
    category: str | None = None,
) -> Finding:
    return Finding(
        id=code,
        detector=detector,
        title=title,
        severity=severity,
        step_ids=[step.id for step in steps],
        step_indexes=indexes_for(steps),
        evidence=[EvidenceItem(key=key, value=value) for key, value in evidence],
        recommendation=recommendation,
        source=source,
        category=category or detector,
    )
