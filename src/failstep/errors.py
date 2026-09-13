from __future__ import annotations


class ParseError(Exception):
    """User-facing input error. CLI maps this to exit 2."""

    def __init__(self, message: str, file: str, code: str = "invalid_input") -> None:
        super().__init__(message)
        self.message = message
        self.file = file
        self.code = code
