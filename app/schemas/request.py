from typing import Any

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    query: str
    session_id: str | None = None
    budget_latency_ms: int = Field(default=2000, ge=100)
    budget_cost_units: int = Field(default=500, ge=1)
    role: str = Field(default="user")
    metadata: dict[str, Any] = Field(default_factory=dict)
