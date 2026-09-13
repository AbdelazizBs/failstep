from __future__ import annotations

from failstep.redact import contains_secret, redact


def test_redact_strips_openai_key_and_bearer() -> None:
    payload = {
        "authorization": "Bearer secret-token",
        "api_key": "sk-test-example",
        "ok": "paid",
    }
    cleaned = redact(payload)
    assert cleaned["authorization"] == "[redacted]"
    assert cleaned["api_key"] == "[redacted]"
    assert cleaned["ok"] == "paid"
    assert not contains_secret(str(cleaned))


def test_plain_text_is_unchanged() -> None:
    assert redact("I cannot find the order.") == "I cannot find the order."
