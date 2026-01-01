import json
import time
import uuid
from typing import Dict, Any, List
from hashlib import sha256
from pathlib import Path
from sqlalchemy.orm import Session
from app.services.experts import BaseExpert, RetrieverExpert, ExpertResponse
from app.services.router import build_router, choose_experts, RouterDecision
from app.services.policy import PolicyEngine, PolicyDecision
from app.services.audit import AuditService
from app.services.memory import MemoryService
from app.services.retrieval import HybridRetriever
from app.schemas.common import Citation
from app.core.security import sign_hmac
from app.core.config import get_settings
from app.models.models import Trace
from app.observability.metrics import REQUEST_COUNT, REQUEST_LATENCY

settings = get_settings()


def canonical_json(data: Dict[str, Any]) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"))


def compute_hash(payload: Dict[str, Any]) -> str:
    return sha256(canonical_json(payload).encode()).hexdigest()


def build_retriever() -> RetrieverExpert:
    corpus_path = Path("data/docs")
    retriever = HybridRetriever.load_from_path(corpus_path)
    return RetrieverExpert(retriever)


class Orchestrator:
    def __init__(self, db: Session, policy_engine: PolicyEngine, audit: AuditService, memory: MemoryService):
        self.db = db
        self.policy_engine = policy_engine
        self.audit = audit
        self.memory = memory
        retriever = build_retriever()
        self.experts, self.router_decision = build_router(retriever)

    def handle_query(self, query: str, session_id: str, budget_latency_ms: int, budget_cost_units: int, role: str) -> Dict[str, Any]:
        start = time.time()
        REQUEST_COUNT.labels("/v1/query", "started").inc()
        normalized = query.strip()
        classification = {"intent": "general" if "policy" not in query else "policy", "confidence": 0.6}
        router_decision = choose_experts(query, budget_latency_ms, budget_cost_units, self.experts)

        policy_decision: PolicyDecision = self.policy_engine.evaluate(role, query, router_decision.chosen)
        if policy_decision.decision == "deny":
            payload = self._pack_response(
                trace_id=str(uuid.uuid4()),
                status="refused",
                answer=None,
                data={},
                citations=[],
                reason_codes=["policy-deny"] + policy_decision.rules_fired,
                confidence=0.0,
                latency_ms=int((time.time() - start) * 1000),
                cost_units=0,
                policy=policy_decision,
                replayable=False,
            )
            self.audit.log_event(payload["trace_id"], "policy_refusal", payload)
            REQUEST_COUNT.labels("/v1/query", "refused").inc()
            return payload

        expert_outputs: List[ExpertResponse] = []
        cost_accum = 0
        citations: List[Citation] = []
        reason_codes = router_decision.reason_codes
        for expert in self.experts:
            if expert.name not in router_decision.chosen:
                continue
            if cost_accum + expert.cost_per_call > budget_cost_units:
                reason_codes.append("budget-exceeded")
                continue
            result = expert.run(query)
            cost_accum += result.cost
            if expert.name == "retriever" and isinstance(result.metadata.get("docs"), list):
                for doc in result.metadata["docs"]:
                    citations.append(
                        Citation(
                            doc_id=doc.get("id", "unknown"),
                            chunk_id="0",
                            quote=doc.get("text", "")[:100],
                            hash=compute_hash(doc),
                        )
                    )
            expert_outputs.append(result)

        combined_answer = " | ".join([o.answer for o in expert_outputs]) if expert_outputs else "No answer"
        confidence = max([o.confidence for o in expert_outputs], default=0.0)
        latency_ms = int((time.time() - start) * 1000)
        trace_id = str(uuid.uuid4())
        output_payload = {
            "answer": combined_answer,
            "details": [o.metadata for o in expert_outputs],
        }
        response_payload = self._pack_response(
            trace_id=trace_id,
            status="success",
            answer=combined_answer,
            data=output_payload,
            citations=citations,
            reason_codes=reason_codes,
            confidence=confidence,
            latency_ms=latency_ms,
            cost_units=cost_accum,
            policy=policy_decision,
            replayable=True,
        )

        trace = Trace(
            trace_id=trace_id,
            input={"query": query},
            normalized_input={"query": normalized},
            classification=classification,
            routing={"chosen": router_decision.chosen},
            retrieval={"citations": [c.model_dump() for c in citations]},
            tool_calls={"experts": [e.metadata for e in expert_outputs]},
            output=response_payload,
            output_hash=compute_hash(response_payload),
            policy=policy_decision.model_dump(),
            cost_units=cost_accum,
            latency_ms=latency_ms,
            replayable=True,
        )
        self.db.add(trace)
        self.db.commit()
        self.db.refresh(trace)

        self.audit.log_event(trace_id, "completed", response_payload)
        self.memory.store(session_id, "assistant", combined_answer)
        REQUEST_COUNT.labels("/v1/query", "success").inc()
        REQUEST_LATENCY.labels("/v1/query").observe(latency_ms)
        return response_payload

    def _pack_response(
        self,
        trace_id: str,
        status: str,
        answer: Any,
        data: Any,
        citations: List[Citation],
        reason_codes: List[str],
        confidence: float,
        latency_ms: int,
        cost_units: int,
        policy: PolicyDecision,
        replayable: bool,
    ) -> Dict[str, Any]:
        return {
            "trace_id": trace_id,
            "status": status,
            "answer": answer,
            "data": data,
            "citations": [c.model_dump() for c in citations],
            "reason_codes": reason_codes,
            "confidence": round(confidence, 3),
            "latency_ms": latency_ms,
            "cost_units": cost_units,
            "policy": policy.model_dump(),
            "replayable": replayable,
        }
