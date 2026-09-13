# Output

The diagnosis **is** the product. If the report is noisy, cute, or vague, the CLI is a toy.

Three formats, one set of facts:

| Format | Who | Flag |
|---|---|---|
| terminal | a human in a shell | `--format terminal` (default) |
| json | CI, scripts, editors | `--format json` |
| markdown | GitHub comments | `--format markdown` |

`--format` is the only switch. No `--pretty`, no `--verbose` in V1. `inspect` is the verbose view of the run. `diagnose` is the verdict. `compare` is counted diffs between two diagnosed runs.

Color: auto. Off when not a TTY, when `NO_COLOR` is set, or when `--format json|markdown`. ASCII only. No emoji. No spinner.

Width: wrap evidence at 88 characters. Do not draw Unicode box art. Use spaces and a blank line. Windows cp1252 must not explode.

## What the eye should hit first

1. The failed step (id + name)
2. The code (`FS004`)
3. Proof
4. What to change

Not a banner. Not a health score. Not five equal "issues."

One **root cause**. Secondary findings after it, shorter.

## Diagnose — terminal

```text
failstep 0.1.0
file     examples/traces/retry-loop.json
run      checkout-agent
status   failed
duration 14820 ms
steps    8

root cause
  FS004  retry loop
  steps  3-5  search_docs

evidence
  identical calls  3
  tool             search_docs
  args             {"query": "refund policy"}
  outputs          unchanged

recommendation
  Cap identical tool retries at 1. Return the first error to the model.

secondary
  none
```

Rules:

- Labels in a left column, 12 characters, lowercase. Values start at column 14.
- Finding id is `FS00x`, then two spaces, then a short title (not a sentence).
- `steps` is an inclusive range when contiguous (`3-5`), else a list (`3, 7`).
- Evidence keys are short nouns. Values are copied or counted. Quote strings that came from the file.
- Recommendation is one or two sentences. Imperative. No "consider", no "it is recommended that".
- `secondary` lists `FSxxx  title  (steps …)` one per line, or `none`.
- A clean run:

```text
failstep 0.1.0
file     examples/traces/success.json
run      checkout-agent
status   success
duration 2100 ms
steps    4

root cause
  none

evidence
  none

recommendation
  none

secondary
  none
```

Exit 0. Do not print "All good!" or a green check.

## Diagnose — JSON

Frozen field names. Versioned. Tests compare this object.

```json
{
  "schema_version": 1,
  "tool": "failstep",
  "tool_version": "0.1.0",
  "file": "examples/traces/retry-loop.json",
  "run": {
    "id": "checkout-agent",
    "status": "failed",
    "duration_ms": 14820,
    "step_count": 8,
    "tokens_in": 4200,
    "tokens_out": 800
  },
  "root_cause": {
    "id": "FS004",
    "detector": "retry",
    "title": "retry loop",
    "severity": "error",
    "step_ids": ["step_3", "step_4", "step_5"],
    "step_indexes": [3, 5],
    "evidence": [
      {"key": "identical_calls", "value": 3},
      {"key": "tool", "value": "search_docs"},
      {"key": "args", "value": {"query": "refund policy"}},
      {"key": "outputs", "value": "unchanged"}
    ],
    "recommendation": "Cap identical tool retries at 1. Return the first error to the model.",
    "source": "deterministic"
  },
  "secondary": [],
  "findings": []
}
```

`findings` is `[root_cause] + secondary` so a script can loop once. `root_cause` is `null` on a clean run.

`step_indexes` is `[first, last]` when contiguous, else the full list. Never 0-based. Step 1 is the first step in the file.

No `confidence`. No `cost_usd`. No `grade`.

Bad input, `--format json`:

```json
{
  "schema_version": 1,
  "tool": "failstep",
  "error": {
    "code": "invalid_input",
    "message": "Not a failstep trace. Expected a JSON object with a steps array. See docs/TRACE_FORMAT.md.",
    "file": "nope.txt"
  }
}
```

Exit 2. Write that JSON to **stdout**. Hints go in `message`, not a second channel.

## Diagnose — markdown

For a PR comment. Same facts, readable in GitHub.

