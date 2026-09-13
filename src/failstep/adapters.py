from __future__ import annotations

import json
from typing import Any


def adapt(data: Any) -> dict[str, Any] | None:
    if isinstance(data, dict) and _is_openai(data):
        payload = _openai(data)
    elif isinstance(data, dict) and _is_langchain(data):
        payload = _langchain(data)
    elif _is_otel(data):
        payload = _otel(data)
    else:
        return None
    steps = payload.get("steps")
    if not isinstance(steps, list) or not steps:
        return None
    return payload


def is_otel_payload(data: Any) -> bool:
    return _is_otel(data)


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


_LLM_OPS = {"chat", "generate_content", "text_completion"}
_TOOL_OPS = {"execute_tool"}
_RETRIEVAL_OPS = {"retrieval"}
_WRAPPER_OPS = {"invoke_agent", "invoke_workflow", "create_agent"}
_ERROR_STATUS = {2, "2", "STATUS_CODE_ERROR", "ERROR", "error"}


def _is_otel(data: Any) -> bool:
    return any(_has_gen_ai(span) for span in _collect_spans(data))


def _has_gen_ai(span: dict[str, Any]) -> bool:
    attrs = _attr_map(span)
    return any(key.startswith("gen_ai.") for key in attrs)


def _collect_spans(data: Any) -> list[dict[str, Any]]:
    if isinstance(data, list):
        if data and all(isinstance(item, dict) for item in data):
            if any(_looks_like_otel_span(item) for item in data):
                return [item for item in data if isinstance(item, dict)]
        return []
    if not isinstance(data, dict):
        return []
    for key in ("resourceSpans", "resource_spans"):
        blocks = data.get(key)
        if not isinstance(blocks, list):
            continue
        out: list[dict[str, Any]] = []
        for block in blocks:
            if not isinstance(block, dict):
                continue
            for scope_key in ("scopeSpans", "scope_spans"):
                scopes = block.get(scope_key) or []
                if not isinstance(scopes, list):
                    continue
                for scope in scopes:
                    if not isinstance(scope, dict):
                        continue
                    spans = scope.get("spans")
                    if isinstance(spans, list):
                        out.extend(
                            item for item in spans if isinstance(item, dict)
                        )
        if out:
            return out
    spans = data.get("spans")
    if isinstance(spans, list) and any(
        isinstance(item, dict) and _looks_like_otel_span(item) for item in spans
    ):
        return [item for item in spans if isinstance(item, dict)]
    steps = data.get("steps")
    if (
        isinstance(steps, list)
        and steps
        and all(
            isinstance(item, dict) and _looks_like_otel_span(item)
            for item in steps
        )
    ):
        return [item for item in steps if isinstance(item, dict)]
    if _looks_like_otel_span(data):
        return [data]
    return []


def _looks_like_otel_span(item: dict[str, Any]) -> bool:
    attrs = _attr_map(item)
    if any(key.startswith("gen_ai.") for key in attrs):
        return True
    if item.get("spanId") or item.get("span_id") or item.get("traceId"):
        if "attributes" in item or "startTimeUnixNano" in item:
            return True
    context = item.get("context")
    if isinstance(context, dict) and (
        context.get("span_id") or context.get("trace_id")
    ):
        if "attributes" in item:
            return True
    return False


def _otel(data: Any) -> dict[str, Any]:
    spans = _collect_spans(data)
    nanos = [_start_nano(span) for span in spans]
    if nanos and all(value is not None for value in nanos):
        order = sorted(range(len(spans)), key=lambda i: (nanos[i], i))
    else:
        order = list(range(len(spans)))

    steps: list[dict[str, Any]] = []
    for index in order:
        mapped = _span_to_step(spans[index])
        if mapped is not None:
            steps.append(mapped)

    tokens_in = _sum_int(step.get("tokens_in") for step in steps)
    tokens_out = _sum_int(step.get("tokens_out") for step in steps)
    duration_ms = _run_duration_ms(spans, steps)
    status = "failed" if any(step.get("error") for step in steps) else "success"
    if status == "success":
        if any(_is_error_status(_status_code(span)) for span in spans):
            status = "failed"
    run_id = _run_id(data, steps)
    return {
        "run_id": run_id,
        "status": status,
        "steps": steps,
        "tokens_in": tokens_in,
        "tokens_out": tokens_out,
        "duration_ms": duration_ms,
    }


