# Audit Specification

- Every request produces audit events with HMAC signatures.
- Stored fields: input, normalized input, classification, routing, retrieval, tool calls, output, policy results, cost, latency, timestamps, replayable flag.
- Immutable design: hashes stored and verified during replay.
- Retrieval artifacts stored with hashes for provenance.
- Access: `/v1/audit/{trace_id}` returns stored trace for forensics.
