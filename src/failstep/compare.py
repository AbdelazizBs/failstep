from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from failstep.diagnose import diagnose
from failstep.models import Finding, Report, Run

_RUN_INT_KEYS = ("steps", "duration_ms", "tokens_in", "tokens_out")


@dataclass(frozen=True)
class FieldDelta:
    key: str
    old: Any
    new: Any
    delta: int | None = None


@dataclass(frozen=True)
class CompareResult:
    old_file: str
    new_file: str
    old_run: Run
    new_run: Run
    old_root: Finding | None
    new_root: Finding | None
    old_ids: tuple[str, ...]
    new_ids: tuple[str, ...]
    gone: tuple[str, ...]
    added: tuple[str, ...]
    same: tuple[str, ...]
    run: tuple[FieldDelta, ...]

    def has_diff(self) -> bool:
        return bool(self.gone or self.added or self.run)


def compare_reports(old: Report, new: Report) -> CompareResult:
    old_ids = _finding_ids(old)
    new_ids = _finding_ids(new)
    old_set = set(old_ids)
    new_set = set(new_ids)
    gone = tuple(item for item in old_ids if item not in new_set)
    added = tuple(item for item in new_ids if item not in old_set)
    same = tuple(item for item in old_ids if item in new_set)
    return CompareResult(
        old_file=old.file,
        new_file=new.file,
        old_run=old.run,
        new_run=new.run,
        old_root=old.root_cause,
        new_root=new.root_cause,
        old_ids=old_ids,
        new_ids=new_ids,
        gone=gone,
        added=added,
        same=same,
        run=_run_deltas(old.run, new.run),
    )


def compare_runs(
    old_run: Run,
    new_run: Run,
    old_file: str,
    new_file: str,
) -> CompareResult:
    old = diagnose(old_run, old_file, no_llm=True)
    new = diagnose(new_run, new_file, no_llm=True)
    return compare_reports(old, new)


def _finding_ids(report: Report) -> tuple[str, ...]:
    seen: list[str] = []
    for item in report.findings:
        if item.id not in seen:
            seen.append(item.id)
    return tuple(seen)


def _run_value(run: Run, key: str) -> Any:
    if key == "status":
        return run.status.value
    if key == "steps":
        return len(run.steps)
    if key == "duration_ms":
        return run.duration_ms
    if key == "tokens_in":
        return run.tokens_in
    if key == "tokens_out":
        return run.tokens_out
    raise KeyError(key)


def _run_deltas(old: Run, new: Run) -> tuple[FieldDelta, ...]:
    out: list[FieldDelta] = []
    old_status = old.status.value
    new_status = new.status.value
    if old_status != new_status:
        out.append(FieldDelta(key="status", old=old_status, new=new_status))
    for key in _RUN_INT_KEYS:
        old_value = _run_value(old, key)
        new_value = _run_value(new, key)
        if old_value is None or new_value is None:
            continue
        if old_value == new_value:
            continue
        if not isinstance(old_value, int) or not isinstance(new_value, int):
            continue
        out.append(
            FieldDelta(
                key=key,
                old=old_value,
                new=new_value,
                delta=new_value - old_value,
            )
        )
    return tuple(out)
