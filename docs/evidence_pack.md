# Evidence Pack

- Audit logs: HMAC signed per event.
- Replay: `/v1/replay/{trace_id}` asserts hash equality.
- Evaluation reports: stored JSON in `eval/report_*.json` and persisted in `eval_runs` table.
- Policies: versioned files under `policies/` and `policy_versions` table.
- Metrics: Prometheus scrape `/metrics` for latency and counts.
