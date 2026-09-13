# Phases

Do not skip. Do not implement the next phase until the current **gate command** is green.

This file is the build order. Implementation has **not** started.

How we test: `docs/TESTING.md`.
How a report must look: `docs/OUTPUT.md`.

---

## Phase 0 — Research and lock (done)

Delivered: product, positioning, stack, architecture, trace format, decisions, testing, output, this file. Name: **failstep**. Git remote: `https://github.com/AbdelazizBs/failstep.git`.

Stop. You read. You approve. Then Phase 1.

---

## Phase 1 — Scaffold that inspects a file

Goal: a real installable CLI that prints a run. No diagnosis yet.

1. `pyproject.toml`: package `failstep`, script `failstep = failstep.cli:app`, `python -m failstep`
2. `src/failstep/` with `cli.py`, `models.py`, `parser.py`, `normalize.py`, `report.py`
3. Native JSON parser (`TRACE_FORMAT.md`). Garbage file = exit 2, message from `OUTPUT.md`
4. `failstep inspect` matches the inspect layout in `OUTPUT.md`
5. `failstep version` prints `failstep 0.1.0`
6. `failstep diagnose` on a valid file: no fake finding. Message: detectors land in Phase 2. Exit 0.
7. pytest: parse native JSON, parse JSONL, reject garbage, inspect golden, exit codes 0/2
8. README 60-second inspect example (terminal block from the golden)
9. Ruff clean

Gate:

```text
uv run pytest tests/test_parser.py tests/test_inspect.py tests/test_cli_exit.py
uv run ruff check .
uv run failstep inspect examples/traces/retry-loop.json
```

Inspect must show run id, status, duration, and each step type/name.

No LLM. No OTEL. No detectors.

---

## Phase 2 — Deterministic diagnose (MVP)

This is the product.

1. Detectors FS001–FS005
2. `failstep diagnose TRACE` terminal / json / markdown — **exactly** `OUTPUT.md`
3. `--fail-on`, exit codes 0/1/2/3
4. Golden traces + frozen reports in `tests/goldens/`
5. Format sniff (no SDK): native, OpenAI `messages` + `tool_calls`, LangChain `intermediate_steps`. Unknown = exit 2
6. Tests per detector: fire, silent on success, evidence strings found in the fixture
7. Honesty test: no `confidence` key, every `step_ids` exists

Gate:

```text
uv run pytest
uv run failstep diagnose examples/traces/retry-loop.json
uv run failstep diagnose examples/traces/retry-loop.json --format json
```

A stranger with no API key sees the retry, the steps, the args, and the cap-retries fix.

Freeze. Do not start Phase 3 until someone other than you has run diagnose on a real dump.

---

## Phase 3 — OpenTelemetry ingest

One adapter. Exported JSON spans. Map `invoke_agent` / `chat` / `execute_tool` / `retrieval`.

Gate: synthetic OTEL fixture → FS002 or FS004. New goldens. Mapping that drops a tool error fails the test.

Not a live OTLP server.

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
