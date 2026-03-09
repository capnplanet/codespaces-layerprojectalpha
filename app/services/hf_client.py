from __future__ import annotations

import time
from typing import Any

import httpx
from tenacity import RetryError, retry, stop_after_attempt, wait_exponential


class HFClient:
    def __init__(
        self,
        endpoint_url: str,
        token: str,
        timeout_ms: int = 15000,
        max_retries: int = 2,
        model: str = "",
    ):
        self.endpoint_url = endpoint_url
        self.token = token
        self.timeout_s = max(timeout_ms, 1000) / 1000
        self.max_retries = max(max_retries, 0)
        self.model = model

    def is_configured(self) -> bool:
        return bool(self.endpoint_url and self.token)

    def generate(self, prompt: str, max_new_tokens: int = 256) -> tuple[str, int, dict[str, Any]]:
        start = time.time()
        response_data = self._call(prompt, max_new_tokens=max_new_tokens)
        generated_text = self._extract_text(response_data)
        latency_ms = int((time.time() - start) * 1000)
        metadata = {
            "provider": "huggingface",
            "endpoint": self._safe_endpoint_hint(),
            "model": self.model or "unknown",
        }
        return generated_text, latency_ms, metadata

    def _safe_endpoint_hint(self) -> str:
        # Avoid logging full endpoint values in traces and responses.
        return self.endpoint_url.split("?")[0][:80]

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

    def _payload(self, prompt: str, max_new_tokens: int) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "inputs": prompt,
            "parameters": {"max_new_tokens": max_new_tokens, "return_full_text": False},
        }
        if self.model:
            payload["model"] = self.model
        return payload

    def _extract_text(self, data: Any) -> str:
        if isinstance(data, list) and data:
            first = data[0]
            if isinstance(first, dict):
                if "generated_text" in first and isinstance(first["generated_text"], str):
                    return first["generated_text"]
                if "summary_text" in first and isinstance(first["summary_text"], str):
                    return first["summary_text"]
        if isinstance(data, dict):
            if "generated_text" in data and isinstance(data["generated_text"], str):
                return data["generated_text"]
            if "text" in data and isinstance(data["text"], str):
                return data["text"]
            if "choices" in data and isinstance(data["choices"], list) and data["choices"]:
                choice = data["choices"][0]
                if isinstance(choice, dict):
                    message = choice.get("message")
                    if isinstance(message, dict) and isinstance(message.get("content"), str):
                        return message["content"]
                    if isinstance(choice.get("text"), str):
                        return choice["text"]
            if "error" in data and isinstance(data["error"], str):
                raise RuntimeError(f"hf_error:{data['error']}")
        raise RuntimeError("hf_error:unrecognized_response")

    def _do_call(self, prompt: str, max_new_tokens: int) -> Any:
        with httpx.Client(timeout=self.timeout_s) as client:
            response = client.post(
                self.endpoint_url,
                headers=self._headers(),
                json=self._payload(prompt, max_new_tokens),
            )
            response.raise_for_status()
            return response.json()

    def _call(self, prompt: str, max_new_tokens: int) -> Any:
        if not self.is_configured():
            raise RuntimeError("hf_error:not_configured")
        if self.max_retries == 0:
            return self._do_call(prompt, max_new_tokens)

        @retry(
            wait=wait_exponential(multiplier=0.25, min=0.25, max=2),
            stop=stop_after_attempt(self.max_retries + 1),
            reraise=True,
        )
        def _retry_call() -> Any:
            return self._do_call(prompt, max_new_tokens)

        try:
            return _retry_call()
        except RetryError as exc:
            raise RuntimeError("hf_error:retry_exhausted") from exc
