import json
import time
import uuid
from functools import lru_cache
from hashlib import sha256
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.models import Trace
from app.observability.metrics import REQUEST_COUNT, REQUEST_LATENCY
from app.schemas.common import Citation
from app.services.audit import AuditService
from app.services.experts import ExpertResponse, HFExpert, RetrieverExpert
from app.services.hf_client import HFClient
from app.services.memory import MemoryService
from app.services.policy import PolicyDecision, PolicyEngine
from app.services.retrieval import HybridRetriever
from app.services.router import build_router

settings = get_settings()


def canonical_json(data: dict[str, Any]) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"))


def compute_hash(payload: dict[str, Any]) -> str:
    return sha256(canonical_json(payload).encode()).hexdigest()


@lru_cache
def build_retriever() -> RetrieverExpert:
    corpus_path = Path("data/docs")
    retriever = HybridRetriever.load_from_path(corpus_path)
    return RetrieverExpert(retriever)


@lru_cache
def build_hf_expert() -> HFExpert | None:
    provider = settings.llm_provider.strip().lower()
    if provider not in {"hf", "huggingface"}:
        return None
    client = HFClient(
        endpoint_url=settings.hf_endpoint_url,
        token=settings.hf_token,
        timeout_ms=settings.hf_timeout_ms,
        max_retries=settings.hf_max_retries,
        model=settings.hf_model,
    )
    if not client.is_configured():
        return None
    return HFExpert(client)


class Orchestrator:
    def __init__(
        self, db: Session, policy_engine: PolicyEngine, audit: AuditService, memory: MemoryService
    ):
        self.db = db
        self.policy_engine = policy_engine
        self.audit = audit
        self.memory = memory
        retriever = build_retriever()
        hf_expert = build_hf_expert()
        self.router = build_router(retriever, hf_expert)
        self.experts = self.router.experts

    def handle_query(
        self, query: str, session_id: str, budget_latency_ms: int, budget_cost_units: int, role: str
    ) -> dict[str, Any]:
        start = time.time()
        REQUEST_COUNT.labels("/v1/query", "started").inc()
        normalized = query.strip()
        classification = {
            "intent": "general" if "policy" not in query else "policy",
            "confidence": 0.6,
        }
        router_decision = self.router.plan(query, budget_latency_ms, budget_cost_units)

        policy_decision: PolicyDecision = self.policy_engine.evaluate(
            role, query, router_decision.chosen
        )
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

        expert_outputs: list[ExpertResponse] = []
        cost_accum = 0
        citations: list[Citation] = []
        reason_codes = list(router_decision.reason_codes)
        if router_decision.fallbacks:
            reason_codes.append("fallback:" + ",".join(router_decision.fallbacks))
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

        combined_answer, confidence = self._fuse_answers(expert_outputs)
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

    def _fuse_answers(self, outputs: list[ExpertResponse]) -> tuple[str, float]:
        if not outputs:
            return "No answer", 0.0
        # weighted by confidence; prefer larger model when close
        weights = []
        for o in outputs:
            w = max(o.confidence, 0.05)
            if o.metadata.get("model") == "large":
                w *= 1.1
            weights.append(w)
        total_w = sum(weights) or 1.0
        pieces = []
        agg_conf = 0.0
        for o, w in zip(outputs, weights, strict=False):
            pieces.append(o.answer)
            agg_conf += o.confidence * (w / total_w)
        fused_answer = " | ".join(pieces)
        return fused_answer, round(agg_conf, 3)

    def _pack_response(
        self,
        trace_id: str,
        status: str,
        answer: Any,
        data: Any,
        citations: list[Citation],
        reason_codes: list[str],
        confidence: float,
        latency_ms: int,
        cost_units: int,
        policy: PolicyDecision,
        replayable: bool,
    ) -> dict[str, Any]:
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
