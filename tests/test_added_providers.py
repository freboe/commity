"""Regression coverage for provider presets and Anthropic wire format."""

from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from pydantic import ValidationError

from commity.config import get_llm_config
from commity.llm import LLM_CLIENTS, LLMGenerationError, llm_client_factory


@pytest.mark.parametrize(
    "provider",
    [
        "deepseek",
        "qwen",
        "dashscope",
        "kimi",
        "moonshot",
        "glm",
        "bigmodel",
        "anthropic",
        "claude",
    ],
)
def test_provider_defaults_and_auth(provider, monkeypatch):
    monkeypatch.setattr("commity.config.load_config_from_file", dict)
    config = get_llm_config(SimpleNamespace(provider=provider, api_key="test-key"))
    client = llm_client_factory(config)
    assert isinstance(client, LLM_CLIENTS[provider])
    assert config.base_url == client.default_base_url
    assert config.model == client.default_model
    with pytest.raises(ValidationError, match="API key"):
        get_llm_config(SimpleNamespace(provider=provider, api_key=""))


@pytest.mark.parametrize("provider", ["deepseek", "qwen", "kimi", "glm"])
def test_compatible_request(provider, monkeypatch, mocker):
    monkeypatch.setattr("commity.config.load_config_from_file", dict)
    client = llm_client_factory(get_llm_config(SimpleNamespace(provider=provider, api_key="key")))
    response = Mock()
    response.json.return_value = {"choices": [{"message": {"content": "fix: input"}}]}
    request = mocker.patch.object(client, "_make_request", return_value=response)
    assert client.generate("diff") == "fix: input"
    url, payload, headers = request.call_args.args
    assert url == client.default_base_url + "/chat/completions"
    assert headers["Authorization"] == "Bearer key"
    assert payload["model"] == client.default_model
    if provider == "qwen":
        assert payload["enable_thinking"] is False


@pytest.fixture
def anthropic(monkeypatch):
    monkeypatch.setattr("commity.config.load_config_from_file", dict)
    return llm_client_factory(get_llm_config(SimpleNamespace(provider="anthropic", api_key="key")))


def test_anthropic_text_and_headers(anthropic, mocker):
    response = Mock()
    response.json.return_value = {
        "content": [
            {"type": "thinking", "thinking": "internal"},
            {"type": "text", "text": "fix: "},
            {"type": "text", "text": "input"},
        ]
    }
    request = mocker.patch.object(anthropic, "_make_request", return_value=response)
    assert anthropic.generate("diff") == "fix: input"
    url, payload, headers = request.call_args.args
    assert url == "https://api.anthropic.com/v1/messages"
    assert headers["x-api-key"] == "key"
    assert headers["anthropic-version"] == "2023-06-01"
    assert payload["messages"] == [{"role": "user", "content": [{"type": "text", "text": "diff"}]}]


def test_anthropic_parallel_tools(anthropic, mocker):
    blocks = [
        {"type": "tool_use", "id": str(i), "name": "read_file", "input": {"path": "a"}}
        for i in range(2)
    ]
    first, second = Mock(), Mock()
    first.json.return_value = {"content": blocks, "stop_reason": "tool_use"}
    second.json.return_value = {"content": [{"type": "text", "text": "fix: done"}]}
    request = mocker.patch.object(anthropic, "_make_request", side_effect=[first, second])
    tools = Mock(max_calls=3)
    tools.definitions = [
        {
            "type": "function",
            "function": {
                "name": "read_file",
                "description": "Read",
                "parameters": {"type": "object"},
            },
        }
    ]
    tools.execute.return_value = "file content"
    assert anthropic.generate_with_tools("diff", tools) == "fix: done"
    payload = request.call_args.args[1]
    assert payload["tools"][0]["input_schema"] == {"type": "object"}
    assert payload["messages"][1]["content"] == blocks
    assert [b["tool_use_id"] for b in payload["messages"][2]["content"]] == ["0", "1"]
    assert tools.execute.call_count == 2


@pytest.mark.parametrize("body", [{"content": [], "stop_reason": "max_tokens"}, {}])
def test_anthropic_invalid_or_truncated_response(anthropic, mocker, body):
    response = Mock()
    response.json.return_value = body
    mocker.patch.object(anthropic, "_make_request", return_value=response)
    with pytest.raises(LLMGenerationError):
        anthropic.generate("diff")


def test_glm_disable_thinking(monkeypatch):
    monkeypatch.setattr("commity.config.load_config_from_file", dict)
    client = llm_client_factory(
        get_llm_config(
            SimpleNamespace(
                provider="glm",
                api_key="key",
                disable_thinking=True,
            )
        )
    )
    assert client._request_payload([])["thinking"] == {"type": "disabled"}  # noqa: SLF001


def test_kimi_reasoning_request(monkeypatch, mocker):
    monkeypatch.setattr("commity.config.load_config_from_file", dict)
    client = llm_client_factory(get_llm_config(SimpleNamespace(provider="kimi", api_key="key")))
    first, second = Mock(), Mock()
    first.json.return_value = {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": None,
                    "reasoning_content": "inspect file",
                    "tool_calls": [
                        {
                            "id": "call1",
                            "type": "function",
                            "function": {
                                "name": "read_file",
                                "arguments": '{"path":"a"}',
                            },
                        }
                    ],
                }
            }
        ]
    }
    second.json.return_value = {"choices": [{"message": {"content": "fix: done"}}]}
    request = mocker.patch.object(client, "_make_request", side_effect=[first, second])
    tools = Mock(max_calls=3)
    tools.definitions = []
    tools.execute.return_value = "contents"
    assert client.generate_with_tools("diff", tools) == "fix: done"
    payload = request.call_args.args[1]
    assert payload["max_completion_tokens"] == 8192
    assert payload["reasoning_effort"] == "low"
    assert "temperature" not in payload
    assert "max_tokens" not in payload
    assert payload["messages"][1]["reasoning_content"] == "inspect file"
