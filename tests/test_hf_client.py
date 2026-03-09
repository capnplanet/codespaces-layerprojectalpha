from app.services.hf_client import HFClient


def test_extract_text_generated_text_list():
    client = HFClient(endpoint_url="https://example.com", token="x")
    data = [{"generated_text": "hello"}]
    assert client._extract_text(data) == "hello"


def test_extract_text_openai_style_choices():
    client = HFClient(endpoint_url="https://example.com", token="x")
    data = {"choices": [{"message": {"content": "hi"}}]}
    assert client._extract_text(data) == "hi"
