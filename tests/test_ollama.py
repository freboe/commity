"""Tests for OllamaClient."""

from unittest.mock import Mock, patch

from commity.config import LLMConfig
from commity.llm import OllamaClient


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
