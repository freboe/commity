"""Tests for LLM module."""

from unittest.mock import Mock, patch

import pytest

from commity.config import LLMConfig
from commity.llm import (
    GeminiClient,
    LLMGenerationError,
    NvidiaClient,
    OllamaClient,
    OpenAIClient,
    OpenRouterClient,
    llm_client_factory,
)


class TestBaseLLMClient:
    """Tests for BaseLLMClient."""

    def test_get_proxies_with_proxy(self):
        """Test _get_proxies when proxy is set."""
        config = LLMConfig(
            provider="ollama",
            base_url="http://localhost:11434",
            model="llama3",
            proxy="http://proxy:8080",
        )
        client = OllamaClient(config)
        proxies = client._get_proxies()  # noqa: SLF001
        assert proxies == {"http": "http://proxy:8080", "https": "http://proxy:8080"}

    def test_get_proxies_without_proxy(self):
        """Test _get_proxies when proxy is not set."""
        config = LLMConfig(
            provider="ollama",
            base_url="http://localhost:11434",
            model="llama3",
        )
        client = OllamaClient(config)
        proxies = client._get_proxies()  # noqa: SLF001
        assert proxies is None

    def test_handle_llm_error_with_response(self):
        """Test _handle_llm_error with response."""
        config = LLMConfig(
            provider="ollama",
            base_url="http://localhost:11434",
            model="llama3",
        )
        client = OllamaClient(config)

        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"

        with pytest.raises(LLMGenerationError) as exc_info:
            client._handle_llm_error(ValueError("test error"), mock_response)  # noqa: SLF001

        assert exc_info.value.status_code == 500
        assert exc_info.value.details == "Internal Server Error"

    def test_handle_llm_error_without_response(self):
        """Test _handle_llm_error without response."""
        config = LLMConfig(
            provider="ollama",
            base_url="http://localhost:11434",
            model="llama3",
        )
        client = OllamaClient(config)

        with pytest.raises(LLMGenerationError) as exc_info:
            client._handle_llm_error(ValueError("test error"))  # noqa: SLF001

        assert "test error" in str(exc_info.value)
        assert exc_info.value.status_code is None

    @patch("commity.llm.base.requests.post")
    def test_make_request_success(self, mock_post):
        """Test _make_request with successful response."""
        config = LLMConfig(
            provider="ollama",
            base_url="http://localhost:11434",
            model="llama3",
        )
        client = OllamaClient(config)

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"response": "test"}
        mock_post.return_value = mock_response

        response = client._make_request(  # noqa: SLF001
            "http://test/api",
            {"model": "test"},
            {"Content-Type": "application/json"},
        )

        assert response.status_code == 200
        mock_post.assert_called_once()

    @patch("commity.llm.base.requests.post")
    def test_make_request_non_200_status(self, mock_post):
        """Test _make_request with non-200 status."""
        config = LLMConfig(
            provider="ollama",
            base_url="http://localhost:11434",
            model="llama3",
        )
        client = OllamaClient(config)

        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Error"
        mock_post.return_value = mock_response

        with pytest.raises(LLMGenerationError):
            client._make_request(  # noqa: SLF001
                "http://test/api",
                {"model": "test"},
                {"Content-Type": "application/json"},
            )


class TestOllamaClient:
    """Tests for OllamaClient."""

    def test_default_values(self):
        """Test default base_url and model."""
        assert OllamaClient.default_base_url == "http://localhost:11434"
        assert OllamaClient.default_model == "llama3"

    @patch("commity.llm.ollama.OllamaClient._make_request")
    def test_generate_success(self, mock_make_request):
        """Test successful generation."""
        config = LLMConfig(
            provider="ollama",
            base_url="http://localhost:11434",
            model="llama3",
        )
        client = OllamaClient(config)

        mock_response = Mock()
        mock_response.json.return_value = {"response": "test commit message"}
        mock_make_request.return_value = mock_response

        result = client.generate("test prompt")
        assert result == "test commit message"

    @patch("commity.llm.ollama.OllamaClient._make_request")
    def test_generate_empty_response(self, mock_make_request):
        """Test generation with empty response."""
        config = LLMConfig(
            provider="ollama",
            base_url="http://localhost:11434",
            model="llama3",
        )
        client = OllamaClient(config)

        mock_response = Mock()
        mock_response.json.return_value = {}
        mock_make_request.return_value = mock_response

        result = client.generate("test prompt")
        assert result is None


