# failstep

A local CLI that diagnoses **why one AI agent run failed**.

Not a dashboard. Not an eval suite. Not a coding-agent linter. Not an LLM wrapper.

```text
pip install failstep
failstep diagnose examples/traces/retry-loop.json
```

No API key. No network. A root cause, quoted evidence, and what to change.

Repo: [github.com/AbdelazizBs/failstep](https://github.com/AbdelazizBs/failstep)

**Phase 1 is in this repo:** `inspect` works. `diagnose` parses the file and refuses to invent a finding until Phase 2 detectors ship.

## 60 seconds

From a clone (Python 3.11+):

```text
pip install -e ".[dev]"
python -m failstep inspect examples/traces/retry-loop.json
```

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
   2  tool       get_customer        120ms  customer_id is required
   3  tool       search_docs          80ms
   4  tool       search_docs          80ms
   5  tool       search_docs          80ms
   6  llm        think               350ms
   7  tool       get_customer        110ms  customer_id is required
   8  llm        answer              400ms
```

If `failstep` is not on PATH:

```text
python -m failstep inspect examples/traces/retry-loop.json
python -m failstep version
```

`diagnose` in Phase 1:

```text
python -m failstep diagnose examples/traces/retry-loop.json
```

```text
No detectors shipped yet. Use inspect, or wait for Phase 2.
```

Garbage input exits `2`. It never prints healthy.

## Commands

```text
failstep inspect TRACE [--format terminal|json|markdown]
failstep diagnose TRACE [--format terminal|json|markdown]
failstep version
```

Native JSON and JSONL only. Contract: [docs/TRACE_FORMAT.md](docs/TRACE_FORMAT.md).
How the report must look: [docs/OUTPUT.md](docs/OUTPUT.md).

## Tests

```text
python -m pytest tests/test_parser.py tests/test_inspect.py tests/test_cli_exit.py
python -m ruff check .
```

If you use uv: `uv sync --extra dev` then `uv run pytest` / `uv run ruff check .`.

## Design

| Doc | What it is |
|---|---|
| [docs/PRODUCT.md](docs/PRODUCT.md) | What we ship, the +, quality bar |
| [docs/POSITIONING.md](docs/POSITIONING.md) | Exact difference vs lookalikes |
| [docs/STACK.md](docs/STACK.md) | Free open-source stack |
| [docs/OUTPUT.md](docs/OUTPUT.md) | How the diagnosis looks (terminal / JSON / markdown) |
| [docs/TESTING.md](docs/TESTING.md) | How each phase is proven |
| [docs/PHASES.md](docs/PHASES.md) | Build order. Do not skip. |
| [docs/TRACE_FORMAT.md](docs/TRACE_FORMAT.md) | Native trace contract |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Modules and pipeline |
| [docs/COMPETITORS.md](docs/COMPETITORS.md) | Market scan |
| [docs/DECISIONS.md](docs/DECISIONS.md) | Locked decisions |

## License

MIT. See [LICENSE](LICENSE).
