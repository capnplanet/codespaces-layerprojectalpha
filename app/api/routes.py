import json
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session
from pathlib import Path
from app.core.database import get_db
from app.core.config import get_settings
from app.services.policy import PolicyEngine
from app.services.audit import AuditService
from app.services.memory import MemoryService
from app.services.orchestrator import Orchestrator, compute_hash
from app.services.eval import run_eval
from app.schemas.request import QueryRequest
from app.schemas.common import QueryResponse, PolicyValidationRequest, EvalRequest
from app.models.models import Trace

router = APIRouter()
settings = get_settings()


def build_services(db: Session):
    policy_engine = PolicyEngine(Path("policies"))
    audit = AuditService(db)
    memory = MemoryService(db)
    orchestrator = Orchestrator(db, policy_engine, audit, memory)
    return orchestrator, policy_engine, audit


@router.get("/healthz", response_class=PlainTextResponse)
def healthz():
    return "ok"


@router.get("/readyz", response_class=PlainTextResponse)
def readyz():
    return "ready"


@router.post("/v1/query", response_model=QueryResponse)
def query(payload: QueryRequest, db: Session = Depends(get_db)):
    orchestrator, policy_engine, _ = build_services(db)
    response = orchestrator.handle_query(
        query=payload.query,
        session_id=payload.session_id or "anon",
        budget_latency_ms=min(payload.budget_latency_ms, settings.max_latency_ms),
        budget_cost_units=min(payload.budget_cost_units, settings.max_cost_units),
        role=payload.role,
    )
    return response


@router.get("/v1/replay/{trace_id}", response_model=QueryResponse)
def replay(trace_id: str, db: Session = Depends(get_db)):
    trace = db.query(Trace).filter(Trace.trace_id == trace_id).first()
    if not trace or not trace.replayable:
        raise HTTPException(status_code=404, detail="Trace not found or not replayable")
    current_hash = compute_hash(trace.output)
    if current_hash != trace.output_hash:
        raise HTTPException(status_code=409, detail="Replay hash mismatch")
    return trace.output


@router.get("/v1/audit/{trace_id}")
def audit(trace_id: str, db: Session = Depends(get_db)):
    return db.query(Trace).filter(Trace.trace_id == trace_id).first()


@router.post("/v1/policy/validate")
def validate_policy(request: PolicyValidationRequest):
    engine = PolicyEngine(Path("policies"))
    decision = engine.evaluate("admin", json.dumps(request.policy), [])
    return decision.model_dump()


@router.post("/v1/eval/run")
def eval_run(request: EvalRequest, db: Session = Depends(get_db)):
    dataset_path = Path("eval/datasets") / f"{request.dataset}.txt"
    if not dataset_path.exists():
        raise HTTPException(status_code=404, detail="Dataset not found")
    return run_eval(db, dataset_path)
