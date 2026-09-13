## failstep 0.1.0
`tests/traces/multi-failure.json` · run `support-agent` · success · 18500 ms · 25 steps

### Root cause
**FS001 malformed output** on `draft` (steps 16)

| evidence | |
|---|---|
| steps | 1 |
| reason | truncated json |
| output | {"answer": "refunds are |
| tool | draft |

**Fix:** Return complete JSON from the tool. Do not truncate the payload.

### Secondary
- **FS002 tool schema** (steps 3, 4, 6, get_customer)
- **FS003 tool failure** (steps 18, notify_billing)
- **FS004 retry loop** (steps 13-15, search_docs)
- **FS005 timeout** (steps 8)
