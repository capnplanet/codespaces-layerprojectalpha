from __future__ import annotations

import argparse
import asyncio
import json
import random
import statistics
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx


@dataclass
class QueryResult:
    ok: bool
    latency_ms: float
    cost_units: int
    policy_decision: str
    status: str


def _build_payload(prompt: str, role: str, idx: int) -> dict[str, Any]:
    return {
        "query": prompt,
        "session_id": f"perf-{idx % 20}",
        "budget_latency_ms": 2000,
        "budget_cost_units": 500,
        "role": role,
        "metadata": {"source": "perf_baseline"},
    }


def _prompts() -> list[str]:
    return [
        "Explain the intermediary layer in simple terms.",
        "Summarize how expert fusion combines responses.",
        "calculate 12 * 7 + 3",
        "Describe how replay verifies deterministic outputs.",
        "Outline how query routing balances cost and latency.",
        "What diagnostics are included in query traces?",
        "Explain retrieval citations and relevance ranking.",
        "calculate round(10 / 3, 2)",
    ]


async def _one_request(
    client: httpx.AsyncClient,
    sem: asyncio.Semaphore,
    api_url: str,
    role: str,
    idx: int,
    delay_s: float,
) -> QueryResult:
    if delay_s > 0:
        await asyncio.sleep(delay_s)
    prompt = random.choice(_prompts())
    payload = _build_payload(prompt, role, idx)
    start = time.perf_counter()
    async with sem:
        try:
            resp = await client.post(f"{api_url}/v1/query", json=payload)
            elapsed_ms = (time.perf_counter() - start) * 1000
            if resp.status_code == 429:
                return QueryResult(False, elapsed_ms, 0, "allow", "rate_limited")
            if resp.status_code != 200:
                return QueryResult(False, elapsed_ms, 0, "error", "http_error")
            body = resp.json()
            policy = body.get("policy") or {}
            return QueryResult(
                ok=body.get("status") == "success",
                latency_ms=elapsed_ms,
                cost_units=int(body.get("cost_units") or 0),
                policy_decision=str(policy.get("decision") or "unknown"),
                status=str(body.get("status") or "unknown"),
            )
        except Exception:
            elapsed_ms = (time.perf_counter() - start) * 1000
            return QueryResult(False, elapsed_ms, 0, "error", "exception")


def _percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    k = (len(ordered) - 1) * p
    lo = int(k)
    hi = min(lo + 1, len(ordered) - 1)
    frac = k - lo
    return ordered[lo] * (1 - frac) + ordered[hi] * frac


def _assert_kpis(
    summary: dict[str, Any],
    max_p95_latency_ms: int | None,
    min_throughput_rps: float | None,
    max_avg_cost_units: float | None,
    require_policy_compliance: bool,
) -> tuple[bool, list[str]]:
    failures: list[str] = []
    if max_p95_latency_ms is not None and summary["latency"]["p95_ms"] > max_p95_latency_ms:
        failures.append(
            f"p95 latency {summary['latency']['p95_ms']:.2f}ms exceeds {max_p95_latency_ms}ms"
        )
    if min_throughput_rps is not None and summary["throughput_rps"] < min_throughput_rps:
        failures.append(f"throughput {summary['throughput_rps']:.3f} below {min_throughput_rps}")
    if max_avg_cost_units is not None and summary["cost_units"]["avg"] > max_avg_cost_units:
        failures.append(f"avg cost {summary['cost_units']['avg']:.2f} exceeds {max_avg_cost_units}")
    if require_policy_compliance and summary["policy"]["violations"] > 0:
        failures.append(f"policy compliance violations detected: {summary['policy']['violations']}")
    return len(failures) == 0, failures


async def run(args: argparse.Namespace) -> int:
    random.seed(42)
    started = time.perf_counter()
    sem = asyncio.Semaphore(args.concurrency)
    timeout = httpx.Timeout(args.timeout_seconds)

    async with httpx.AsyncClient(timeout=timeout) as client:
        tasks = [
            _one_request(
                client,
                sem,
                args.api_url.rstrip("/"),
                args.role,
                i,
                (i / args.requests_per_second) if args.requests_per_second > 0 else 0.0,
            )
            for i in range(args.requests)
        ]
        results = await asyncio.gather(*tasks)

    elapsed_s = max(time.perf_counter() - started, 1e-6)
    latencies = [r.latency_ms for r in results]
    costs = [r.cost_units for r in results]
    successes = [r for r in results if r.ok]
    policy_violations = [r for r in results if r.policy_decision == "deny" or r.status == "refused"]

    summary = {
        "run": {
            "timestamp": datetime.now(UTC).isoformat(),
            "api_url": args.api_url,
            "requests": args.requests,
            "concurrency": args.concurrency,
            "role": args.role,
            "duration_seconds": round(elapsed_s, 3),
        },
        "counts": {
            "success": len(successes),
            "failed": len(results) - len(successes),
        },
        "latency": {
            "avg_ms": round(statistics.fmean(latencies) if latencies else 0.0, 3),
            "p50_ms": round(_percentile(latencies, 0.50), 3),
            "p95_ms": round(_percentile(latencies, 0.95), 3),
            "max_ms": round(max(latencies) if latencies else 0.0, 3),
        },
        "throughput_rps": round(len(results) / elapsed_s, 3),
        "cost_units": {
            "avg": round(statistics.fmean(costs) if costs else 0.0, 3),
            "p95": round(_percentile([float(c) for c in costs], 0.95), 3),
            "total": int(sum(costs)),
        },
        "policy": {
            "violations": len(policy_violations),
        },
        "status_distribution": {
            "success": sum(1 for r in results if r.status == "success"),
            "refused": sum(1 for r in results if r.status == "refused"),
            "rate_limited": sum(1 for r in results if r.status == "rate_limited"),
            "http_error": sum(1 for r in results if r.status == "http_error"),
            "exception": sum(1 for r in results if r.status == "exception"),
        },
    }

    report_dir = Path("eval")
    report_dir.mkdir(parents=True, exist_ok=True)
    stamp = str(int(time.time()))
    report_path = report_dir / f"perf_baseline_{stamp}.json"

    kpi_ok, failures = _assert_kpis(
        summary,
        max_p95_latency_ms=args.max_p95_latency_ms,
        min_throughput_rps=args.min_throughput_rps,
        max_avg_cost_units=args.max_avg_cost_units,
        require_policy_compliance=args.require_policy_compliance,
    )
    summary["kpi"] = {"pass": kpi_ok, "failures": failures}

    report_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(json.dumps(summary, indent=2))
    print(f"Report written to: {report_path}")

    return 0 if kpi_ok else 2


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run baseline E2E performance test against /v1/query"
    )
    parser.add_argument("--api-url", default="http://localhost:8000")
    parser.add_argument("--requests", type=int, default=100)
    parser.add_argument("--concurrency", type=int, default=5)
    parser.add_argument("--timeout-seconds", type=float, default=30.0)
    parser.add_argument("--requests-per-second", type=float, default=0.8)
    parser.add_argument("--role", default="user")
    parser.add_argument("--max-p95-latency-ms", type=int, default=None)
    parser.add_argument("--min-throughput-rps", type=float, default=None)
    parser.add_argument("--max-avg-cost-units", type=float, default=None)
    parser.add_argument("--require-policy-compliance", action="store_true")
    return parser.parse_args()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(run(parse_args())))
