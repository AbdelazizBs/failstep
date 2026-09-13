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

---

## Phase 4 — Optional LLM leftover (done)

Only if no detector produced `error`. Opt-in: `FAILSTEP_LLM_URL`. Default path never networks. `--no-llm` skips. `--no-redact` warns; secrets are still stripped.

Fake HTTP in tests. Redaction test fails if `sk-` / `Bearer` is in the POST body. `Finding.source = llm`. Id `FS000`. Does not overwrite FS001–FS005.

No hardcoded OpenAI. No raw file upload. Extra: `failstep[llm]` (httpx).

Gate (green, 2026-09-13):

```text
python -m pytest
python -m ruff check .
python -m failstep diagnose tests/traces/leftover-secret.json
python -m failstep diagnose tests/traces/leftover-secret.json --no-llm
python -m failstep diagnose examples/traces/retry-loop.json
```

Without `FAILSTEP_LLM_URL`, leftover dump stays silent. Retry dump stays FS004.

---

## Phase 5 — RAG detectors (done)

Empty retrieval (FS006), duplicate chunks (FS007), conflicting sources (FS008). Only when `type=retrieval` steps exist. Duplicate identity is `id` / `doc_id` / `chunk_id`, else `source`+`text`. Conflicts fire only on a shared scalar field (not free-text). Different texts from different sources stay silent.

Gate (green, 2026-09-13):

```text
python -m pytest
python -m ruff check .
python -m failstep diagnose tests/traces/retrieval-silent.json
python -m failstep diagnose tests/traces/retrieval-conflict.json
python -m failstep diagnose tests/traces/retrieval-then-fail.json
```

Empty+duplicate dump → FS006 root, FS007 secondary, no FS008. Structured `refunds` true/false → FS008. Tool failure after a healthy retrieval stays FS003.

---

## Phase 6 — Compare (done)

`failstep compare old.json new.json`

Counted diffs only: finding ids gone/added/same, root-cause ids, and run fields that exist on both sides. Leftover is never called. Missing duration is not invented.

Gate (green, 2026-09-13):

```text
python -m pytest
python -m ruff check .
python -m failstep compare examples/traces/retry-loop.json examples/traces/success.json
python -m failstep compare examples/traces/success.json examples/traces/success.json
```

Retry vs success → exit 1, gone FS004, status failed → success, steps 8 → 4. Identical success files → exit 0.

---

## Phase 7 — Fix suggestions (done)

`failstep fix TRACE` prints the recommendation as a patch. Same voice as diagnose. Does not write the user's source. Leftover is never called.

Gate (green, 2026-09-13):

```text
python -m pytest
python -m ruff check .
python -m failstep fix examples/traces/retry-loop.json
python -m failstep fix examples/traces/success.json
```

Retry dump → exit 1, patch FS004, cap retries. Success dump → exit 0, patch none. Trace file bytes stay unchanged.

---

## Phase 8 — Release (done)

GitHub Actions: pytest + ruff, Python 3.11/3.12/3.13, Ubuntu + Windows.

PyPI packaging (`python -m build`), CONTRIBUTING, issue templates, changelog. Publish runs on a GitHub Release only after a `pypi` environment and trusted publisher exist.

Gate (green locally, 2026-09-13):

```text
python -m pytest
python -m ruff check .
python -m build
```

V1 freeze. There is no Phase 9 in this file.

---

## Non-goals forever unless we reopen DECISIONS.md

- Web UI
- SaaS
- Capture SDK as the main path
- Recover / rerun / self-heal
- Health scores
- Invented cost
- Emoji in default output
