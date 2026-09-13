from __future__ import annotations

from failstep.detectors import run_detectors
from failstep.evidence import DETECTOR_ORDER
from failstep.models import Finding, Report, Run, Severity


def diagnose(run: Run, file_display: str) -> Report:
    findings = run_detectors(run)
    ordered = _sort(findings)
    root = _root(ordered)
    secondary = [item for item in ordered if item is not root]
    findings_out = ([root] + secondary) if root is not None else []
    return Report(
        file=file_display,
        run=run,
        root_cause=root,
        secondary=secondary,
        findings=findings_out,
    )


def _sort(findings: list[Finding]) -> list[Finding]:
    rank = {code: index for index, code in enumerate(DETECTOR_ORDER)}
    return sorted(
        findings,
        key=lambda item: (
            0 if item.severity is Severity.error else 1,
            rank.get(item.id, 99),
            item.step_indexes[0] if item.step_indexes else 0,
        ),
    )


def _root(findings: list[Finding]) -> Finding | None:
    errors = [item for item in findings if item.severity is Severity.error]
    pool = errors or findings
    return pool[0] if pool else None
