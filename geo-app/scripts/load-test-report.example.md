# Load Test Results Template

## Test Configuration
- Tool: k6
- Date: YYYY-MM-DD
- Duration: 2.5 minutes
- Max VUs: 100

## Results
| Metric | Value | Threshold | Status |
|--------|-------|-----------|--------|
| P50 Latency | ms | <500ms | |
| P95 Latency | ms | <2000ms | |
| P99 Latency | ms | <5000ms | |
| RPS (peak) | req/s | >50 | |
| Error Rate | % | <5% | |

## Run Command
```
k6 run --env API_URL=http://localhost:8000 scripts/load-test.js
```
