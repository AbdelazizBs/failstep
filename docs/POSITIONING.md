# Positioning

Same-looking tools. Different job. This file is the difference, line by line.

## Map of the space

```text
store traces          Langfuse, Phoenix, Opik, LangSmith, Braintrust
score a dataset       Ragas, DeepEval, Promptfoo
block coding agents   agentlint (PyPI), npm agentlint, AgentDoctor config scanners
explain Python crash  whyfail
LLM-explain a trace   agent-debug
research kitchen sink agentdebugx, ariadx, agent-failure-debugger
inspect TS trees      AgentInspect
RAG-only RCA          rag-doctor
name squat            runlint 0.0.1 empty wheel
                      PyPI agent-doctor (Traceloop init SDK)

failstep              lint ONE finished agent run from a file,
                      with detectors, proof, and CI exit codes
```

## Direct clones (same sentence, different product)

### agent-debug (`pip install agent-debug`)

Same sentence: diagnose why the agent failed from `trace.json`.

| | agent-debug | failstep |
|---|---|---|
| Engine | LLM classifier, 15 subcategories | 5 deterministic detectors |
| Default | needs Anthropic/OpenAI/DeepSeek/Ollama | no provider |
| Numbers | `confidence 95%`, severity 3/5 | counted fields only |
| Capture | decorator / patch / context manager | none in V1 (file you already have) |
| Runtime | ~15s, billed | milliseconds, free |
| Stack | Typer + Rich + Pydantic + anthropic | Typer + Rich + Pydantic, no vendor SDK |

Their GitHub Action comments a model essay on the PR. Ours fails CI on `FS004` with JSON.

### agentdebugx

Same verb: `agentdebug diagnose trace.json`. They even have a heuristic mode without an LLM.

They also: attribute, recover, rerun, HTTP runner, FastAPI UI, Error Hub, Claude/Codex plugins, GUI RCA.

We stop at diagnose + inspect. If we add recover/rerun/UI we become a worse AgentDebugX.

### agentdx

Same idea: pathologies on a JSON trace (tool thrashing, instruction drift).

SDK. No real CLI. Synthetic eval. Planned ML and LLM-as-judge.

We are a CLI a stranger can run in 60 seconds, with exit codes.

### AgentInspect (594 stars)

Local-first, evidence, CI. Winning product in **TypeScript**.

They build execution trees and trajectory contracts. We build **root-cause detectors on a dump**, in Python, for people who already export JSON from LangGraph/PydanticAI/custom agents.

Do not rewrite AgentInspect in Python. Do not add a web tree viewer in V1.

### agentlint (PyPI v2.5.5) and npm `agentlint`

The word "lint" is taken for **coding-agent guardrails** (secrets, force-push, MCP config).

failstep does not lint CLAUDE.md. It lints a **run**.

Never brand as "the eslint of agents". That sentence is already used. Say "a linter for a failed run file".

### whyfail

Closest **honesty** product. Evidence-based RCA, local, "insufficient evidence", redaction.

Domain: live Python exceptions (`KeyError`, `IndexError`). Not agent traces.

We copy the contract (do not guess). We do not copy the name, the engine, or the input.

### rag-doctor

Deterministic RCA, no API key. Domain: query + docs + answer. Not tool steps.

RAG detectors are Phase 5, after the agent CLI is real.

### PyPI `agent-doctor` / npm `agent-doctor`

Name is dead. Instrumentation SDK and MCP health scanner. Unrelated. Do not fight them.

## What we tell developers

> Langfuse shows the span tree. failstep tells you the failed step.
>
> agent-debug asks a model. failstep reads the file.
>
> agentlint watches Claude Code. failstep watches the trace you already exported.