def _span_to_step(span: dict[str, Any]) -> dict[str, Any] | None:
    attrs = _attr_map(span)
    op = attrs.get("gen_ai.operation.name")
    if not isinstance(op, str) or not op:
        op = _op_from_name(span.get("name"))
    if not op and "gen_ai.tool.name" in attrs:
        op = "execute_tool"
    if not op and "gen_ai.request.model" in attrs:
        op = "chat"
    if not op and not any(key.startswith("gen_ai.") for key in attrs):
        return None

    if op in _TOOL_OPS:
        step_type = "tool"
        name = attrs.get("gen_ai.tool.name") or _name_tail(
            span.get("name"), "tool"
        )
        incoming = _maybe_json(attrs.get("gen_ai.tool.call.arguments"))
        outgoing = _maybe_json(attrs.get("gen_ai.tool.call.result"))
        schema = _tool_schema(attrs, name if isinstance(name, str) else "")
    elif op in _LLM_OPS:
        step_type = "llm"
        name = attrs.get("gen_ai.request.model") or _name_tail(
            span.get("name"), "chat"
        )
        incoming = _maybe_json(attrs.get("gen_ai.input.messages"))
        outgoing = _maybe_json(attrs.get("gen_ai.output.messages"))
        schema = None
    elif op in _RETRIEVAL_OPS:
        step_type = "retrieval"
        name = attrs.get("gen_ai.tool.name") or _name_tail(
            span.get("name"), "retrieval"
        )
        incoming = attrs.get("gen_ai.retrieval.query.text")
        if incoming is not None:
            incoming = {"query": incoming}
        outgoing = _maybe_json(attrs.get("gen_ai.retrieval.documents"))
        schema = None
    else:
        step_type = "other"
        name = attrs.get("gen_ai.agent.name") or _name_tail(
            span.get("name"), op or "span"
        )
        incoming = _maybe_json(attrs.get("gen_ai.input.messages"))
        outgoing = _maybe_json(attrs.get("gen_ai.output.messages"))
        schema = None

    if not isinstance(name, str) or not name:
        name = op or "span"

    error = _span_error(span, attrs)
    latency = None if op in _WRAPPER_OPS else _latency_ms(span)
    step: dict[str, Any] = {
        "id": _span_id(span),
        "type": step_type,
        "name": name,
        "input": incoming,
        "output": outgoing,
        "error": error,
        "latency_ms": latency,
        "tokens_in": _as_int(attrs.get("gen_ai.usage.input_tokens")),
        "tokens_out": _as_int(attrs.get("gen_ai.usage.output_tokens")),
    }
    if schema is not None:
        step["schema"] = schema
    parent = _parent_id(span)
    meta: dict[str, Any] = {}
    if parent:
        meta["parent_id"] = parent
    if op:
        meta["gen_ai.operation.name"] = op
    if meta:
        step["metadata"] = meta
    return step


def _tool_schema(attrs: dict[str, Any], tool_name: str) -> dict[str, Any] | None:
    raw = attrs.get("gen_ai.tool.definitions")
    raw = _maybe_json(raw)
    if isinstance(raw, dict):
        raw = [raw]
    if not isinstance(raw, list):
        return None
    for item in raw:
        if not isinstance(item, dict):
            continue
        if tool_name and item.get("name") not in {None, tool_name}:
            continue
        params = item.get("parameters") or item.get("schema")
        if isinstance(params, dict) and (
            "required" in params or "properties" in params
        ):
            return params
        if "required" in item or "properties" in item:
            return item
    return None


def _span_error(span: dict[str, Any], attrs: dict[str, Any]) -> str | None:
    status = span.get("status") if isinstance(span.get("status"), dict) else {}
    message = status.get("message") or status.get("description")
    if isinstance(message, str) and message.strip():
        return message
    for key in ("exception.message", "error.type", "error.message"):
        value = attrs.get(key)
        if isinstance(value, str) and value.strip():
            return value
    events = span.get("events")
    if isinstance(events, list):
        for event in events:
            if not isinstance(event, dict):
                continue
            name = event.get("name") or event.get("event_name")
            event_attrs = _attr_map(event) if "attributes" in event else event
            if name == "exception" or event_attrs.get("exception.message"):
                text = event_attrs.get("exception.message")
                if isinstance(text, str) and text.strip():
                    return text
    return None


def _status_code(span: dict[str, Any]) -> Any:
    status = span.get("status")
    if not isinstance(status, dict):
        return None
    if "code" in status:
        return status.get("code")
    return status.get("status_code")


def _is_error_status(code: Any) -> bool:
    return code in _ERROR_STATUS


def _attr_map(item: dict[str, Any]) -> dict[str, Any]:
    raw = item.get("attributes")
    if isinstance(raw, dict):
        mapped: dict[str, Any] = {}
        for key, value in raw.items():
            mapped[str(key)] = (
                _maybe_json(value) if isinstance(value, str) else value
            )
        return mapped
    if not isinstance(raw, list):
        return {}
    out: dict[str, Any] = {}
    for entry in raw:
        if not isinstance(entry, dict):
            continue
        key = entry.get("key")
        if not isinstance(key, str):
            continue
        out[key] = _otel_value(entry.get("value"))
    return out


