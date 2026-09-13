## failstep 0.1.1
`examples/traces/retry-loop.json` -> `examples/traces/success.json`

### Root cause
old **FS004 retry loop** · new _none_

### Findings
| | |
|---|---|
| gone | FS004 |
| added | none |
| same | none |

### Run
| field | old | new | delta |
|---|---:|---:|---:|
| status | failed | success |  |
| steps | 8 | 4 | -4 |
| duration ms | 14820 | 2100 | -12720 |
| tokens in | 4200 | 800 | -3400 |
| tokens out | 800 | 120 | -680 |
