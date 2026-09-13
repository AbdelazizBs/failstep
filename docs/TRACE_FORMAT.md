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

## What sniffers may accept (Phase 2)

1. OpenAI dump: `messages[]` with `tool_calls` / `role=tool`
2. LangChain dump: `intermediate_steps` pairs
3. Phase 3: OTEL GenAI span list (`gen_ai.operation.name`)

Sniffers never drop errors on the floor. If a required mapping is missing, say so in inspect output.

## Stability

Native schema is versioned. Additive fields are fine. Renames need a new schema version field (`schema_version: 1`).
