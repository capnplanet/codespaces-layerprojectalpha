# darpaa-moe-intermediary-layer

Offline-first, DARPA-style MoE intermediary layer with FastAPI, Postgres, Redis, Celery, OpenTelemetry, Prometheus, Grafana, and policy-as-code.

Design notes: offline-first, zero-trust defaults, FIPS-friendly crypto (SHA-256 HMAC), cloud-agnostic via Docker Compose, reproducible builds via pinned Python version and container image, rate limiting via SlowAPI, RBAC on sensitive endpoints, hybrid retrieval (BM25 + dense fallback), Grafana dashboards provisioned, SLSA provenance workflow.

## 📘 Documentation

**NEW:** Comprehensive documentation now available:

👉 **[EXECUTIVE_SUMMARY.md](docs/EXECUTIVE_SUMMARY.md)** - Feynman-style guide covering:
- High-level architecture and purpose
- Detailed algorithmic function locations and explanations
- Cross-domain applications (defense, aerospace, biopharma, commercial)
- LLM integration strategies and implementation guides
- Security model, scaling recommendations, and extensibility

👉 **[ALGORITHM_REFERENCE.md](docs/ALGORITHM_REFERENCE.md)** - Technical reference for all algorithms:
- Complete algorithm descriptions with complexity analysis
- Performance benchmarks and tuning parameters
- Extensibility points and customization examples

👉 **[LLM_INTEGRATION.md](docs/LLM_INTEGRATION.md)** - Step-by-step LLM integration guide:
- Cloud API integration (OpenAI, Anthropic, Google)
- Self-hosted models (Llama, Mistral via vLLM/Ollama)
- Advanced use cases (RAG, Chain-of-Thought, Multi-Agent Debate)
- Production deployment checklist

## Quickstart (Codespaces or local)
1. `make install`
2. `make migrate`
3. `make up` (starts API, worker, db, redis, otel, prometheus, grafana)

API runs on http://localhost:8000.

## Demo
- Query: `curl -X POST http://localhost:8000/v1/query -H 'Content-Type: application/json' -d '{"query":"Explain routing policy", "session_id":"s1"}'`
- Replay: `curl http://localhost:8000/v1/replay/<trace_id>`
- Audit: `curl http://localhost:8000/v1/audit/<trace_id>`
- Eval (admin): `curl -X POST http://localhost:8000/v1/eval/run -H 'Authorization: Bearer <token>' -H 'Content-Type: application/json' -d '{"dataset":"demo"}'`
- Go variant: `go run ./go` then `curl -X POST http://localhost:9000/v1/query -d '{"query":"test"}'`

## Make targets
- `make format` – black + ruff fix
- `make lint` – ruff + black check
- `make typecheck` – mypy
- `make test` – pytest
- `make sbom` – CycloneDX SBOM (satisfies SBOM requirement; pair with SLSA provenance in CI pipelines)

## Observability
- Prometheus scrape `/metrics`
- Grafana auto-provisioned (see grafana/provisioning)
- OpenTelemetry exporter to otel-collector (compose)

## Algorithmic behaviors (current)
- Router: budget-aware scoring (cost/latency) with math-mandatory override, fallbacks tracked in `reason_codes`.
- Retrieval: chunked BM25 + optional dense rerank, hash dedup, top-k = 5 with per-chunk scores.
- Expert fusion: confidence-weighted merge with slight preference for `expert_large`; calculator guarded against unsafe expressions.
- Policy: intent classification + role allow/deny + on-disk hot reload of YAML policies.
- Eval: JSONL-style cases with `prompt` and `expects` assertions (contains/not_contains), regression diff vs previous run, HTML/JSON reports under `eval/`.
- Memory: Redis-backed session lists capped to 50 with 24h TTL, simple summary helper for compact recalls.

## Access control & safety
- Rate limiting via SlowAPI middleware
- RBAC: admin-only for audit, eval, policy validation (Bearer token optional; falls back to payload role)
- Policy enforcement with allowed/restricted tools and intents

## Security and determinism
- HMAC-signed audit logs
- Policy enforcement before execution
- Deterministic hash stored for replay
- RBAC-ready via JWT roles

## Go variant
A Go implementation with mirrored endpoints lives in `go/` (minimal parity for defense alignment).
