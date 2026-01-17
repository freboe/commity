"""Tests for GeminiClient."""

from unittest.mock import Mock, patch

from commity.config import LLMConfig
from commity.llm import GeminiClient


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
