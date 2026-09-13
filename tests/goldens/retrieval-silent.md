## failstep 0.1.2
`tests/traces/retrieval-silent.json` · run `retrieval-silent` · success · 400 ms · 3 steps

### Root cause
**FS006 empty retrieval** on `search_docs` (steps 1)

| evidence | |
|---|---|
| tool | search_docs |
| steps | 1 |
| hits | 0 |
| chunks | 0 |
| query | refund policy |

**Fix:** Do not answer from an empty retrieval. Retry the query or tell the user nothing was found.

### Secondary
- **FS007 duplicate chunks** (steps 2, search_docs)
