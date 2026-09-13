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

Python 3.12, uv, Typer, Rich, Pydantic v2, pytest, ruff. Runtime deps: those three libraries only. See STACK.md.

## LLM

Detectors first. LLM leftover only, Phase 4, never default, never hardcoded OpenAI, never raw log upload.

## V1 commands

`inspect`, `diagnose`, `version`.

## V1 detectors

FS001 malformed, FS002 schema, FS003 tool failure, FS004 retry, FS005 timeout.

## Formats

Native JSON/JSONL now. OpenAI messages + LangChain intermediate_steps sniff in Phase 2. OTEL in Phase 3.

## Next

Read PRODUCT, POSITIONING, PHASES. Approve. Then Phase 1 only.
