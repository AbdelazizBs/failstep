# Trace format

V1 native schema. Adapters map into this. If we cannot map, we exit 2.

## Native JSON

```json
{
  "run_id": "checkout-agent",
  "status": "failed",
  "duration_ms": 14820,
  "error": null,
  "tokens_in": 4200,
  "tokens_out": 800,
  "steps": [
    {
      "id": "step_7",
      "type": "tool",
      "name": "get_customer",
      "input": {"email": "aziz@example.com"},
      "output": null,
      "error": "customer_id is required",
      "latency_ms": 120,
      "schema": {
        "required": ["customer_id"],
        "properties": {
          "customer_id": {"type": "string"}
        }
      }
    }
  ]
}
```

JSONL: one step object per line, optional first line `{ "run_id": "...", "status": "failed" }`.

## Field rules

- `type`: `llm` | `tool` | `retrieval` | `other`
- `status`: `success` | `failed` | `unknown`
- `schema` is optional. Without it, FS002 only fires on explicit validation error text plus obvious shape bugs.
- Extra fields allowed. Unknown fields go to `metadata`.
- Missing optional fields are null, not invented.

## What sniffers accept

1. Native failstep JSON / JSONL / a JSON array of steps
2. OpenAI dump: `messages[]` with `tool_calls` / `role=tool`
3. LangChain dump: `intermediate_steps` pairs
4. Exported OpenTelemetry GenAI JSON (`gen_ai.operation.name`)

A `messages` array that maps to zero steps is unknown shape (exit 2).
HTTP-only OTLP (no `gen_ai.*`) is unknown shape (exit 2).

Sniffers never drop errors on the floor. Native `steps` wins if both native and adapter keys exist.

## OpenTelemetry JSON (Phase 3)

Supported dumps, not a live collector:

1. OTLP JSON: `resourceSpans` / `resource_spans` → `scopeSpans` / `scope_spans` → `spans`
2. Python SDK export: `{ "spans": [ ... ] }` with `context.span_id` and dict `attributes`

Attributes may be OTLP `{key, value: {stringValue|intValue|boolValue}}` or a plain dict. JSON strings are decoded when they look like objects.

| `gen_ai.operation.name` | Step type |
|---|---|
| `chat` / `generate_content` / `text_completion` | `llm` |
| `execute_tool` | `tool` |
| `retrieval` | `retrieval` |
| `invoke_agent` / `invoke_workflow` / `create_agent` / other | `other` |

Tool args: `gen_ai.tool.call.arguments`. Tool result: `gen_ai.tool.call.result`. Schema for FS002: `gen_ai.tool.definitions`. Errors: span `status.message`, `exception.message`, or exception events. Timestamps are nanoseconds; child spans get `latency_ms`. Wrapper ops omit `latency_ms` so they cannot dominate FS005; run `duration_ms` still uses their start/end. Spans sort by start time. `parent_id` is kept in step metadata.

This is not universal OTEL support.

## Stability

Native schema is versioned. Additive fields are fine. Renames need a new schema version field (`schema_version: 1`).
