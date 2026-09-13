# Stack

Everything here is free for us and for users. MIT/Apache/BSD dependencies only. No paid SaaS required to run or to develop.

## Runtime

| Piece | Choice | Why | Cost |
|---|---|---|---|
| Language | Python 3.12+ | AI-dev default, your language, typing | free |
| Package manager | [uv](https://github.com/astral-sh/uv) | Fast, lockfile, Apache-2.0 | free |
| CLI | [Typer](https://github.com/fastapi/typer) MIT | `failstep diagnose` with `--help` | free |
| Terminal | [Rich](https://github.com/Textualize/rich) MIT | Tables, readable reports, Windows-safe | free |
| Models | [Pydantic v2](https://github.com/pydantic/pydantic) MIT | Trace + Finding + Report | free |
| Tests | pytest MIT | Detectors and CLI | free |
| Lint/format | [Ruff](https://github.com/astral-sh/ruff) MIT | One tool | free |
| Types | mypy (dev extra) | Optional, not a religion | free |
| License | MIT | Same as the rest of this stack | free |

Python stdlib does JSON, JSONL, regex redaction, pathlib. Do not add a library for those.

## Optional later (still free)

| Piece | When | Notes |
|---|---|---|
| Ollama | Phase 4 semantic leftover | Local model, no key. User installs it. We do not bundle weights. |
| OpenAI-compatible HTTP | Phase 4 | User brings endpoint. No hardcoded OpenAI. `httpx` only if needed. |
| OpenTelemetry JSON parse | Phase 3 | Parse exported JSON. Do **not** depend on `opentelemetry-sdk` unless parsing requires it. |

## Forbidden in V1 (and not "free" in practice)

Postgres, Redis, ClickHouse, Kafka, FastAPI, React, Docker-required, Kubernetes, AWS, LangChain as a runtime dep, sentence-transformers, anthropic/openai SDKs, any telemetry.

"Free" also means the **user** pays nothing and sends nothing by default.

## Dev machine

```text
uv sync --extra dev
uv run pytest
uv run ruff check .
uv run failstep diagnose examples/traces/retry-loop.json
```

No Docker. No cloud account. CI on GitHub Actions (free for public OSS) in Phase 8, not Phase 1.

## Distribution

- GitHub public repo, MIT
- PyPI when Phase 2 is actually useful
- `pip install failstep` / `uv pip install failstep`

No npm package. This is Python.

## Dependency budget

V1 runtime deps: **typer, rich, pydantic**. That's it.

If a PR adds a fourth runtime dep, it needs a sentence in DECISIONS.md.
