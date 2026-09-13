# Competitors

Last checked: 2026-09-13. Positioning (the +) is in POSITIONING.md.

## Observability (store traces)

Langfuse, Phoenix, Opik, LangSmith, Braintrust, Helicone, Agenta.

They answer "what happened across many runs." We do not copy DB/UI/ingestion.

## Eval (score datasets)

Ragas, DeepEval, Promptfoo, AgentEvals.

They answer "is this version better." Not one failed file.

## Same-looking diagnosis tools

| Project | What it is | Why failstep is not it |
|---|---|---|
| [agent-debug](https://pypi.org/project/agent-debug/) | `analyze trace.json`, LLM, 95% confidence | Detectors, no scores, no key |
| [agentdebugx](https://pypi.org/project/agentdebugx/) | Diagnose + attribute + recover + rerun + UI | File in, report out |
| [agent-failure-debugger](https://pypi.org/project/agent-failure-debugger/) | Causal graph library | Tiny CLI, fail loud on bad input |
| [ariadx](https://pypi.org/project/ariadx/) | Taxonomy SDK, heavy ML deps | No LangGraph/xgboost in V1 |
| [agentdx](https://pypi.org/project/agentdx/) | Pathology SDK, no CLI | CLI + CI |
| [agent-triage](https://pypi.org/project/agent-triage/) | Multi-agent batch ranking | Single run |
| [rag-doctor](https://pypi.org/project/rag-doctor/) | RAG RCA | Agent steps first |
| [Phantom](https://github.com/farazfookeer/phantom) | Capture + replay + UI | No capture V1 |
| [AgentInspect](https://github.com/rajudandigam/agent-inspect) | TS local evidence (594★) | Python detectors on a dump |
| [whyfail](https://pypi.org/project/whyfail/) | Evidence RCA for Python exceptions | Agent traces, not live frames |
| [agentlint](https://pypi.org/project/agentlint/) | Real-time coding-agent hooks | Post-run file |
| npm [agentlint](https://www.npmjs.com/package/agentlint) | Scan CLAUDE.md / MCP | Not config |
| npm [agent-doctor](https://www.npmjs.com/package/agent-doctor) | MCP/token health | Name collision only |
| PyPI [agent-doctor](https://pypi.org/project/agent-doctor/) | Traceloop `init()` SDK | Name collision only |
| PyPI [runlint](https://pypi.org/project/runlint/) | Empty 0.0.1 squat | Avoid the name |
| PyPI [failtrace](https://pypi.org/project/failtrace/) | Test-result LLM analysis | Avoid the name |

## Names we will not use

agent-doctor, agentlint, runlint, whyfail, rag-doctor, agentdx, failtrace, whyran.

## Remaining wedge (keep all six)

1. One local file in. Diagnosis out. No capture SDK in V1.
2. Deterministic detectors first. Zero API key.
3. LLM only as leftover semantic fallback.
4. No invented confidence or cost.
5. Python CLI (AgentInspect owns TS; agentdebugx owns the kitchen sink).
6. OTEL GenAI as ingest adapter, not the product.

If we cannot keep those six, we should not build this.
