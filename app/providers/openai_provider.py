from __future__ import annotations

import httpx

from app.providers.base import (
    LLMProvider,
    ProviderConfig,
    ProviderError,
    ProviderResponse,
    count_tokens,
    estimate_cost_usd,
    timed_call,
)


class OpenAIProvider(LLMProvider):
    name = "openai"

    # USD per 1K tokens (approx based on public pricing at time of writing)
    PRICE_PER_1K = {
        "gpt-4o-mini": {"prompt": 0.00015, "completion": 0.0006},
        "gpt-4o": {"prompt": 0.005, "completion": 0.015},
    }

    def __init__(self, config: ProviderConfig, http_client: httpx.Client | None = None):
        self.config = config
        self.client = http_client or httpx.Client(base_url=config.base_url, timeout=30)

    def generate(self, prompt: str, tools: list[dict] | None = None) -> ProviderResponse:
        if not self.config.api_key:
            raise ProviderError("OpenAI API key missing")

        payload: dict = {
            "model": self.config.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
        }
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        def _call():
            return self.client.post(
                "/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.config.api_key}"},
                json=payload,
            )

        response, latency_ms = timed_call(_call)
        if response.status_code >= 400:
            raise ProviderError(f"OpenAI error {response.status_code}: {response.text}")

        data = response.json()
        choice = data.get("choices", [{}])[0]
        message = choice.get("message", {})
        text = message.get("content", "") or ""

        usage = data.get("usage", {})
        prompt_tokens = usage.get("prompt_tokens") or count_tokens(prompt, self.config.model)
        completion_tokens = usage.get("completion_tokens") or count_tokens(text, self.config.model)
        total_tokens = usage.get("total_tokens") or prompt_tokens + completion_tokens

        pricing = self.PRICE_PER_1K.get(self.config.model, {"prompt": 0.0, "completion": 0.0})
        cost_usd = estimate_cost_usd(prompt_tokens, completion_tokens, pricing)

        return ProviderResponse(
            text=text,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            cost_usd=cost_usd,
            model=self.config.model,
            latency_ms=latency_ms,
            raw_response=data,
        )
