"""Tests for NvidiaClient."""

from unittest.mock import Mock, patch

from commity.config import LLMConfig
from commity.llm import NvidiaClient


class TestNvidiaClient:
    """Tests for NvidiaClient."""

    def test_default_values(self):
        """Test default base_url and model."""
        assert NvidiaClient.default_base_url == "https://integrate.api.nvidia.com/v1"
        assert NvidiaClient.default_model == "nvidia/llama-3.1-70b-instruct"

    @patch("commity.llm.nvidia.NvidiaClient._make_request")
    def test_generate_success(self, mock_make_request):
        """Test successful generation."""
        config = LLMConfig(
            provider="nvidia",
            base_url="https://integrate.api.nvidia.com/v1",
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
