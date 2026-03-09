# Performance Baseline (HF End-to-End)

This document defines and records the performance baseline for the MoE intermediary layer when using a Hugging Face endpoint via Codespaces secrets.

## Scope

- Endpoint under test: `/v1/query`
- Provider mode: `LLM_PROVIDER=hf`
- Secrets used: `HF_TOKEN`, `HF_ENDPOINT_URL`
- Profile type: baseline (paced, policy-compliant)

## Run Configuration

- Command:

```bash
make perf-assert
```

- Effective benchmark arguments:

```bash
python scripts/perf_baseline.py \
  --api-url http://localhost:8000 \
  --requests 100 \
  --concurrency 2 \
  --requests-per-second 0.8 \
  --role admin \
  --max-p95-latency-ms 2000 \
  --min-throughput-rps 0.5 \
  --max-avg-cost-units 40 \
  --require-policy-compliance
```

## KPI Definitions

- `p95 latency`: 95th percentile client-observed request latency in milliseconds.
- `throughput`: total completed requests divided by wall-clock run duration.
- `avg cost units/request`: average of `cost_units` returned by `/v1/query`.
- `policy compliance`: zero denied/refused responses in the allowed benchmark profile.

## Current Baseline Result (2026-03-09)

- Requests: `100`
- Concurrency: `2`
- Pace: `0.8 req/s`
- Role: `admin`

Measured values:

- Success: `100/100`
- Failed: `0/100`
- Average latency: `927.532 ms`
- p50 latency: `919.968 ms`
- p95 latency: `977.229 ms`
- Max latency: `1006.925 ms`
- Throughput: `0.802 req/s`
- Avg cost units/request: `35.0`
- p95 cost units/request: `35.0`
- Total cost units: `3500`
- Policy violations: `0`
- KPI pass: `true`

Report artifact:

- `eval/perf_baseline_1773070302.json`

## Thresholds (Default Baseline Gate)

- `p95 latency <= 2000 ms`
- `throughput >= 0.5 req/s`
- `avg cost units/request <= 40`
- `policy violations == 0`

These defaults are intended for Codespaces/dev-container baseline characterization and should be tightened for production-grade environments.

## How To Reproduce

1. Export provider and endpoint variables:

```bash
export LLM_PROVIDER=hf
export HF_TOKEN=<secret>
export HF_ENDPOINT_URL=<endpoint>
```

2. Start API runtime.
3. Run `make perf-baseline` for a non-gated report.
4. Run `make perf-assert` for pass/fail KPI evaluation.

## Notes

- Benchmark load is intentionally paced to remain within API rate limits.
- Policy-compliant prompts are used so failures represent system behavior, not intentional policy denials.
- In this baseline, cost is driven by selected experts and reflected in response `cost_units`.