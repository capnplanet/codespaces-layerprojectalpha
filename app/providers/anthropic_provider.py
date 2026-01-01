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


class AnthropicProvider(LLMProvider):
    name = "anthropic"

    PRICE_PER_1K = {
        "claude-3-5-sonnet-20240620": {"prompt": 0.003, "completion": 0.015},
        "claude-3-opus-20240229": {"prompt": 0.015, "completion": 0.075},
    }

    def __init__(self, config: ProviderConfig, http_client: httpx.Client | None = None):
        self.config = config
        self.client = http_client or httpx.Client(base_url=config.base_url, timeout=30)

    def generate(self, prompt: str, tools: list[dict] | None = None) -> ProviderResponse:
        if not self.config.api_key:
            raise ProviderError("Anthropic API key missing")

        payload: dict = {
            "model": self.config.model,
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature,
            "messages": [{"role": "user", "content": prompt}],
        }
        if tools:
            payload["tools"] = tools

        def _call():
            return self.client.post(
                "/v1/messages",
                headers={
                    "x-api-key": self.config.api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json=payload,
            )

        response, latency_ms = timed_call(_call)
        if response.status_code >= 400:
            raise ProviderError(f"Anthropic error {response.status_code}: {response.text}")

        data = response.json()
        content_list = data.get("content", [])
        text = "".join([c.get("text", "") for c in content_list if isinstance(c, dict)])

        usage = data.get("usage", {})
        prompt_tokens = usage.get("input_tokens") or count_tokens(prompt, self.config.model)
        completion_tokens = usage.get("output_tokens") or count_tokens(text, self.config.model)
        total_tokens = prompt_tokens + completion_tokens

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
