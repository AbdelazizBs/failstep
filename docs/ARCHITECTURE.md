# Architecture

V1 is a local CLI. No server. No database. No UI.

Package and command: **failstep**. Python 3.11+, pip-installable, `python -m failstep` as backup.

## Pipeline

```text
trace.json / trace.jsonl / otel.json
        │
        ▼
     parser          sniff format, reject garbage (exit 2)
        │
        ▼
    normalize        Run + Step (Pydantic)
        │
        ▼
    detectors        FS001–FS005, evidence only
        │
        ├── findings ──► report (one root cause + secondary)
        │
        └── no error finding
                 │
                 ▼
           optional LLM (Phase 4, if configured)
                 │
                 ▼
              report or "Insufficient evidence."
```

## Layout (Phase 1+)

```text
src/failstep/
    __init__.py
    cli.py
    models.py
    parser.py
    normalize.py
    diagnose.py
    report.py
    redact.py
    llm.py
    detectors/
        base.py
        malformed.py
        schema.py
        tool_error.py
        retry.py
        timeout.py

tests/
examples/traces/
docs/
pyproject.toml
README.md
LICENSE
```

Phase 1 does not create a providers package or FastAPI. `report.py` is enough.

## Internal model

```text
Run    id, name, status, duration_ms, error, tokens_in/out, steps[]
Step   index, id, type, name, input, output, error, latency_ms, tokens, metadata
Finding  id (FS00x), detector, category, title, severity, step_ids,
         evidence[], recommendation, impact (counted only),
         source (deterministic | heuristic | llm)
Report   run, root_cause, secondary[], findings[]
```

No confidence field on Finding.

Nested OTEL spans flatten to ordered steps. Optional `parent_id` in metadata.

## Detector order

1. FS001 MalformedOutput
2. FS002 ToolSchema
3. FS003 ToolFailure
4. FS004 RetryLoop
5. FS005 Timeout

Root cause = highest severity, then this order.

## Output

Terminal is the product. JSON is CI. Markdown is for GitHub comments.

ASCII-safe. No required emoji.

```text
failstep
Run: checkout-agent
Status: failed
Duration: 14820 ms
Steps: 8

Root cause  FS002 tool schema  (step 7, get_customer)
Evidence
  expected required: customer_id
  received keys: email
  step error: "customer_id is required"

Secondary   FS004 retry loop  get_customer x3 same args

Recommendation
  Validate tool arguments against the schema before execution.
  Stop retrying an identical failed call.
```

## Security

Traces are untrusted. Redact secrets before any LLM call. Default path never uploads. `--no-redact` warns.
