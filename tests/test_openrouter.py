"""Tests for OpenRouterClient."""

from unittest.mock import Mock, patch

from commity.config import LLMConfig
from commity.llm import OpenRouterClient


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
