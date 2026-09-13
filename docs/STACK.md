# Stack

Rule: a stranger installs with pip, runs one command, gets a diagnosis. No Docker, no account, no Node, no API key.

Everything is MIT/Apache/BSD. The user pays nothing. The default path never sends a byte.

## What developers actually type

```text
pip install failstep
failstep diagnose trace.json
```

That has to work on Windows, macOS, and Linux. `uv pip install failstep` is extra, not required.

Also: `python -m failstep diagnose trace.json` for people whose PATH did not get the script.

## Locked choices

| Piece | Choice | Why this, not the "fancier" option |
|---|---|---|
| Language | **Python 3.11+** | Agent traces come from LangGraph, PydanticAI, LlamaIndex, CrewAI. Those people already have Python. AgentInspect owns TypeScript. We do not split. |
| User install | **pip / PyPI** | If it is not `pip install`, most of them will not try it. |
| Maintainer | **uv** | Fast lockfile for us. Users never need uv. |
| Package layout | **src/failstep**, hatchling | Standard. pip, uv, and GitHub Actions all eat `pyproject.toml`. |
| CLI | **Typer** | `--help` for free. Click is older. argparse is too bare. |
| Terminal | **Rich** | Tables on Windows without a TUI. Textual would be an app to learn. We are not an app. |
| Models | **Pydantic v2** | Untrusted JSON in. Strict Run/Step/Finding out. dataclasses would leak garbage through. |
| Tests | **pytest** | Detectors live or die on fixtures. |
| Lint | **Ruff** | One tool. Not flake8+black+isort. |
| License | **MIT** | Companies can use it. |
| CI (Phase 8) | **GitHub Actions** | Free for public OSS. pytest + ruff. |

V1 runtime deps: **typer, rich, pydantic**. Stop.

A fourth runtime dep needs a sentence in `DECISIONS.md`.

Stdlib does JSON, JSONL, pathlib, regex redaction. Do not add a library for those.

## Why Python, not Rust / Go / TypeScript

| Temptation | Why it blocks *use* |
|---|---|
| TypeScript CLI | AgentInspect already won that crowd. Python people will not `npm i -g`. |
| Rust / Go binary | Faster, worse for us: no one hacks a detector in a language they do not write agents in. PRs die. |
| Dual Python + TS | We become two products. |

Best stack is the one a LangGraph author can clone and patch before lunch.

## Python 3.11, not 3.12-only

3.12 is nicer. 3.11 is what a lot of conda and company images still run.

3.11 gives us `tomllib` and the typing we need. We do not need 3.12.

Test in CI later on 3.11, 3.12, 3.13. Never require 3.13.

## Will this block us later?

No, if we leave doors and refuse product-shaped dependencies.

| Later need | Door we already have | Trap |
|---|---|---|
| OpenAI / LangChain dumps | Parser adapters, Phase 2 | LangChain as a runtime dep |
| OTEL GenAI | Parse exported JSON, Phase 3 | `opentelemetry-sdk`, a collector, a server |
| Semantic leftover | `failstep[llm]` extra with **httpx** only, Phase 4 | `openai` / `anthropic` SDKs |
| Local model | Ollama HTTP, user installs it | Bundled weights |
| Huge traces | Load whole file in V1 (normal dumps are small). Stream later (`ijson`) if a real file OOM | Rewrite in Rust |
| MCP so Claude can call us | stdio entry in the same Python package | A second Node service |
| GitHub Action | `failstep diagnose --format json --fail-on error` | A hosted app |
| Windows PATH pain | `python -m failstep` | "Install WSL" |
| Tool-arg schema (FS002) | Tiny required-keys + types checker | `jsonschema` until a fixture proves we need it |

We can add extras. We cannot add a database and still claim we are a linter.

## Optional extras (not V1)

```text
failstep          # diagnose, no network
failstep[llm]     # leftover: httpx + FAILSTEP_LLM_URL
```

No `failstep[otel-sdk]`. Exported JSON is enough.

## Forbidden (they make the tool heavier than the problem)

Postgres, Redis, FastAPI, React, Docker-required, Kubernetes, AWS, LangChain, sentence-transformers, OpenAI/Anthropic SDKs, telemetry, a TUI, a web tree viewer.

"Free" also means the **user** sends nothing by default.

## Dev machine (us)

```text
uv sync --extra dev
uv run pytest
uv run ruff check .
uv run failstep inspect examples/traces/retry-loop.json
```

No Docker. No cloud account.

## What "simple" means in the CLI

- Zero config file for V1
- One positional path
- Flags: `--format`, `--fail-on`, `--no-llm`, `--no-redact`
- `compare` takes two paths. No leftover. Counted diffs only.
- Garbage input: exit 2, point at `docs/TRACE_FORMAT.md`
- ASCII-safe terminal (this machine is Windows)
- JSON field names frozen by tests

If a developer needs a tutorial after `failstep --help`, we failed.
