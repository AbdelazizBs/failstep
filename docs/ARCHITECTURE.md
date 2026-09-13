# Architecture

V1 is a local CLI. No server. No database. No UI.

Package and command: **failstep**. Python 3.11+, pip-installable, `python -m failstep` as backup.

## Pipeline

```text
trace.json / trace.jsonl / otel.json
        |
        v
     parser          sniff format, reject garbage (exit 2)
        |
        v
    normalize        Run + Step (Pydantic)
        |
        v
    detectors        FS001-FS005, evidence only
        |
        +-- findings --> report (one root cause + secondary)
        |
        +-- no error finding
                 |
                 v
           optional LLM (Phase 4, if configured)
                 |
                 v
              report or "Insufficient evidence."
```

## Layout

Phase 3 (shipped). `adapters.py` maps OpenAI, LangChain, and exported OTEL GenAI JSON into native steps.

```text
src/failstep/
    __init__.py
    __main__.py
    cli.py
    errors.py
    models.py
    parser.py
    adapters.py
    normalize.py
    evidence.py
    diagnose.py
    report.py
    detectors/
        __init__.py
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

Later, not created yet: `redact.py`, `llm.py`.

No providers package. No FastAPI.

## Internal model

```text
Run    id, name, status, duration_ms, error, tokens_in/out, steps[]
Step   index, id, type, name, input, output, error, latency_ms, tokens, metadata
Finding  id (FS00x), detector, category, title, severity, step_ids,
         evidence[], recommendation,
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

Root cause = highest severity (`error` then `warning`), then this order, then first step index.

FS005 thresholds: step `latency_ms >= 15000` (error), run `duration_ms >= 30000` (error), one step `>= 80%` of run and `>= 5000ms` (warning).

## Output

Contract: `docs/OUTPUT.md`. Tests freeze it (`docs/TESTING.md`).

Terminal is the product. JSON is CI. Markdown is for GitHub comments.

ASCII-safe. No required emoji. No confidence field. One root cause, then secondary.

## Security

Traces are untrusted. Redact secrets before any LLM call. Default path never uploads. `--no-redact` warns.
