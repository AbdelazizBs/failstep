from __future__ import annotations

from failstep.evidence import canonical, finding
from failstep.models import Finding, Run, Step, StepType


def detect(run: Run) -> list[Finding]:
    findings: list[Finding] = []
    streak: list[Step] = []
    streak_key: tuple[str, str] | None = None

    def flush() -> None:
        nonlocal streak, streak_key
        if len(streak) >= 3 and streak_key is not None:
            findings.append(_finding(streak))
        streak = []
        streak_key = None

    for step in run.steps:
        if step.type is not StepType.tool:
            flush()
            continue
        key = (step.name, canonical(step.input))
        if streak_key == key:
            streak.append(step)
            continue
        flush()
        streak = [step]
        streak_key = key
    flush()
    return findings


def _finding(steps: list[Step]) -> Finding:
    first = steps[0]
    outputs = [canonical(step.output) for step in steps]
    unchanged = len(set(outputs)) == 1
    return finding(
        code="FS004",
        detector="retry",
        title="retry loop",
        steps=steps,
        evidence=[
            ("identical calls", len(steps)),
            ("tool", first.name),
            ("args", first.input),
            ("outputs", "unchanged" if unchanged else "changed"),
        ],
        recommendation=(
            "Cap identical tool retries at 1. Return the first error to the model."
        ),
    )
