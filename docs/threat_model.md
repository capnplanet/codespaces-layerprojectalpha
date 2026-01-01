# Threat Model

## Scope
Intermediary layer handling user queries, routing to experts, applying policies, and persisting audits.

## Assumptions
- Zero-trust: all inputs are untrusted.
- Offline-first: no internet dependency required.
- FIPS-friendly crypto: SHA-256 HMAC via `cryptography`/stdlib.
- Cloud-agnostic deployment via Docker.

## Assets
- User queries and session memory.
- Audit logs and trace records.
- Policy definitions.

## Threats
- Injection in prompts or tool expressions.
- Unauthorized tool use.
- Audit log tampering.
- Data exfiltration via retrieval.

## Controls
- Policy-as-code enforcement before execution.
- HMAC-signed audit entries.
- RBAC via token role claims.
- Rate limiting via Redis (slowapi ready hook).
- Structured outputs with hashes for replay.
- Minimal exposure of secrets via env vars.
