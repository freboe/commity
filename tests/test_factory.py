"""Tests for llm_client_factory."""

import pytest

from commity.config import LLMConfig
from commity.llm import (
    GeminiClient,
    NvidiaClient,
    OllamaClient,
    OpenAIClient,
    OpenRouterClient,
    llm_client_factory,
)


class TestLLMClientFactory:
    """Tests for llm_client_factory."""

    def test_factory_ollama(self):
        """Test factory creates OllamaClient."""
        config = LLMConfig(
            provider="ollama",
            base_url="http://localhost:11434",
            model="llama3",
        )
        client = llm_client_factory(config)
        assert isinstance(client, OllamaClient)

    def test_factory_gemini(self):
        """Test factory creates GeminiClient."""
        config = LLMConfig(
            provider="gemini",
            base_url="https://generativelanguage.googleapis.com",
            model="gemini-2.5-flash",
            api_key="test-key",
        )
        client = llm_client_factory(config)
        assert isinstance(client, GeminiClient)

    def test_factory_openai(self):
        """Test factory creates OpenAIClient."""
        config = LLMConfig(
            provider="openai",
            base_url="https://api.openai.com/v1",
            model="gpt-3.5-turbo",
            api_key="test-key",
        )
        client = llm_client_factory(config)
        assert isinstance(client, OpenAIClient)

    def test_factory_openrouter(self):
        """Test factory creates OpenRouterClient."""
        config = LLMConfig(
            provider="openrouter",
            base_url="https://openrouter.ai/api/v1",
            model="qwen/qwen3-coder:free",
            api_key="test-key",
        )
        client = llm_client_factory(config)
        assert isinstance(client, OpenRouterClient)

    def test_factory_nvidia(self):
        """Test factory creates NvidiaClient."""
        config = LLMConfig(
            provider="nvidia",
            base_url="https://integrate.api.nvidia.com/v1",
            model="nvidia/llama-3.1-70b-instruct",
            api_key="test-key",
        )
        client = llm_client_factory(config)
        assert isinstance(client, NvidiaClient)

    def test_factory_unsupported_provider(self):
        """Test factory with unsupported provider."""
        config = LLMConfig(
            provider="unknown",
            base_url="http://test",
            model="test-model",
        )
        # Need to bypass validation
        config.provider = "unknown"  # Set after creation
        with pytest.raises(NotImplementedError, match="Provider unknown is not supported"):
            llm_client_factory(config)
