# Changelog

## Unreleased

- Drop competitor comparison docs. Product docs describe failstep only.
- Ignore local venvs, recordings, and private traces so they stay off git and PyPI.

## 0.1.0

- `inspect`, `diagnose`, `compare`, `fix`, `version`
- Detectors FS001–FS008 (malformed, schema, tool failure, retry, timeout, empty retrieval, duplicate chunks, conflicting sources)
- Native JSON/JSONL, OpenAI messages, LangChain `intermediate_steps`, exported OpenTelemetry GenAI JSON
- Optional leftover LLM (`FS000`) only when `FAILSTEP_LLM_URL` is set and no error finding exists
- `compare` counts finding-id and run-field diffs
- `fix` prints the recommendation as a patch and does not write files
- Exit codes 0/1/2/3
