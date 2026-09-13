# Contributing

## Setup

Python 3.11 or newer.

```text
pip install -e ".[dev]"
```

`uv sync --extra dev` is optional.

## Checks

```text
python -m pytest
python -m ruff check .
```

Run those before every pull request.

## Pull requests

- One change. Update goldens in the same PR if output changed.
- A detector must fire on a fixture, stay silent on `examples/traces/success.json`, and copy evidence from the file.
- Do not add `confidence`, cost, or health scores.
- Do not call a real LLM in tests.
- Unknown trace shape is exit 2, never a silent empty run.

Trace contract: `docs/TRACE_FORMAT.md`.
Report contract: `docs/OUTPUT.md`.
Test contract: `docs/TESTING.md`.

## Local data

Do not commit virtualenvs, recordings, or personal traces. Put those in `local/`, `media/`, or a `*-venv/` directory. They are gitignored and excluded from the sdist.

Redact secrets (`sk-`, `Bearer`, customer emails) before pasting a dump into an issue.

## Release

Version lives in `pyproject.toml` and `src/failstep/__init__.py`. Keep them equal. Add a `CHANGELOG.md` entry.

GitHub Actions publishes to PyPI on a GitHub Release. That needs a `pypi` environment on the repo and a trusted publisher on PyPI. Do not put a PyPI token in the repository.
