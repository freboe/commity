"""Tests for OpenAIClient."""

from unittest.mock import Mock, patch

from commity.config import LLMConfig
from commity.llm import OpenAIClient


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
