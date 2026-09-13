from __future__ import annotations

import re
from typing import Any

_SECRET = re.compile(
    r"sk-[A-Za-z0-9_-]+|Bearer\s+\S+",
    re.IGNORECASE,
)


def redact(value: Any) -> Any:
    if isinstance(value, str):
        return _SECRET.sub("[redacted]", value)
    if isinstance(value, dict):
        return {str(key): redact(inner) for key, inner in value.items()}
    if isinstance(value, list):
        return [redact(item) for item in value]
    if isinstance(value, tuple):
        return [redact(item) for item in value]
    return value


def contains_secret(text: str) -> bool:
    return _SECRET.search(text) is not None
