# failstep

A local CLI that diagnoses **why one AI agent run failed**.

Not a dashboard. Not an eval suite. Not a coding-agent linter. Not an LLM wrapper.

```text
pip install failstep
failstep diagnose examples/traces/retry-loop.json
```

No API key. No network. A root cause, quoted evidence, and what to change.

Read this before any implementation:

| Doc | What it is |
|---|---|
| [docs/PRODUCT.md](docs/PRODUCT.md) | What we ship, the +, quality bar |
| [docs/POSITIONING.md](docs/POSITIONING.md) | Exact difference vs lookalikes |
| [docs/STACK.md](docs/STACK.md) | Free open-source stack |
| [docs/PHASES.md](docs/PHASES.md) | Build order. Do not skip. |
| [docs/TRACE_FORMAT.md](docs/TRACE_FORMAT.md) | Native trace contract |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Modules and pipeline |
| [docs/COMPETITORS.md](docs/COMPETITORS.md) | Market scan |
| [docs/DECISIONS.md](docs/DECISIONS.md) | Locked decisions |

**No production code yet.** Phase 0 is documentation. Phase 1 starts only after you approve `docs/PHASES.md`.

## One sentence

Give failstep a trace file. It finds the failed step, proves it from the file, and tells you what to fix.

## License

MIT. See [LICENSE](LICENSE).
