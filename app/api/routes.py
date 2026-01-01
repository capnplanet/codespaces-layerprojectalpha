import json
from pathlib import Path

from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.core.security import decode_token
from app.models.models import Trace
from app.schemas.common import EvalRequest, PolicyValidationRequest, QueryResponse
from app.schemas.request import QueryRequest
from app.services.audit import AuditService
from app.services.eval import run_eval
from app.services.memory import MemoryService
from app.services.orchestrator import Orchestrator, compute_hash
from app.services.policy import PolicyEngine

router = APIRouter()
settings = get_settings()


def build_services(db: Session):
    policy_engine = PolicyEngine(Path("policies"))
    audit = AuditService(db)
    memory = MemoryService(db)
    orchestrator = Orchestrator(db, policy_engine, audit, memory)
    return orchestrator, policy_engine, audit


def resolve_role(payload_role: str, authorization: str | None) -> str:
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1]
        try:
            _, role = decode_token(token)
            return role or payload_role
        except Exception:
            return payload_role
    return payload_role


@router.get("/healthz", response_class=PlainTextResponse)
def healthz():
    return "ok"


@router.get("/readyz", response_class=PlainTextResponse)
def readyz():
    return "ready"


@router.post("/v1/query", response_model=QueryResponse)
def query(
    payload: QueryRequest,
    db: Session = Depends(get_db),  # noqa: B008
    authorization: str | None = Header(default=None),
):
    orchestrator, policy_engine, _ = build_services(db)
    role = resolve_role(payload.role, authorization)
    response = orchestrator.handle_query(
        query=payload.query,
        session_id=payload.session_id or "anon",
        budget_latency_ms=min(payload.budget_latency_ms, settings.max_latency_ms),
        budget_cost_units=min(payload.budget_cost_units, settings.max_cost_units),
        role=role,
    )
    return response


@router.get("/v1/replay/{trace_id}", response_model=QueryResponse)
def replay(trace_id: str, db: Session = Depends(get_db)):  # noqa: B008
    trace = db.query(Trace).filter(Trace.trace_id == trace_id).first()
    if not trace or not trace.replayable:
        raise HTTPException(status_code=404, detail="Trace not found or not replayable")
    current_hash = compute_hash(trace.output)
    if current_hash != trace.output_hash:
        raise HTTPException(status_code=409, detail="Replay hash mismatch")
    return trace.output


@router.get("/v1/audit/{trace_id}")
def audit(
    trace_id: str,
    db: Session = Depends(get_db),  # noqa: B008
    authorization: str | None = Header(default=None),
):
    role = resolve_role("user", authorization)
    if role != "admin":
        raise HTTPException(status_code=403, detail="forbidden")
    return db.query(Trace).filter(Trace.trace_id == trace_id).first()


@router.post("/v1/policy/validate")
def validate_policy(
    request: PolicyValidationRequest, authorization: str | None = Header(default=None)
):
    role = resolve_role("user", authorization)
    if role != "admin":
        raise HTTPException(status_code=403, detail="forbidden")
    engine = PolicyEngine(Path("policies"))
    decision = engine.evaluate("admin", json.dumps(request.policy), [])
    return decision.model_dump()


@router.post("/v1/eval/run")
def eval_run(
    request: EvalRequest,
    db: Session = Depends(get_db),  # noqa: B008
    authorization: str | None = Header(default=None),
):
    role = resolve_role("user", authorization)
    if role != "admin":
        raise HTTPException(status_code=403, detail="forbidden")
    dataset_path = Path("eval/datasets") / f"{request.dataset}.txt"
    if not dataset_path.exists():
        raise HTTPException(status_code=404, detail="Dataset not found")
    return run_eval(db, dataset_path)