class TestGeminiClient:
    """Tests for GeminiClient."""

    def test_default_values(self):
        """Test default base_url and model."""
        assert GeminiClient.default_base_url == "https://generativelanguage.googleapis.com"
        assert GeminiClient.default_model == "gemini-2.5-flash"

    @patch("commity.llm.gemini.GeminiClient._make_request")
    def test_generate_success(self, mock_make_request):
        """Test successful generation."""
        config = LLMConfig(
            provider="gemini",
            base_url="https://generativelanguage.googleapis.com",
            model="gemini-2.5-flash",
            api_key="test-key",
        )
        client = GeminiClient(config)

        mock_response = Mock()
        mock_response.json.return_value = {
            "candidates": [{"content": {"parts": [{"text": "test commit message"}]}}]
        }
        mock_make_request.return_value = mock_response

        result = client.generate("test prompt")
        assert result == "test commit message"

    @patch("commity.llm.gemini.GeminiClient._make_request")
    def test_generate_with_multiple_parts(self, mock_make_request):
        """Test generation with multiple parts (thought and answer)."""
        config = LLMConfig(
            provider="gemini",
            base_url="https://generativelanguage.googleapis.com",
            model="gemini-2.5-flash",
            api_key="test-key",
        )
        client = GeminiClient(config)

        mock_response = Mock()
        mock_response.json.return_value = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {"text": "thinking..."},
                            {"text": "final commit message"},
                        ]
                    }
                }
            ]
        }
        mock_make_request.return_value = mock_response

        result = client.generate("test prompt")
        assert result == "final commit message"  # Should get the last part


class TestOpenAIClient:
    """Tests for OpenAIClient."""

    def test_default_values(self):
        """Test default base_url and model."""
        assert OpenAIClient.default_base_url == "https://api.openai.com/v1"
        assert OpenAIClient.default_model == "gpt-3.5-turbo"

    @patch("commity.llm.openai.OpenAIClient._make_request")
    def test_generate_success(self, mock_make_request):
        """Test successful generation."""
        config = LLMConfig(
            provider="openai",
            base_url="https://api.openai.com/v1",
            model="gpt-3.5-turbo",
            api_key="test-key",
        )
        client = OpenAIClient(config)

        mock_response = Mock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "test commit message"}}]
        }
        mock_make_request.return_value = mock_response

        result = client.generate("test prompt")
        assert result == "test commit message"


class TestOpenRouterClient:
    """Tests for OpenRouterClient."""

    def test_default_values(self):
        """Test default base_url and model."""
        assert OpenRouterClient.default_base_url == "https://openrouter.ai/api/v1"
        assert OpenRouterClient.default_model == "qwen/qwen3-coder:free"

    @patch("commity.llm.openrouter.OpenRouterClient._make_request")
    def test_generate_success(self, mock_make_request):
        """Test successful generation."""
        config = LLMConfig(
            provider="openrouter",
            base_url="https://openrouter.ai/api/v1",
            model="qwen/qwen3-coder:free",
            api_key="test-key",
        )
        client = OpenRouterClient(config)

        mock_response = Mock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "test commit message"}}]
        }
        mock_make_request.return_value = mock_response

        result = client.generate("test prompt")
        assert result == "test commit message"


class TestNvidiaClient:
    """Tests for NvidiaClient."""

    def test_default_values(self):
        """Test default base_url and model."""
        assert NvidiaClient.default_base_url == "https://integrate.api.nvidia.com"
        assert NvidiaClient.default_model == "nvidia/llama-3.1-70b-instruct"

    @patch("commity.llm.nvidia.NvidiaClient._make_request")
    def test_generate_success(self, mock_make_request):
        """Test successful generation."""
        config = LLMConfig(
            provider="nvidia",
            base_url="https://integrate.api.nvidia.com",
            model="nvidia/llama-3.1-70b-instruct",
            api_key="test-key",
        )
        client = NvidiaClient(config)

        mock_response = Mock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "test commit message"}}]
        }
        mock_make_request.return_value = mock_response

        result = client.generate("test prompt")
        assert result == "test commit message"


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
            base_url="https://integrate.api.nvidia.com",
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
