from __future__ import annotations

from collections.abc import Callable

from failstep.detectors.malformed import detect as detect_malformed
from failstep.detectors.retry import detect as detect_retry
from failstep.detectors.schema import detect as detect_schema
from failstep.detectors.timeout import detect as detect_timeout
from failstep.detectors.tool_error import detect as detect_tool_error
from failstep.models import Finding, Run

Detector = Callable[[Run], list[Finding]]

DETECTORS: list[Detector] = [
    detect_malformed,
    detect_schema,
    detect_tool_error,
    detect_retry,
    detect_timeout,
]


def run_detectors(run: Run) -> list[Finding]:
    findings: list[Finding] = []
    for detector in DETECTORS:
        findings.extend(detector(run))
    return findings
