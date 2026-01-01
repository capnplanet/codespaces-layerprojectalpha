#!/usr/bin/env bash
set -euo pipefail

trace=$(curl -s -X POST http://localhost:8000/v1/query -H 'Content-Type: application/json' -d '{"query":"Explain routing policy", "session_id":"demo"}' | jq -r '.trace_id')
echo "Trace: $trace"
echo "Replay:" 
curl -s http://localhost:8000/v1/replay/$trace | jq
