from __future__ import annotations

import math
import time
from dataclasses import dataclass
from typing import Any, Protocol

try:  # optional dependency for accurate token accounting
    import tiktoken  # type: ignore
except Exception:  # pragma: no cover - optional
    tiktoken = None


class ProviderError(RuntimeError):
    """Raised when a provider call fails."""


@dataclass
class ProviderConfig:
    api_key: str
    base_url: str
    model: str
    temperature: float = 0.0
    max_tokens: int = 512


@dataclass
class ProviderResponse:
    text: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost_usd: float
    model: str
    latency_ms: int
    raw_response: dict[str, Any]


class LLMProvider(Protocol):
    name: str

    def generate(
        self, prompt: str, tools: list[dict[str, Any]] | None = None
    ) -> ProviderResponse: ...


_DEF_ENCODING = "cl100k_base"


def _estimate_tokens_with_tiktoken(prompt: str, model: str) -> int:
    if tiktoken is None:  # pragma: no cover - optional dependency not present
        return 0
    try:
        enc = tiktoken.encoding_for_model(model)
    except Exception:  # pragma: no cover - fallback when model unknown
        enc = tiktoken.get_encoding(_DEF_ENCODING)
    return len(enc.encode(prompt))


def count_tokens(prompt: str, model: str) -> int:
    tokens = _estimate_tokens_with_tiktoken(prompt, model)
    if tokens > 0:
        return tokens
    # fallback heuristic: 1 token ~ 4 chars
    return max(1, math.ceil(len(prompt) / 4))


def estimate_cost_usd(
    prompt_tokens: int, completion_tokens: int, price_per_1k: dict[str, float]
) -> float:
    prompt_cost = (prompt_tokens / 1000.0) * price_per_1k.get("prompt", 0.0)
    completion_cost = (completion_tokens / 1000.0) * price_per_1k.get("completion", 0.0)
    return round(prompt_cost + completion_cost, 6)


def timed_call(fn):
    start = time.time()
    result = fn()
    latency_ms = int((time.time() - start) * 1000)
    return result, latency_ms
