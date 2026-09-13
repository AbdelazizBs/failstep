## failstep 0.1.1
`examples/traces/retry-loop.json` · run `checkout-agent` · failed · 14820 ms · 8 steps

### Root cause
**FS004 retry loop** on `search_docs` (steps 3-5)

| evidence | |
|---|---|
| identical calls | 3 |
| tool | search_docs |
| args | `{"query": "refund policy"}` |
| outputs | unchanged |

**Fix:** Cap identical tool retries at 1. Return the first error to the model.

### Secondary
_none_
