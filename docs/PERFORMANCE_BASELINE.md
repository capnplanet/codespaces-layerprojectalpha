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

## Executive Summary (Feynman Style)

Think of this system like a trained operations team handling incoming requests.

- It was consistently fast: almost all requests completed in about one second or less at the slow end (`p95 = 977.229 ms`).
- It was reliable: all 100 requests completed successfully.
- It followed governance rules: zero policy violations.
- It stayed within cost guardrails: average cost was `35.0`, below the threshold of `40`.
- It met the baseline objective: this run passed all gates for safe, steady operation.

Business interpretation:
the platform demonstrated a stable operating mode that is fast enough for interactive use, compliant by default, and economically controlled for routine workloads.

## Engineering Summary (Feynman Style)

Treat this as a controlled cruise test rather than a maximum-stress test.

- Load profile: 100 total requests, concurrency 2, paced at `0.8 req/s`.
- End-to-end outcome: `success=100`, `failed=0`, `refused=0`, `policy_violations=0`.
- Latency shape: `avg=927.532 ms`, `p50=919.968 ms`, `p95=977.229 ms`, `max=1006.925 ms`.
- Capacity at this profile: `throughput=0.802 req/s` (as expected for the selected pacing).
- Cost behavior: `avg=35.0`, `p95=35.0`, `total=3500` cost units.
- Gate evaluation: pass on all configured thresholds (`p95<=2000`, `throughput>=0.5`, `avg_cost<=40`, `violations==0`).

Engineering interpretation:
the current HF-backed path is stable under paced baseline load, with predictable latency and cost characteristics, and no policy regressions in the allowed test profile.

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