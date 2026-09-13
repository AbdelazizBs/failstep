# Testing

We do not ship a phase because it "looks done." We ship it when a command fails if we broke it.

No detector, parser, or report change lands without a test that would have caught the bug.

## What we are proving

Three things, always:

1. **The file is read honestly.** Garbage in = exit 2. Never "healthy."
2. **The diagnosis is earned.** Finding IDs, step indexes, and numbers come from the file.
3. **The report is stable.** A developer and a CI job see the same facts. Terminal layout can get richer; JSON field names cannot thrash.

If a PR cannot name which of those it protects, it is not ready.

## Layout

```text
examples/traces/          product demos (README)
tests/
  traces/                 hard fixtures (openai, langchain, jsonl, traps)
  test_parser.py
  test_inspect.py
  test_cli_exit.py
  test_diagnose.py
  test_sniff.py
  test_honesty.py
  test_detectors/
  goldens/
    inspect-retry-loop.terminal.txt
    inspect-retry-loop.json
    retry-loop.terminal.txt
    retry-loop.json
    retry-loop.md
    success.terminal.txt
    multi-failure.terminal.txt
    multi-failure.json
    multi-failure.md
    timeout-missing-duration.json
```

`examples/traces/` is the product demo. `tests/traces/` can be ugly. Do not put secrets in either.

Locked detector IDs:

```text
Detector | Fires on | Silent on | False-positive protection | Evidence required
FS001    | truncated/invalid JSON, missing output fields | success, prose, JSON in a sentence, wrong output types when keys exist | does not parse prose as JSON | reason, output sample from the step
FS002    | missing/extra/wrong-type/null required args, validation error text | no schema and no error text, valid args | does not invent required keys | expected required / received keys from the step
FS003    | HTTP 4xx/5xx, empty error payload | schema errors, timeout text, success | recovered run still names the failed step | step error / http status copied
FS004    | 3+ consecutive identical tool+args | 2 repeats, changed args, LLM between repeats | does not collapse similar queries | identical calls counted, args copied
FS005    | step >=15000ms, timeout text, run >=30000ms, 80% dominate warning | healthy latencies | missing duration stays null, multiple timeouts keep the slowest | latency_ms / run_duration_ms from the file
```

Phase 5 owns empty retrieval and duplicate chunks. Those fixtures must stay silent today.

## Layers

### 1. Unit

Parser, models, one detector at a time.

A detector test is three cases:

- **fires** on the matching fixture, with the expected `id`, `step_ids`, and evidence keys
- **silent** on `success.json`
- **does not invent** a field that is missing in the file

No mocks of the trace. Pass a real `Run` object built from a fixture.

### 2. Golden reports

For each example trace, freeze:

- JSON report (`tests/goldens/<name>.json`)
- terminal stdout (`tests/goldens/<name>.terminal.txt`)
- markdown (`tests/goldens/<name>.md`) once diagnose exists

CLI test: run the command, compare. A change to wording is a golden update in the same PR, with a reason.

JSON is compared as parsed objects (key order does not matter). Terminal is compared as text (whitespace at EOL stripped, nothing else).

### 3. CLI / exit codes

Use Typer's `CliRunner`. Assert stdout **and** `exit_code`.

| Case | Exit |
|---|---|
| missing file | 2 |
| empty file | 2 |
| `{not json` | 2 |
| unknown shape | 2 |
| valid success, no findings | 0 |
| valid, finding at `--fail-on` | 1 |
| internal crash | 3 (tests force this with a hook, not by hoping) |

`--format json` on a bad file still prints a small JSON error object, not a traceback. Tracebacks are for exit 3.

### 4. Hands on this machine

Windows first. After the test suite is green:

```text
python -m failstep inspect examples/traces/retry-loop.json
python -m failstep diagnose examples/traces/retry-loop.json
python -m failstep diagnose examples/traces/retry-loop.json --format json
```

Look at it. If a column wraps into garbage at 80 characters, the golden is wrong.

No emoji. No color when stdout is not a TTY (`NO_COLOR` / non-tty). Tests run non-tty, so goldens are uncolored.

## Phase gates

Do not start the next phase until the gate command is green.

### Phase 1 (done)

Installable inspect CLI.

### Phase 2 (done)

```text
python -m pytest
python -m failstep diagnose examples/traces/retry-loop.json --format json
```

Every FS001-FS005 example fires the right id. `success.json` is empty findings, exit 0.

Trap fixtures in `tests/traces/` (schema-traps, retry-silent, multi-failure, timeout-missing-duration, retrieval-silent) are green. Keep them green.

### Phase 3

OTEL JSON ingest. New fixture in `tests/traces/` plus a diagnose golden. If the mapping drops a tool error, that is a failed test, not a "known limit" in the README.

### Phase 4

LLM tests use a fake HTTP endpoint (stdlib `http.server` or a tiny fixture). No real API key in CI. Redaction test: a fixture with `sk-` / `Bearer` must not appear in the payload the fake server received.

### Phase 8

GitHub Actions: pytest + ruff on 3.11, 3.12, 3.13. Windows + Ubuntu. That is when "it works on my machine" stops being an argument.

Until then, **you** run pytest on this Windows box before every push.

## Commands we always run before a push

```text
python -m ruff check .
python -m pytest
```

Same with `uv run` if that is how you installed.

No coverage theater. We do not chase 100%. We chase: parser, five detectors, three report formats, four exit codes.

## What a detector PR must include

1. A fixture under `examples/traces/` or `tests/traces/`
2. The finding id and evidence keys in the test
3. Updated goldens if terminal/JSON changed
4. A line in the PR: "silent on success.json"

## What we will not do

- Snapshot the whole Rich render tree
- Call a real LLM in tests
- Mark a flaky detector as `xfail` and ship it
- Assert on wall-clock duration of the CLI
- Hide a failed parse behind a default empty `Run`

## Honesty checks (automated)

A small test walks every `Finding` in goldens:

- no key named `confidence`
- no `$` in recommendation unless the fixture has a cost field (it will not, in V1)
- every `step_ids` entry exists on the `Run`
- every evidence string is either a counted field (`identical_calls=3`) or a substring of the fixture file

That last one is the proof contract, in pytest.