```markdown
## failstep
`examples/traces/retry-loop.json` · run `checkout-agent` · failed · 14820 ms · 8 steps

### Root cause
**FS004 retry loop** on `search_docs` (steps 3-5)

| evidence | |
|---|---|
| identical calls | 3 |
| args | `{"query": "refund policy"}` |
| outputs | unchanged |

**Fix:** Cap identical tool retries at 1. Return the first error to the model.

### Secondary
_none_
```

No HTML. No badge images.

## Compare — terminal

```text
failstep 0.1.0
old          examples/traces/retry-loop.json
new          examples/traces/success.json

root cause
  old  FS004  retry loop
  new  none

findings
  gone   FS004
  added  none
  same   none

run
  status       failed -> success
  steps        8 -> 4  (-4)
  duration ms  14820 -> 2100  (-12720)
  tokens in    4200 -> 800  (-3400)
  tokens out   800 -> 120  (-680)
```

Rules:

- Labels stay 12 characters. Values start at column 14.
- Finding ids only. No evidence dump, no recommendation rewrite, no prose "improved".
- Integer fields print `old -> new  (signed delta)`. Status has no delta.
- A field missing on either side is omitted. Do not invent `0`.
- Identical files: `gone`/`added`/`same`/`run` are `none` except `same` lists ids that exist on both.

JSON field names: `old`, `new`, `diff.findings.{gone,added,same}`, `diff.root_cause.{old,new}`, `diff.run[]` with `key`/`old`/`new`/`delta`.

Exit 1 when any finding id or printed run field changed. Exit 0 when there is no diff.

## Fix — terminal

```text
failstep 0.1.0
file         examples/traces/retry-loop.json
run          checkout-agent

patch
  FS004  retry loop
  steps  3-5  search_docs
  Cap identical tool retries at 1. Return the first error to the model.

also
  none
```

Rules:

- The patch **is** the recommendation. Do not invent source edits, diffs, or extra advice.
- Do not write files. Stdout only.
- `also` lists secondary findings the same way, or `none`.
- A clean run prints `patch` / `also` as `none`. Exit 0. Do not print "All good!".
- JSON field names: `patch`, `also`. `patch` is `null` on a clean run.
- Leftover is never called.

## Inspect — terminal

A table of what happened. No verdict.

Labels are 12 characters, then a space, then the value (column 14).
`type` is 9 characters so `retrieval` fits. Names longer than 16 characters are truncated with `...`.

```text
failstep 0.1.0
file         examples/traces/retry-loop.json
run          checkout-agent
status       failed
duration     14820 ms
steps        8
tokens       4200 in / 800 out

step  type       name              latency  error
   1  llm        plan                210ms
   2  tool       get_customer        120ms
   3  tool       search_docs          80ms
   4  tool       search_docs          80ms
   5  tool       search_docs          80ms
   6  llm        think               350ms
   7  tool       get_order            90ms
   8  llm        answer              400ms
```

Truncate `error` at 40 characters with `...`. Full text is in `--format json` inspect (normalized run) or, later, in diagnose evidence.

Columns are right-aligned for numbers, left for names.

## Errors (all formats)

Speak like a tool, not a chatbot.

| Situation | Message (idea) |
|---|---|
| file missing | `File not found: PATH` |
| empty | `File is empty: PATH` |
| invalid JSON | `Invalid JSON at PATH: <parser error>` |
| unknown shape | `Not a failstep trace. Expected a JSON object with a steps array. See docs/TRACE_FORMAT.md.` |
| internal crash | `Internal error.` (exit 3). JSON: `{"error": {"code": "internal"}}` |

Do not print a Python traceback on user errors. Tracebacks are exit 3 only.

## Voice

- Short titles: `retry loop`, `tool schema`, `malformed output`, `tool failure`, `timeout`, `empty retrieval`, `duplicate chunks`, `conflicting sources`, `leftover`
- Evidence is data, not prose (`identical_calls  3`, not "It appears the agent may have retried")
- Recommendation is a patch in words: what to cap, validate, or stop
- Never "might", "perhaps", "95%", "critical!!!"
- Never blame the user. Blame the step.

This is how we look more serious than agent-debug's essay, and more useful than a Langfuse screenshot.
