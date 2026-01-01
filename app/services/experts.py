import time
from hashlib import sha256
from typing import Protocol

from app.providers.base import LLMProvider, ProviderResponse
from app.tools.registry import ToolExecutor


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


class ToolRegistryExpert(BaseExpert):
    name = "tool_calculator"
    cost_per_call = 3
    latency_range = (10, 25)

    def __init__(self, executor: ToolExecutor):
        self.executor = executor
        self.active_role = "user"

    def run(self, prompt: str) -> ExpertResponse:
        # Extract expression after keyword to keep compatibility with previous prompt style
        expr = prompt.replace("calculate", "", 1).strip() or prompt.strip()
        start = time.time()
        result = self.executor.execute(
            tool_name=self.name,
            payload={"expression": expr},
            role=self.active_role,
            intents=["math"] if any(sym in prompt for sym in ["+", "-", "*", "/"]) else ["general"],
        )
        latency_ms = int((time.time() - start) * 1000) + self.latency_range[0]
        if not result.success:
            return ExpertResponse(
                answer="Unable to compute",
                cost=self.cost_per_call,
                latency_ms=latency_ms,
                confidence=0.2,
                metadata={"tool": self.name, "error": result.error},
            )
        return ExpertResponse(
            answer=f"Result: {result.output}",
            cost=self.cost_per_call,
            latency_ms=latency_ms,
            confidence=0.9,
            metadata={"tool": self.name, "result": result.output},
        )


class ProviderExpertLLM(BaseExpert):
    name = "provider_llm"
    cost_per_call = 25
    latency_range = (200, 600)

    def __init__(self, provider: LLMProvider):
        self.provider = provider
        self.name = f"{provider.name}_llm"

    def run(self, prompt: str) -> ExpertResponse:
        start = time.time()
        try:
            result: ProviderResponse = self.provider.generate(prompt)
        except Exception as exc:
            latency_ms = int((time.time() - start) * 1000) + self.latency_range[0]
            return ExpertResponse(
                answer="provider_error",
                cost=self.cost_per_call,
                latency_ms=latency_ms,
                confidence=0.0,
                metadata={"provider": self.provider.name, "error": str(exc)},
            )

        cost_units = max(1, int(result.cost_usd * 1000))
        latency_ms = result.latency_ms
        return ExpertResponse(
            answer=result.text,
            cost=cost_units,
            latency_ms=latency_ms,
            confidence=0.82,
            metadata={
                "provider": self.provider.name,
                "model": result.model,
                "prompt_tokens": result.prompt_tokens,
                "completion_tokens": result.completion_tokens,
                "total_tokens": result.total_tokens,
                "cost_usd": result.cost_usd,
                "raw": result.raw_response,
            },
        )


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
