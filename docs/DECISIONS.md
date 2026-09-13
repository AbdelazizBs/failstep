# Decisions

Locked. Change on purpose, in this file.

## Name

**failstep**

Checked 2026-09-13:

| Candidate | Result |
|---|---|
| agent-doctor | Dead. PyPI SDK + npm MCP scanner + GitHub CLIs |
| agentlint | Dead. Real-time coding-agent guardrails |
| runlint | Dead. Empty PyPI squat, "AI Agent Observability" |
| whyfail | Dead. Evidence RCA for **Python exceptions** |
| failtrace | Dead. Test-result LLM analysis |
| rag-doctor | Dead. RAG-only RCA |
| agentdx | Dead. Pathology SDK |
| whyran | PyPI 404, but GitHub user `WhyRan` exists; too close to whyfail |
| tracedx | PyPI 404, collides with agentdx |
| rundiag | PyPI 404, forgettable |
| failstep | **Chosen.** PyPI 404. GitHub user 404. GitHub search: 0 repos. Names the failed step. |

Command: `failstep diagnose trace.json`
Package: `failstep`
Repo folder: `failstep`

## Product

Local CLI. One file in. Root cause + evidence + recommendation out.

Not: framework, RAG engine, dashboard, coding agent, SaaS, capture SDK (V1).

## Honesty

No invented confidence, cost, or quality. `Insufficient evidence.` when the file cannot support the claim.

## Stack

Python **3.11+** (not 3.12-only). Users install with **pip**. We develop with **uv**. Hatchling, src layout.

CLI: Typer. Terminal: Rich. Models: Pydantic v2. Tests: pytest. Lint: ruff.

V1 runtime deps: typer, rich, pydantic. See STACK.md.

Doors we keep, deps we do not take yet: OTEL-as-JSON, `failstep[llm]` + httpx in Phase 4, `python -m failstep`.

Not Python 3.12-only: too many conda/company images still on 3.11, and we would lose them for no feature.

## LLM

Detectors first. LLM leftover only, Phase 4, never default, never hardcoded OpenAI, never raw log upload.

## V1 commands

`inspect`, `diagnose`, `version`.

## V1 detectors

FS001 malformed, FS002 schema, FS003 tool failure, FS004 retry, FS005 timeout.

FS005: step `>= 15000ms` error, run `>= 30000ms` error, one step `>= 80%` of run and `>= 5000ms` warning.

Retry loop: same tool + same args, 3+ consecutive tool steps.

Schema errors are not also counted as tool failures. Timeout text is not also counted as tool failure.

## Formats

Native JSON/JSONL. OpenAI messages + LangChain intermediate_steps sniff (Phase 2, shipped). OTEL in Phase 3.

## Report

Three formats, one fact set: terminal, json, markdown. Spec: `OUTPUT.md`.

No confidence, no cost, no grade, no emoji. One root cause. Recommendation is imperative.
JSON field names are a contract (`schema_version: 1`).

## Tests

Pytest from Phase 1. Golden traces + frozen reports. Exit codes 0/1/2/3 asserted.
A finding's evidence must appear in the fixture file. Spec: `TESTING.md`.

CI (Actions, 3.11-3.13, Windows+Ubuntu) is Phase 8. Until then, run pytest on this Windows box before every push.

## Remote

https://github.com/AbdelazizBs/failstep.git

## Next

Phase 2 is done. Freeze. Phase 3 is OTEL JSON ingest, after a real dump has been run through `diagnose`.
