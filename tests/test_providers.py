import httpx

from app.providers.anthropic_provider import AnthropicProvider
from app.providers.base import ProviderConfig
from app.providers.openai_provider import OpenAIProvider


def test_openai_provider_mock():
    def handler(request: httpx.Request) -> httpx.Response:
        data = {
            "choices": [{"message": {"content": "hello world"}}],
            "usage": {"prompt_tokens": 5, "completion_tokens": 2, "total_tokens": 7},
        }
        return httpx.Response(200, json=data)

    transport = httpx.MockTransport(handler)
    client = httpx.Client(transport=transport, base_url="https://mock")
    provider = OpenAIProvider(
        ProviderConfig(
            api_key="test",
            base_url="https://mock",
            model="gpt-4o-mini",
            temperature=0.0,
            max_tokens=50,
        ),
        http_client=client,
    )

    resp = provider.generate("hi")
    assert resp.text == "hello world"
    assert resp.prompt_tokens == 5
    assert resp.completion_tokens == 2
    assert resp.total_tokens == 7
    assert resp.cost_usd >= 0


def test_anthropic_provider_mock():
    def handler(request: httpx.Request) -> httpx.Response:
        data = {
            "content": [{"text": "anthropic reply"}],
            "usage": {"input_tokens": 6, "output_tokens": 4},
        }
        return httpx.Response(200, json=data)

    transport = httpx.MockTransport(handler)
    client = httpx.Client(transport=transport, base_url="https://mock")
    provider = AnthropicProvider(
        ProviderConfig(
            api_key="test",
            base_url="https://mock",
            model="claude-3-5-sonnet-20240620",
            temperature=0.0,
            max_tokens=50,
        ),
        http_client=client,
    )

    resp = provider.generate("hi")
    assert resp.text == "anthropic reply"
    assert resp.prompt_tokens == 6
    assert resp.completion_tokens == 4
    assert resp.total_tokens == 10
    assert resp.cost_usd >= 0
