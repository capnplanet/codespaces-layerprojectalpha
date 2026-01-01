from typing import Any

from pydantic import BaseModel, Field


class Citation(BaseModel):
    doc_id: str
    chunk_id: str
    quote: str
    hash: str


class PolicyDecision(BaseModel):
    decision: str
    rules_fired: list[str]


class QueryResponse(BaseModel):
    trace_id: str
    status: str
    answer: str | None
    data: Any
    citations: list[Citation]
    reason_codes: list[str]
    confidence: float
    latency_ms: int
    cost_units: int
    policy: PolicyDecision
    replayable: bool


class PolicyValidationRequest(BaseModel):
    policy: dict


class EvalRequest(BaseModel):
    dataset: str = Field(default="demo")
