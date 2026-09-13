from __future__ import annotations

from failstep.detectors import run_detectors
from failstep.evidence import DETECTOR_ORDER
from failstep.llm import leftover_finding, load_llm_config
from failstep.models import Finding, Report, Run, Severity


def diagnose(
    run: Run,
    file_display: str,
    *,
    no_llm: bool = False,
    llm_url: str | None = None,
    llm_token: str | None = None,
) -> Report:
    findings = run_detectors(run)
    ordered = _sort(findings)
    if not no_llm and not _has_error(ordered):
        extra = leftover_finding(
            run, load_llm_config(url=llm_url, token=llm_token)
        )
        if extra is not None:
            ordered = _sort([*ordered, extra])
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


def _has_error(findings: list[Finding]) -> bool:
    return any(item.severity is Severity.error for item in findings)


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
