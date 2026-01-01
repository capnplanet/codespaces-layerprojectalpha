import json
from datetime import datetime
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from app.models.models import EvalRun


def _parse_case(line: str) -> dict[str, Any]:
    try:
        data = json.loads(line)
        if isinstance(data, dict):
            return data
    except Exception:
        pass
    return {"prompt": line, "expects": []}


def _grade(output: str, expects: list[dict[str, Any]]) -> bool:
    if not expects:
        return True
    for rule in expects:
        if "contains" in rule and rule["contains"].lower() not in output.lower():
            return False
        if "not_contains" in rule and rule["not_contains"].lower() in output.lower():
            return False
    return True


def _render_html(report: dict) -> str:
    rows = "".join(
        f"<tr><td>{r['case']}</td><td>{r['passed']}</td><td>{r['latency_ms']}</td><td>{r['cost_units']}</td></tr>"
        for r in report["results"]
    )
    summary = report["summary"]
    return (
        "<html><body>"
        "<h1>Evaluation Report</h1>"
        f"<p>Total: {summary['total']} | Passed: {summary['passed']} | "
        f"Failed: {summary['failed']}</p>"
        "<table border='1'><tr><th>Case</th><th>Passed</th><th>Latency(ms)</th><th>Cost</th></tr>"
        f"{rows}</table>"
        "</body></html>"
    )


def _diff_against_previous(current: dict, history: list[EvalRun]) -> dict[str, Any]:
    if not history:
        return {"regressions": 0, "message": "first run"}
    prev = history[-1].results
    prev_failed = {r["case"] for r in prev.get("results", []) if not r.get("passed")}
    curr_failed = {r["case"] for r in current.get("results", []) if not r.get("passed")}
    regressions = len(curr_failed - prev_failed)
    return {
        "regressions": regressions,
        "message": "regressions detected" if regressions else "no regressions",
    }


def run_eval(db: Session, dataset_path: Path) -> dict:
    with open(dataset_path, encoding="utf-8") as f:
        cases_raw = [line.strip() for line in f if line.strip()]

    cases = [_parse_case(line) for line in cases_raw]
    results = []
    for case in cases:
        prompt = case.get("prompt", "")
        expects = case.get("expects", [])
        # offline deterministic scoring placeholder
        latency_ms = 10 + len(prompt)
        cost_units = 1
        output = prompt  # echo for offline mode
        passed = _grade(output, expects)
        results.append(
            {"case": prompt, "passed": passed, "latency_ms": latency_ms, "cost_units": cost_units}
        )

    summary = {
        "total": len(results),
        "passed": sum(1 for r in results if r["passed"]),
        "failed": sum(1 for r in results if not r["passed"]),
        "timestamp": datetime.utcnow().isoformat(),
        "avg_latency_ms": sum(r["latency_ms"] for r in results) / max(len(results), 1),
        "total_cost_units": sum(r["cost_units"] for r in results),
    }
    report = {"summary": summary, "results": results}

    history = db.query(EvalRun).order_by(EvalRun.created_at).all()
    diff = _diff_against_previous(report, history)
    report["regression"] = diff

    ts = datetime.utcnow().timestamp()
    report_path = Path("eval") / f"report_{ts}.json"
    html_path = Path("eval") / f"report_{ts}.html"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    html_path.write_text(_render_html(report), encoding="utf-8")
    run = EvalRun(dataset=str(dataset_path), results=report, report_path=str(report_path))
    db.add(run)
    db.commit()
    return report
