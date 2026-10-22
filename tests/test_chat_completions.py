"""Protocol regression tests shared by Chat Completions providers."""

from unittest.mock import Mock

import pytest

from commity.config import LLMConfig
from commity.llm import LLMGenerationError, NvidiaClient, OpenAIClient, OpenRouterClient


@pytest.fixture(
    params=[("openai", OpenAIClient), ("nvidia", NvidiaClient), ("openrouter", OpenRouterClient)]
)
def chat_client(request):
    provider, client_class = request.param
    return client_class(
        LLMConfig(
            provider=provider,
            base_url=client_class.default_base_url,
            model=client_class.default_model,
            api_key="test-key",
        )
    )


def test_preserves_provider_request_contract(chat_client, mocker):
    response = Mock()
    response.json.return_value = {"choices": [{"message": {"content": "fix: handle input"}}]}
    make_request = mocker.patch.object(chat_client, "_make_request", return_value=response)

    assert chat_client.generate("staged diff") == "fix: handle input"

    config = chat_client.config
    headers = {"Content-Type": "application/json", "Authorization": "Bearer test-key"}
    if config.provider == "openrouter":
        headers["X-Title"] = "Commity CLI"
    make_request.assert_called_once_with(
        f"{config.base_url}/chat/completions",
        {
            "model": config.model,
            "messages": [{"role": "user", "content": "staged diff"}],
            "temperature": config.temperature,
            "max_tokens": config.max_tokens,
        },
        headers,
    )


def test_preserves_request_error_details(chat_client, mocker):
    error = LLMGenerationError("request rejected", status_code=429, details="rate limited")
    mocker.patch.object(chat_client, "_make_request", side_effect=error)

    with pytest.raises(LLMGenerationError) as caught:
        chat_client.generate("staged diff")

    assert caught.value is error


def test_invalid_response_is_reported_as_generation_error(chat_client, mocker):
    response = Mock()
    response.json.return_value = {"choices": []}
    mocker.patch.object(chat_client, "_make_request", return_value=response)

    with pytest.raises(LLMGenerationError):
        chat_client.generate("staged diff")
