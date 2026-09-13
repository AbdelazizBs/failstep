# Phases

Do not skip. Do not implement the next phase until the current one is demonstrable.

This file is the build order. Implementation has **not** started.

---

## Phase 0 — Research and lock (done)

Delivered:

- `docs/COMPETITORS.md`
- `docs/POSITIONING.md`
- `docs/PRODUCT.md`
- `docs/STACK.md`
- `docs/ARCHITECTURE.md`
- `docs/TRACE_FORMAT.md`
- `docs/DECISIONS.md`
- this file
- name: **failstep**
- git repo initialized, docs only

Stop. You read. You approve. Then Phase 1.

---

## Phase 1 — Scaffold that inspects a file

Goal: a real installable CLI that prints a run, no diagnosis yet.

1. `pyproject.toml`: package `failstep`, script `failstep = failstep.cli:app`
2. `src/failstep/` with `cli.py`, `models.py`, `parser.py`, `normalize.py`, `report.py`
3. Native JSON parser (TRACE_FORMAT.md). Garbage file = exit 2.
4. `failstep inspect examples/traces/retry-loop.json` prints the step table
5. `failstep version`
6. `failstep diagnose` exists but says detectors land in Phase 2 (or returns "no detectors yet") — do not fake a diagnosis
7. pytest: parse native JSON, parse JSONL, reject garbage
8. README 60-second inspect example
9. Ruff clean

Done when:

```text
uv run failstep inspect examples/traces/retry-loop.json
```

shows run id, status, duration, and each step type/name.

No LLM. No OTEL. No detectors.

---

## Phase 2 — Deterministic diagnose (MVP)

This is the product.

1. Detectors FS001–FS005
2. `failstep diagnose TRACE` with terminal / json / markdown
3. `--fail-on`, exit codes 0/1/2/3
4. Golden traces:
   - `schema-mismatch.json`
   - `retry-loop.json`
   - `malformed-json.json`
   - `tool-failure.json`
   - `timeout.json`
   - `success.json`
5. Format sniff (still no SDK):
   - native failstep JSON
   - OpenAI-style `messages` + `tool_calls`
   - LangChain-style `intermediate_steps`
   - unknown = exit 2 + hint
6. Tests per detector: fire on fixture, stay quiet on success, never invent fields
7. README diagnose example (text block is enough until Phase 8)

Done when the success definition in PRODUCT.md is true **without an API key**.

Freeze here. Do not start Phase 3 until someone other than you has run diagnose on a real dump.

---

## Phase 3 — OpenTelemetry ingest

One adapter. Exported JSON spans. Map:

- `invoke_agent` / `chat` / `execute_tool` / `retrieval`
- tool name, arguments, result, definitions
- tokens, errors

Not a live OTLP server.

Done when `failstep diagnose otel-trace.json` hits FS002/FS004 on a synthetic OTEL fixture.

---

## Phase 4 — Optional LLM leftover

Only if no detector produced `error`.

- Provider protocol
- Ollama + OpenAI-compatible
- Redact before send
- `--no-llm` default behavior stays "skip"
- Model must quote evidence or return Insufficient evidence
- Finding.source = `llm`

No hardcoded OpenAI. No sending the raw file.

---

## Phase 5 — RAG detectors

Empty retrieval, duplicate chunks, conflicting sources. Only when retrieval steps exist. Never claim factual correctness without evidence.

---

## Phase 6 — Compare

`failstep compare old.json new.json`

Counted diffs only: latency, tokens, LLM/tool counts, failures, retries.

---

## Phase 7 — Fix suggestions

`failstep fix trace.json` prints a suggested patch (tool description, retry cap). Does not write the user's source unless they pass an explicit flag later. V1 of fix is stdout only.

---

## Phase 8 — Release

PyPI, GitHub Actions (pytest + ruff), CONTRIBUTING, issue templates, changelog, 20s terminal recording, LinkedIn.

Not before Phase 2 is boringly solid.

---

## Non-goals forever unless we reopen DECISIONS.md

- Web UI
- SaaS
- Capture SDK as the main path
- Recover / rerun / self-heal
- Health scores
- Invented cost
