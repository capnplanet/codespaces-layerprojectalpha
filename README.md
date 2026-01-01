# darpaa-moe-intermediary-layer

Offline-first, DARPA-style MoE intermediary layer with FastAPI, Postgres, Redis, Celery, OpenTelemetry, Prometheus, and policy-as-code.

Design notes: offline-first, zero-trust defaults, FIPS-friendly crypto (SHA-256 HMAC), cloud-agnostic via Docker Compose, reproducible builds via pinned Python version and container image.

## Quickstart (Codespaces or local)
1. `make install`
2. `make migrate`
3. `make up` (starts API, worker, db, redis, otel, prometheus, grafana)

API runs on http://localhost:8000.

## Demo
- Query: `curl -X POST http://localhost:8000/v1/query -H 'Content-Type: application/json' -d '{"query":"Explain routing policy", "session_id":"s1"}'`
- Replay: `curl http://localhost:8000/v1/replay/<trace_id>`
- Audit: `curl http://localhost:8000/v1/audit/<trace_id>`
- Eval: `curl -X POST http://localhost:8000/v1/eval/run -H 'Content-Type: application/json' -d '{"dataset":"demo"}'`
- Go variant: `go run ./go` then `curl -X POST http://localhost:9000/v1/query -d '{"query":"test"}'`

## Make targets
- `make format` – black + ruff fix
- `make lint` – ruff + black check
- `make typecheck` – mypy
- `make test` – pytest
- `make sbom` – CycloneDX SBOM (satisfies SBOM requirement; pair with SLSA provenance in CI pipelines)

## Security and determinism
- HMAC-signed audit logs
- Policy enforcement before execution
- Deterministic hash stored for replay
- RBAC-ready via JWT roles

## Go variant
A Go implementation with mirrored endpoints lives in `go/` (minimal parity for defense alignment).
