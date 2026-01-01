import random
import time
from typing import Dict, Tuple, List
from hashlib import sha256

class ExpertResponse:
    def __init__(self, answer: str, cost: int, latency_ms: int, confidence: float, metadata: Dict):
        self.answer = answer
        self.cost = cost
        self.latency_ms = latency_ms
        self.confidence = confidence
        self.metadata = metadata


class BaseExpert:
    name: str = "base"
    cost_per_call: int = 10
    latency_range: Tuple[int, int] = (50, 100)

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
        return ExpertResponse(answer, self.cost_per_call, latency_ms, 0.55, {"deterministic": deterministic})


class ExpertLarge(BaseExpert):
    name = "expert_large"
    cost_per_call = 20
    latency_range = (120, 200)

    def run(self, prompt: str) -> ExpertResponse:
        start = time.time()
        deterministic = sha256(("large" + prompt).encode()).hexdigest()[:16]
        answer = f"LargeExpert deep answer: {prompt[:100]} [{deterministic}]"
        latency_ms = int((time.time() - start) * 1000) + self.latency_range[0]
        return ExpertResponse(answer, self.cost_per_call, latency_ms, 0.78, {"deterministic": deterministic})


class ToolExpert(BaseExpert):
    name = "tool_calculator"
    cost_per_call = 2
    latency_range = (10, 20)

    def run(self, prompt: str) -> ExpertResponse:
        start = time.time()
        try:
            expr = prompt.replace("calculate", "").strip()
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

    def __init__(self, retriever: "Retriever"):
        self.retriever = retriever

    def run(self, prompt: str) -> ExpertResponse:
        start = time.time()
        docs = self.retriever.search(prompt)
        snippets = "; ".join([d["text"][:80] for d in docs])
        latency_ms = int((time.time() - start) * 1000) + self.latency_range[0]
        return ExpertResponse(snippets, self.cost_per_call, latency_ms, 0.6, {"docs": docs})


class Retriever:
    def __init__(self, index: List[Dict]):
        self.index = index

    def search(self, query: str) -> List[Dict]:
        scored = []
        for doc in self.index:
            score = query.lower().count(doc["title"].lower()) + random.random() * 0.01
            scored.append((score, doc))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [d for _, d in scored[:3]]
