# Product

Name: **failstep**
Command: `failstep`
PyPI: `failstep` (404 on 2026-09-13 — available)
GitHub user/org `failstep`: 404. Search: 0 repos.

Tagline:

> A local linter for one failed agent run.

## The job

A developer has a JSON/JSONL dump of an agent execution. The HTTP status was 200. The answer is wrong, the tool looped, or the call was malformed.

They do not want:

- another Langfuse tab
- a 15-class LLM report with 95% confidence
- a research toolkit with recover/rerun/UI
- a hook that blocks Claude Code while they type

They want:

```text
failstep diagnose trace.json
```

and, in under a second, on their laptop, with no key:

1. What failed
2. Which step
3. Evidence copied from the file
4. What to change

That is the whole product for V1.

## The + (what nobody else ships as one small CLI)

Five properties, together. Lookalikes have one or two. Not all five.

### 1. Static analysis of a run file

Like ruff, for traces.

Input is a file that already exists. We do not wrap the agent. We do not install hooks. We do not stand up a collector.

`agentlint` lints **coding-agent actions in real time**.
`failstep` lints **a finished agent run**.

### 2. Detectors are the engine. LLM is optional leftover.

Schema mismatch, retry loop, tool error, timeout, malformed JSON are **code**. They run with `--no-llm` as the default path, not a fallback.

`agent-debug` sends the trace to a model and prints `confidence 95%`.
We never do that.

### 3. Proof contract

Every printed number was counted in the file.

Allowed: `extra_tool_calls: 3`, `duration_ms: 14820`, `tokens_in: 4200` if the field exists.

Forbidden: confidence scores, dollar savings, health grades, "32% token reduction".

If the file cannot support a claim: `Insufficient evidence.`

`whyfail` already owns this honesty for **Python exceptions**. We apply the same contract to **agent traces**. Different input. Same refusal to guess.

### 4. One root cause

Not a taxonomy dump. One primary finding. Secondary issues listed under it.

Ranking is deterministic: severity, then detector order. No model votes.

### 5. CI is a first-class user

```text
failstep diagnose trace.json --format json --fail-on error
```

| Exit | Meaning |
|---|---|
| 0 | nothing at the fail threshold |
| 1 | finding at or above threshold |
| 2 | invalid / unreadable input |
| 3 | internal error |

JSON field names are a contract. Tests freeze them. A silent "healthy" on garbage input is a bug.

## What we will be accused of (and the answer in the README)

| Comment | Our answer, built in |
|---|---|
| "This is Langfuse." | No server, no DB, no UI. File in, report out. |
| "This is agent-debug." | Their default path is an LLM. Ours is detectors. We print no confidence. |
| "This is agentdebugx." | They recover, rerun, and serve a UI. We diagnose one file. |
| "This is agentlint." | They block coding-agent tool calls. We read a trace after the run. |
| "This is whyfail." | They explain Python KeyError from live frames. We explain tool/retry/schema from a dump. |
| "This is AgentInspect." | They are TypeScript inspect trees. We are a Python diagnosis CLI. |
| "Needs OpenAI." | `failstep diagnose` works with no provider. Tests prove it. |
| "Can't parse my dump." | Native schema is V1. OpenAI messages + LangChain `intermediate_steps` sniff in Phase 2. OTEL in Phase 3. Unknown shape = exit 2 with a pointer to TRACE_FORMAT.md. Never pretend success. |
| "Fake metrics." | No confidence field on the Finding model. |
| "Windows mojibake." | ASCII-safe terminal. No required emoji. |
| "Secrets leaked to GPT." | Default path never leaves the machine. LLM path redacts first. |
| "Empty project." | Golden traces + detector tests before any social post. |

## V1 commands

```text
failstep inspect TRACE
failstep diagnose TRACE [--format terminal|json|markdown] [--no-llm] [--fail-on error|warning]
failstep version
```

Not in V1: `explain`, `compare`, `fix`, `serve`, `init`, capture SDK.

## V1 detectors

| ID | Detector | Fires when |
|---|---|---|
| FS001 | MalformedOutput | invalid JSON, truncated tool payload, missing required output fields |
| FS002 | ToolSchema | args miss required keys, extra keys vs schema, type mismatch, explicit validation error text |
| FS003 | ToolFailure | exception, HTTP 4xx/5xx, empty error payload |
| FS004 | RetryLoop | same tool + same args, 3+ times, no meaningful change |
| FS005 | Timeout | step/run over threshold, or one step dominates duration |

Root cause = first `error` in that ID order, else first `warning`.

## Success

A stranger, no account, no key:

```text
pip install failstep
failstep diagnose examples/traces/retry-loop.json
```

sees the retry, the step indexes, the repeated arguments, and "stop retrying identical calls".

If that is not true, we do not launch on LinkedIn.
