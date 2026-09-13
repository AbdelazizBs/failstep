from __future__ import annotations

import re

from failstep.evidence import finding
from failstep.models import Finding, Run, Severity, Step

STEP_MS = 15_000
RUN_MS = 30_000
DOMINATE_RATIO = 0.8
DOMINATE_MIN_MS = 5_000

_TIMEOUT_TEXT = re.compile(r"\btime.?out\b", re.IGNORECASE)


def detect(run: Run) -> list[Finding]:
    timed_steps = [step for step in run.steps if _step_timeout(step)]
    run_hit = _run_timeout(run)
    slowest = max(run.steps, key=lambda s: s.latency_ms or 0, default=None)
    dominate = _dominates(run, slowest)

    if timed_steps:
        step = max(timed_steps, key=lambda s: s.latency_ms or 0)
        return [_timeout_finding(run, [step], Severity.error, "step over threshold")]
    if run_hit:
        steps = [slowest] if slowest and (slowest.latency_ms or 0) > 0 else []
        if not steps:
            return []
        return [_timeout_finding(run, steps, Severity.error, "run over threshold")]
    if dominate and slowest is not None:
        return [
            _timeout_finding(
                run, [slowest], Severity.warning, "step dominates duration"
            )
        ]
    return []


def _step_timeout(step: Step) -> bool:
    if (step.latency_ms or 0) >= STEP_MS:
        return True
    if step.error and _TIMEOUT_TEXT.search(step.error):
        return True
    return False


def _run_timeout(run: Run) -> bool:
    if (run.duration_ms or 0) >= RUN_MS:
        return True
    if run.error and _TIMEOUT_TEXT.search(run.error):
        return True
    return False


def _dominates(run: Run, step: Step | None) -> bool:
    if step is None or run.duration_ms is None or run.duration_ms <= 0:
        return False
    latency = step.latency_ms or 0
    if latency < DOMINATE_MIN_MS:
        return False
    return latency / run.duration_ms >= DOMINATE_RATIO


def _timeout_finding(
    run: Run, steps: list[Step], severity: Severity, reason: str
) -> Finding:
    step = steps[0]
    evidence = [
        ("reason", reason),
        ("step", step.name),
        ("latency_ms", step.latency_ms),
    ]
    if run.duration_ms is not None:
        evidence.append(("run_duration_ms", run.duration_ms))
    return finding(
        code="FS005",
        detector="timeout",
        title="timeout",
        steps=steps,
        evidence=evidence,
        recommendation="Bound the step with a timeout. Stop waiting after the limit.",
        severity=severity,
    )
