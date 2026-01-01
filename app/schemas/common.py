from typing import List, Optional, Any
from pydantic import BaseModel, Field


class Citation(BaseModel):
    doc_id: str
    chunk_id: str
    quote: str
    hash: str


class PolicyDecision(BaseModel):
    decision: str
    rules_fired: List[str]


class QueryResponse(BaseModel):
    trace_id: str
    status: str
    answer: Optional[str]
    data: Any
    citations: List[Citation]
    reason_codes: List[str]
    confidence: float
    latency_ms: int
    cost_units: int
    policy: PolicyDecision
    replayable: bool


class PolicyValidationRequest(BaseModel):
    policy: dict


class EvalRequest(BaseModel):
    dataset: str = Field(default="demo")
