# Phases

Do not skip. Do not implement the next phase until the current **gate command** is green.

This file is the build order.

How we test: `docs/TESTING.md`.
How a report must look: `docs/OUTPUT.md`.

---

## Phase 0 — Research and lock (done)

Delivered: product, positioning, stack, architecture, trace format, decisions, testing, output, this file. Name: **failstep**. Git remote: `https://github.com/AbdelazizBs/failstep.git`.

---

## Phase 1 — Scaffold that inspects a file (done)

Installable CLI. Native JSON + JSONL. `inspect` prints the run. `diagnose` does not invent a finding.

Shipped: `pyproject.toml`, `src/failstep/` (`cli`, `models`, `parser`, `normalize`, `report`), examples, pytest, ruff clean.

Gate (green, 2026-09-13):

```text
python -m pytest tests/test_parser.py tests/test_inspect.py tests/test_cli_exit.py
python -m ruff check .
python -m failstep inspect examples/traces/retry-loop.json
```

`diagnose` on a valid file: "No detectors shipped yet. Use inspect, or wait for Phase 2." Exit 0. Garbage: exit 2.

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
