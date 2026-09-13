# Product

Name: **failstep**
Command: `failstep`
PyPI: `failstep`
Requires: Python 3.11+, `pip install failstep`
GitHub: [AbdelazizBs/failstep](https://github.com/AbdelazizBs/failstep)

Tagline:

> A local CLI that diagnoses why one AI agent run failed.

## The job

A developer has a JSON or JSONL dump of one agent run. The HTTP status was 200. The answer is still wrong, a tool looped, or a call was malformed.

They run:

```text
failstep diagnose trace.json
```

and, in under a second, on their laptop, with no API key, they get:

1. What failed
2. Which step
3. Evidence copied from the file
4. What to change

That is the whole product for V1.

## What V1 is

- A local CLI. One finished run file in. A diagnosis out.
- Deterministic detectors on the default path. No API key required.
- Optional leftover (`FS000`) only when `FAILSTEP_LLM_URL` is set and no error finding exists.
- Proof from the file. No confidence scores, dollar savings, or health grades.
- One root cause. Secondary issues listed under it.
- CI exit codes that stay stable.

| Exit | Meaning |
|---|---|
| 0 | nothing at the fail threshold |
| 1 | finding at or above threshold |
| 2 | invalid or unreadable input |
| 3 | internal error |

Garbage input never prints healthy. JSON field names are a contract. Tests freeze them.

## What V1 is not

- A dashboard, database, or hosted service
- A capture SDK or a live wrapper around the agent
- An eval suite over a dataset
- A hook that blocks coding-agent tools while someone types
- A recover, rerun, or self-heal toolkit

## Proof contract

Every printed number was counted in the file.

Allowed: `extra_tool_calls: 3`, `duration_ms: 14820`, `tokens_in: 4200` if the field exists.

Forbidden: confidence scores, dollar savings, health grades, invented percentages.

If the file cannot support a claim: `Insufficient evidence.`

## V1 commands

```text
failstep inspect TRACE
failstep diagnose TRACE [--format terminal|json|markdown] [--no-llm] [--no-redact] [--fail-on error|warning]
failstep compare OLD NEW [--format terminal|json|markdown]
failstep fix TRACE [--format terminal|json|markdown]
failstep version
```

Not in V1: `explain`, `serve`, `init`, capture SDK.

## V1 detectors

| ID | Detector | Fires when |
|---|---|---|
| FS001 | MalformedOutput | invalid JSON, truncated tool payload, missing required output fields |
| FS002 | ToolSchema | args miss required keys, extra keys vs schema, type mismatch, explicit validation error text |
| FS003 | ToolFailure | exception, HTTP 4xx/5xx, empty error payload |
| FS004 | RetryLoop | same tool + same args, 3+ times, no meaningful change |
| FS005 | Timeout | step/run over threshold, or one step dominates duration |
| FS006 | EmptyRetrieval | retrieval step returned zero documents |
| FS007 | DuplicateChunks | same chunk id or source+text twice in one retrieval step |
| FS008 | ConflictingSources | two documents in one step disagree on a shared scalar field |
| FS000 | leftover | opt-in only: no error finding, `FAILSTEP_LLM_URL` set, warning |

Root cause = first `error` in that ID order, else first `warning`. FS000 cannot replace FS001–FS008.

## Success

A stranger, no account, no key:

```text
pip install failstep
failstep diagnose examples/traces/retry-loop.json
```

sees the retry, the step indexes, the repeated arguments, and "stop retrying identical calls".

If that is not true, V1 is not ready.