def _otel_value(value: Any) -> Any:
    if not isinstance(value, dict):
        return _maybe_json(value) if isinstance(value, str) else value
    if "stringValue" in value:
        return _maybe_json(value["stringValue"])
    if "intValue" in value:
        return _as_int(value["intValue"])
    if "doubleValue" in value:
        return value["doubleValue"]
    if "boolValue" in value:
        return value["boolValue"]
    if "arrayValue" in value and isinstance(value["arrayValue"], dict):
        values = value["arrayValue"].get("values") or []
        if isinstance(values, list):
            return [_otel_value(item) for item in values]
    if "kvlistValue" in value and isinstance(value["kvlistValue"], dict):
        values = value["kvlistValue"].get("values") or []
        mapped: dict[str, Any] = {}
        if isinstance(values, list):
            for entry in values:
                if isinstance(entry, dict) and isinstance(entry.get("key"), str):
                    mapped[entry["key"]] = _otel_value(entry.get("value"))
        return mapped
    return value


def _span_id(span: dict[str, Any]) -> str | None:
    for key in ("spanId", "span_id"):
        value = span.get(key)
        if isinstance(value, str) and value:
            return value
    context = span.get("context")
    if isinstance(context, dict):
        value = context.get("span_id") or context.get("spanId")
        if isinstance(value, str) and value:
            return value
    return None


def _parent_id(span: dict[str, Any]) -> str | None:
    for key in ("parentSpanId", "parent_span_id", "parent_id"):
        value = span.get(key)
        if isinstance(value, str) and value:
            return value
    return None


def _start_nano(span: dict[str, Any]) -> int | None:
    for key in ("startTimeUnixNano", "start_time_unix_nano", "start_time"):
        nano = _as_nano(span.get(key))
        if nano is not None:
            return nano
    return None


def _end_nano(span: dict[str, Any]) -> int | None:
    for key in ("endTimeUnixNano", "end_time_unix_nano", "end_time"):
        nano = _as_nano(span.get(key))
        if nano is not None:
            return nano
    return None


def _as_nano(value: Any) -> int | None:
    number = _as_int(value)
    if number is not None:
        return number
    return None


def _latency_ms(span: dict[str, Any]) -> int | None:
    start = _start_nano(span)
    end = _end_nano(span)
    if start is None or end is None or end < start:
        return None
    return (end - start) // 1_000_000


def _run_duration_ms(
    spans: list[dict[str, Any]], steps: list[dict[str, Any]]
) -> int | None:
    starts = [_start_nano(span) for span in spans]
    ends = [_end_nano(span) for span in spans]
    present = [
        (start, end)
        for start, end in zip(starts, ends, strict=True)
        if start is not None and end is not None
    ]
    if present:
        first = min(start for start, _end in present)
        last = max(end for _start, end in present)
        return (last - first) // 1_000_000
    latencies = [
        step.get("latency_ms")
        for step in steps
        if isinstance(step.get("latency_ms"), int)
    ]
    if latencies:
        return max(latencies)
    return None


def _run_id(data: Any, steps: list[dict[str, Any]]) -> str:
    if isinstance(data, dict):
        for key in ("run_id", "id"):
            value = data.get(key)
            if isinstance(value, str) and value:
                return value
        for block_key in ("resourceSpans", "resource_spans"):
            blocks = data.get(block_key)
            if not isinstance(blocks, list):
                continue
            for block in blocks:
                if not isinstance(block, dict):
                    continue
                resource = block.get("resource")
                if not isinstance(resource, dict):
                    continue
                attrs = _attr_map(resource)
                name = attrs.get("service.name")
                if isinstance(name, str) and name:
                    return name
    for step in steps:
        if step.get("type") == "other" and step.get("name"):
            return str(step["name"])
    return "otel-run"


def _op_from_name(name: Any) -> str | None:
    if not isinstance(name, str) or not name:
        return None
    head = name.split()[0]
    known = _LLM_OPS | _TOOL_OPS | _RETRIEVAL_OPS | {
        "invoke_agent",
        "invoke_workflow",
        "create_agent",
        "embeddings",
    }
    if head in known:
        return head
    if name in known:
        return name
    return None


def _name_tail(name: Any, default: str) -> str:
    if not isinstance(name, str) or not name:
        return default
    parts = name.split(None, 1)
    if len(parts) == 2:
        return parts[1]
    return name


def _as_int(value: Any) -> int | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    if isinstance(value, str) and value.lstrip("-").isdigit():
        return int(value)
    return None


def _sum_int(values: Any) -> int | None:
    total = 0
    found = False
    for value in values:
        number = _as_int(value)
        if number is None:
            continue
        total += number
        found = True
    return total if found else None
