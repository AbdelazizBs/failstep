from __future__ import annotations

import json
from typing import Any


def adapt(data: Any) -> dict[str, Any] | None:
    if not isinstance(data, dict):
        return None
    if _is_openai(data):
        payload = _openai(data)
    elif _is_langchain(data):
        payload = _langchain(data)
    else:
        return None
    steps = payload.get("steps")
    if not isinstance(steps, list) or not steps:
        return None
    return payload


def _is_openai(data: dict[str, Any]) -> bool:
    messages = data.get("messages")
    if not isinstance(messages, list) or not messages:
        return False
    return any(isinstance(item, dict) and "role" in item for item in messages)


def _is_langchain(data: dict[str, Any]) -> bool:
    steps = data.get("intermediate_steps")
    return isinstance(steps, list) and bool(steps)


def _openai(data: dict[str, Any]) -> dict[str, Any]:
    steps: list[dict[str, Any]] = []
    pending: dict[str, dict[str, Any]] = {}
    for message in data.get("messages") or []:
        if not isinstance(message, dict):
            continue
        role = message.get("role")
        if role == "assistant":
            tool_calls = message.get("tool_calls") or []
            content = message.get("content")
            if content and not tool_calls:
                steps.append(
                    {
                        "type": "llm",
                        "name": "assistant",
                        "output": content,
                    }
                )
            if not isinstance(tool_calls, list):
                continue
            for call in tool_calls:
                if not isinstance(call, dict):
                    continue
                fn = (
                    call.get("function")
                    if isinstance(call.get("function"), dict)
                    else {}
                )
                args: Any = fn.get("arguments", {})
                if isinstance(args, str):
                    try:
                        args = json.loads(args)
                    except json.JSONDecodeError:
                        pass
                step = {
                    "id": call.get("id"),
                    "type": "tool",
                    "name": fn.get("name") or "tool",
                    "input": args,
                }
                call_id = call.get("id")
                if isinstance(call_id, str):
                    pending[call_id] = step
                steps.append(step)
        elif role == "tool":
            output = _maybe_json(message.get("content"))
            error = message.get("error")
            if not (isinstance(error, str) and error):
                error = None
            if error is None and isinstance(output, str) and _looks_error(output):
                error = output
                output = None
            call_id = message.get("tool_call_id")
            target = pending.get(call_id) if isinstance(call_id, str) else None
            if target is not None:
                target["output"] = output
                if error:
                    target["error"] = error
            else:
                steps.append(
                    {
                        "type": "tool",
                        "name": message.get("name") or "tool",
                        "output": output,
                        "error": error,
                    }
                )
    run_id = data.get("run_id") or data.get("id") or "openai-run"
    if not isinstance(run_id, str):
        run_id = "openai-run"
    return {
        "run_id": run_id,
        "status": data.get("status") or "unknown",
        "steps": steps,
        "tokens_in": data.get("tokens_in"),
        "tokens_out": data.get("tokens_out"),
        "duration_ms": data.get("duration_ms"),
    }


def _langchain(data: dict[str, Any]) -> dict[str, Any]:
    steps: list[dict[str, Any]] = []
    for item in data.get("intermediate_steps") or []:
        action, observation = _pair(item)
        tool = action.get("tool") or action.get("name") or "tool"
        tool_input = action.get("tool_input", action.get("input"))
        error = None
        output: Any = observation
        if isinstance(observation, str) and _looks_error(observation):
            error = observation
            output = None
        steps.append(
            {
                "type": "tool",
                "name": tool,
                "input": tool_input,
                "output": output,
                "error": error,
            }
        )
    final = data.get("output")
    if final is not None:
        steps.append({"type": "llm", "name": "output", "output": final})
    run_id = data.get("run_id") or "langchain-run"
    if not isinstance(run_id, str):
        run_id = "langchain-run"
    return {
        "run_id": run_id,
        "status": data.get("status") or "unknown",
        "steps": steps,
        "tokens_in": data.get("tokens_in"),
        "tokens_out": data.get("tokens_out"),
        "duration_ms": data.get("duration_ms"),
    }


def _pair(item: Any) -> tuple[dict[str, Any], Any]:
    if isinstance(item, (list, tuple)) and len(item) >= 2:
        action, observation = item[0], item[1]
    elif isinstance(item, dict) and "action" in item:
        action, observation = item.get("action"), item.get("observation")
    else:
        action, observation = item, None
    if not isinstance(action, dict):
        action = {"tool": str(action)}
    return action, observation


def _maybe_json(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    text = value.strip()
    if text[:1] in "{[":
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return value
    return value


def _looks_error(text: str) -> bool:
    head = text[:80].lower()
    return "error" in head or "traceback" in head or "exception" in head
