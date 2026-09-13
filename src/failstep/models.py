from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class StepType(StrEnum):
    llm = "llm"
    tool = "tool"
    retrieval = "retrieval"
    other = "other"


class RunStatus(StrEnum):
    success = "success"
    failed = "failed"
    unknown = "unknown"


class Step(BaseModel):
    model_config = ConfigDict(extra="forbid")

    index: int
    id: str
    type: StepType
    name: str
    input: Any = None
    output: Any = None
    error: str | None = None
    latency_ms: int | None = None
    tokens_in: int | None = None
    tokens_out: int | None = None
    schema_: dict[str, Any] | None = Field(default=None, alias="schema")
    metadata: dict[str, Any] = Field(default_factory=dict)


class Run(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    name: str | None = None
    status: RunStatus
    duration_ms: int | None = None
    error: str | None = None
    tokens_in: int | None = None
    tokens_out: int | None = None
    steps: list[Step] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
