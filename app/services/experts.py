import time
from hashlib import sha256
from typing import Protocol

from app.services.hf_client import HFClient


class SupportsSearch(Protocol):
    def search(self, query: str) -> list[dict]: ...


class ExpertResponse:
    def __init__(self, answer: str, cost: int, latency_ms: int, confidence: float, metadata: dict):
        self.answer = answer
        self.cost = cost
        self.latency_ms = latency_ms
        self.confidence = confidence
        self.metadata = metadata


class BaseExpert:
    name: str = "base"
    cost_per_call: int = 10
    latency_range: tuple[int, int] = (50, 100)

    def run(self, prompt: str) -> ExpertResponse:
        raise NotImplementedError


class ExpertSmall(BaseExpert):
    name = "expert_small"
    cost_per_call = 5
    latency_range = (40, 80)

    def run(self, prompt: str) -> ExpertResponse:
        start = time.time()
        deterministic = sha256(prompt.encode()).hexdigest()[:12]
        answer = f"SmallExpert processed: {prompt[:100]} [{deterministic}]"
        latency_ms = int((time.time() - start) * 1000) + self.latency_range[0]
        return ExpertResponse(
            answer,
            self.cost_per_call,
            latency_ms,
            0.55,
            {"deterministic": deterministic, "model": "small"},
        )


class ExpertLarge(BaseExpert):
    name = "expert_large"
    cost_per_call = 20
    latency_range = (120, 200)

    def run(self, prompt: str) -> ExpertResponse:
        start = time.time()
        deterministic = sha256(("large" + prompt).encode()).hexdigest()[:16]
        answer = f"LargeExpert deep answer: {prompt[:100]} [{deterministic}]"
        latency_ms = int((time.time() - start) * 1000) + self.latency_range[0]
        return ExpertResponse(
            answer,
            self.cost_per_call,
            latency_ms,
            0.78,
            {"deterministic": deterministic, "model": "large"},
        )


class ToolExpert(BaseExpert):
    name = "tool_calculator"
    cost_per_call = 2
    latency_range = (10, 20)

    def run(self, prompt: str) -> ExpertResponse:
        start = time.time()
        try:
            expr = prompt.replace("calculate", "").strip()
            if any(
                sym in expr
                for sym in ["__", "import", "eval", "exec", "os", "sys", "open", "subprocess"]
            ):
                raise ValueError("unsafe expression")
            result = eval(expr, {"__builtins__": {"abs": abs, "round": round}})
            answer = f"Result: {result}"
            conf = 0.9
        except Exception:
            answer = "Unable to compute"
            conf = 0.2
        latency_ms = int((time.time() - start) * 1000) + self.latency_range[0]
        return ExpertResponse(answer, self.cost_per_call, latency_ms, conf, {"tool": "calculator"})


class RetrieverExpert(BaseExpert):
    name = "retriever"
    cost_per_call = 8
    latency_range = (60, 90)

    def __init__(self, retriever: SupportsSearch):
        self.retriever = retriever

    def run(self, prompt: str) -> ExpertResponse:
        start = time.time()
        docs = self.retriever.search(prompt)
        snippets = "; ".join([d["text"][:80] for d in docs])
        latency_ms = int((time.time() - start) * 1000) + self.latency_range[0]
        return ExpertResponse(snippets, self.cost_per_call, latency_ms, 0.6, {"docs": docs})


class HFExpert(BaseExpert):
    name = "expert_hf"
    cost_per_call = 25
    latency_range = (250, 800)

    def __init__(self, client: HFClient):
        self.client = client

    def run(self, prompt: str) -> ExpertResponse:
        start = time.time()
        try:
            answer, observed_latency_ms, metadata = self.client.generate(prompt)
            latency_ms = max(observed_latency_ms, int((time.time() - start) * 1000))
            metadata["model"] = metadata.get("model") or "hf"
            return ExpertResponse(answer, self.cost_per_call, latency_ms, 0.83, metadata)
        except Exception as exc:
            latency_ms = int((time.time() - start) * 1000)
            return ExpertResponse(
                answer="HF provider unavailable",
                cost=0,
                latency_ms=latency_ms,
                confidence=0.0,
                metadata={"provider": "huggingface", "error": str(exc)[:120]},
            )
