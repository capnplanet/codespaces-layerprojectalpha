from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    query: str
    session_id: Optional[str] = None
    budget_latency_ms: int = Field(default=2000, ge=100)
    budget_cost_units: int = Field(default=500, ge=1)
    role: str = Field(default="user")
    metadata: Dict[str, Any] = Field(default_factory=dict)
