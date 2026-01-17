"""Tests for BaseLLMClient."""

from unittest.mock import Mock, patch

import pytest

from commity.config import LLMConfig
from commity.llm import LLMGenerationError, OllamaClient


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
