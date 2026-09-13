# failstep

A local CLI that diagnoses **why one AI agent run failed**.

Not a dashboard. Not an eval suite. Not a coding-agent linter. Not an LLM wrapper.

Python 3.11+. No API key. No network. A root cause, quoted evidence, and what to change.

```text
pip install failstep
failstep version
failstep diagnose TRACE.json
```

`TRACE.json` is a finished run you already have. The wheel does not ship example files.

If an older version is already installed:

```text
pip install -U failstep
```

To try the bundled retry dump:

```text
git clone https://github.com/AbdelazizBs/failstep.git
cd failstep
pip install failstep
failstep diagnose examples/traces/retry-loop.json
```

Repo: [github.com/AbdelazizBs/failstep](https://github.com/AbdelazizBs/failstep)

[![CI](https://github.com/AbdelazizBs/failstep/actions/workflows/ci.yml/badge.svg)](https://github.com/AbdelazizBs/failstep/actions/workflows/ci.yml)

`inspect` prints the run. `diagnose` names the failed step. `compare` counts diffs. `fix` prints the recommendation.

## 60 seconds

From a clone, for contributors (Python 3.11+):

```text
pip install -e ".[dev]"
python -m failstep diagnose examples/traces/retry-loop.json
```

```text
failstep 0.1.2
file         examples/traces/retry-loop.json
run          checkout-agent
status       failed
duration     14820 ms
steps        8

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

Exit `1` when there is a finding (`--fail-on error`, the default). A clean run exits `0`. Garbage input exits `2`. It never prints healthy.

If `failstep` is not on PATH:

```text
python -m failstep diagnose examples/traces/retry-loop.json
python -m failstep inspect examples/traces/retry-loop.json
python -m failstep version
```

```text
failstep inspect TRACE [--format terminal|json|markdown]
failstep diagnose TRACE [--format terminal|json|markdown] [--fail-on error|warning] [--no-llm] [--no-redact]
failstep compare OLD NEW [--format terminal|json|markdown]
failstep fix TRACE [--format terminal|json|markdown]
failstep version
```

Native JSON and JSONL. Also OpenAI `messages` + `tool_calls`, LangChain `intermediate_steps`, and exported OpenTelemetry GenAI JSON (`resourceSpans` or `{spans: [...]}`). Contract: [docs/TRACE_FORMAT.md](docs/TRACE_FORMAT.md).
How the report must look: [docs/OUTPUT.md](docs/OUTPUT.md).

Detectors: FS001 malformed output, FS002 tool schema, FS003 tool failure, FS004 retry loop, FS005 timeout, FS006 empty retrieval, FS007 duplicate chunks, FS008 conflicting sources. Optional leftover (`FS000`) only if `FAILSTEP_LLM_URL` is set, httpx is installed (`pip install failstep[llm]`), and no error finding exists. `--no-llm` skips it. Secrets are redacted before the request.

## Tests

```text
python -m pytest
python -m ruff check .
```

If you use uv: `uv sync --extra dev` then `uv run pytest` / `uv run ruff check .`.

## Design

| Doc | What it is |
|---|---|
| [docs/PRODUCT.md](docs/PRODUCT.md) | What we ship, quality bar |
| [docs/STACK.md](docs/STACK.md) | Free open-source stack |
| [docs/OUTPUT.md](docs/OUTPUT.md) | How the diagnosis looks (terminal / JSON / markdown) |
| [docs/TESTING.md](docs/TESTING.md) | How each phase is proven |
| [docs/PHASES.md](docs/PHASES.md) | Build order. Do not skip. |
| [docs/TRACE_FORMAT.md](docs/TRACE_FORMAT.md) | Native trace contract |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Modules and pipeline |
| [docs/DECISIONS.md](docs/DECISIONS.md) | Locked decisions |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Setup, tests, pull requests |
| [CHANGELOG.md](CHANGELOG.md) | Shipped versions |

Unknown shape exits `2`. Open an issue with the command, exit code, and redacted stdout. Do not paste API keys.

## License

MIT. See [LICENSE](LICENSE).
