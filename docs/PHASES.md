# Phases

Do not skip. Do not implement the next phase until the current **gate command** is green.

How we test: `docs/TESTING.md`.
How a report must look: `docs/OUTPUT.md`.

---

## Phase 0 — Research and lock (done)

Delivered: product, positioning, stack, architecture, trace format, decisions, testing, output, this file. Name: **failstep**. Git remote: `https://github.com/AbdelazizBs/failstep.git`.

---

## Phase 1 — Scaffold that inspects a file (done)

Installable CLI. Native JSON + JSONL. `inspect` prints the run.

---

## Phase 2 — Deterministic diagnose (done)

The product. Detectors FS001–FS005. `diagnose` terminal / json / markdown. `--fail-on`. Exit codes 0/1/2/3. OpenAI and LangChain sniff. Honesty tests.

Gate (green, 2026-09-13):

```text
python -m pytest
python -m ruff check .
python -m failstep diagnose examples/traces/retry-loop.json
python -m failstep diagnose examples/traces/retry-loop.json --format json
```

A stranger with no API key sees the retry, the steps, the args, and the cap-retries fix.

Test corpus gate (green, 2026-09-13):

```text
python -m pytest
python -m ruff check .
python -m failstep diagnose tests/traces/multi-failure.json
```

81 tests. Trap fixtures fire, stay silent, and do not invent evidence. `multi-failure.json` lights FS001–FS005 without mixing step ids.

---

## Phase 3 — OpenTelemetry ingest (done)

One adapter. Exported JSON spans. Map `invoke_agent` / `chat` / `execute_tool` / `retrieval`. Wrapper spans stay in `inspect` and do not set `latency_ms`, so they cannot steal FS005.

Not a live OTLP server. No `opentelemetry-sdk`.

Gate (green, 2026-09-13):

```text
python -m pytest
python -m ruff check .
python -m failstep diagnose examples/traces/otel-retry-loop.json
python -m failstep diagnose tests/traces/otel-tool-error.json
python -m failstep diagnose tests/traces/otel-http-only.json
```

Retry dump → FS004, no FS005. Tool error dump → FS003. HTTP-only dump → exit 2.

Freeze. Do not start Phase 4 until someone says go.

---

## Phase 4 — Optional LLM leftover

Only if no detector produced `error`.

Fake HTTP in tests. Redaction test must fail if `sk-` / `Bearer` leaves the machine. `--no-llm` still skips. `Finding.source = llm`.

No hardcoded OpenAI. No raw file upload.

---

## Phase 5 — RAG detectors

Empty retrieval, duplicate chunks, conflicting sources. Only when retrieval steps exist. Same golden + honesty rules.

---

## Phase 6 — Compare

`failstep compare old.json new.json`

Counted diffs only. JSON + terminal goldens.

---

## Phase 7 — Fix suggestions

`failstep fix trace.json` prints a suggested patch to stdout. Same voice as the recommendation line. Does not write the user's source.

---

## Phase 8 — Release

GitHub Actions: pytest + ruff, Python 3.11/3.12/3.13, Ubuntu + Windows.

PyPI, CONTRIBUTING, issue templates, changelog, 20s terminal recording, LinkedIn.

Not before Phase 2 goldens are boring.

---

## Non-goals forever unless we reopen DECISIONS.md

- Web UI
- SaaS
- Capture SDK as the main path
- Recover / rerun / self-heal
- Health scores
- Invented cost
- Emoji in default output
