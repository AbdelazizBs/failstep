## failstep 0.1.2
`examples/traces/retry-loop.json` · run `checkout-agent`

### Patch
**FS004 retry loop** on `search_docs` (steps 3-5)

Cap identical tool retries at 1. Return the first error to the model.

### Also
_none_
