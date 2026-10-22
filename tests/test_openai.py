"""Tests for OpenAIClient."""

import json
from unittest.mock import Mock, patch

import pytest

from commity.config import LLMConfig
from commity.llm import OpenAIClient
from commity.utils.token_counter import TOKEN_SAFETY_MARGIN, count_tokens


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

        payload = mock_make_request.call_args.args[1]
        assert "thinking" not in payload

    @patch("commity.llm.openai.OpenAIClient._make_request")
    def test_generate_disables_thinking_for_supported_glm(self, mock_make_request):
        config = LLMConfig(
            provider="openai",
            base_url="https://open.bigmodel.cn/api/coding/paas/v4",
            model="glm-5.2",
            api_key="test-key",
            disable_thinking=True,
        )
        client = OpenAIClient(config)
        response = Mock()
        response.json.return_value = {"choices": [{"message": {"content": "test commit message"}}]}
        mock_make_request.return_value = response

        result = client.generate("test prompt")

        assert result == "test commit message"
        payload = mock_make_request.call_args.args[1]
        assert payload["thinking"] == {"type": "disabled"}

    @pytest.mark.parametrize("disable_thinking", [False, True])
    @patch("commity.llm.openai.OpenAIClient._make_request")
    def test_generate_with_repository_tool(self, mock_make_request, disable_thinking):
        config = LLMConfig(
            provider="openai",
            base_url="https://open.bigmodel.cn/api/coding/paas/v4",
            model="glm-5.2",
            disable_thinking=disable_thinking,
            api_key="test-key",
        )
        client = OpenAIClient(config)
        repository_tools = Mock()
        repository_tools.max_calls = 5
        repository_tools.definitions = [{"type": "function", "function": {"name": "read_file"}}]
        repository_tools.execute.return_value = "1: relevant source"

        tool_response = Mock()
        tool_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [
                            {
                                "id": "call-1",
                                "type": "function",
                                "function": {
                                    "name": "read_file",
                                    "arguments": json.dumps({"path": "app.py"}),
                                },
                            }
                        ],
                    }
                }
            ]
        }
        final_response = Mock()
        final_response.json.return_value = {
            "choices": [{"message": {"role": "assistant", "content": '{"type":"fix"}'}}]
        }
        mock_make_request.side_effect = [tool_response, final_response]

        result = client.generate_with_tools("test prompt", repository_tools)

        assert result == '{"type":"fix"}'
        repository_tools.execute.assert_called_once_with("read_file", {"path": "app.py"})
        second_payload = mock_make_request.call_args_list[1].args[1]
        assert second_payload["messages"][-1] == {
            "role": "tool",
            "tool_call_id": "call-1",
            "content": "1: relevant source",
        }

        for call in mock_make_request.call_args_list:
            payload = call.args[1]
            if disable_thinking:
                assert payload["thinking"] == {"type": "disabled"}
            else:
                assert "thinking" not in payload
        first_payload = mock_make_request.call_args_list[0].args[1]
        assert first_payload["tools"] == repository_tools.definitions
        assert first_payload["tool_choice"] == "auto"

    @patch("commity.llm.openai.OpenAIClient._make_request")
    def test_generate_with_tools_returns_without_calling_tool(self, mock_make_request):
        config = LLMConfig(
            provider="openai",
            base_url="https://api.openai.com/v1",
            model="gpt-3.5-turbo",
            api_key="test-key",
        )
        client = OpenAIClient(config)
        repository_tools = Mock(max_calls=5, definitions=[])
        response = Mock()
        response.json.return_value = {
            "choices": [{"message": {"role": "assistant", "content": "direct result"}}]
        }
        mock_make_request.return_value = response

        result = client.generate_with_tools("test prompt", repository_tools)

        assert result == "direct result"
        repository_tools.execute.assert_not_called()

    @pytest.mark.parametrize("tool_result", ["x" * 10_000, '"path": "C:\\source"\n' * 1_000])
    @patch("commity.llm.openai.OpenAIClient._make_request")
    def test_tool_result_is_truncated_to_remaining_context(self, mock_make_request, tool_result):
        config = LLMConfig(
            provider="openai",
            base_url="https://api.openai.com/v1",
            model="gpt-3.5-turbo",
            api_key="test-key",
            max_tokens=50,
            context_window_tokens=1000,
        )
        client = OpenAIClient(config)
        repository_tools = Mock()
        repository_tools.max_calls = 5
        repository_tools.definitions = [{"type": "function", "function": {"name": "read_file"}}]
        repository_tools.execute.return_value = tool_result

        tool_response = Mock()
        tool_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [
                            {
                                "id": "call-1",
                                "type": "function",
                                "function": {
                                    "name": "read_file",
                                    "arguments": '{"path":"app.py"}',
                                },
                            }
                        ],
                    }
                }
            ]
        }
        final_response = Mock()
        final_response.json.return_value = {
            "choices": [{"message": {"role": "assistant", "content": '{"type":"fix"}'}}]
        }
        mock_make_request.side_effect = [tool_response, final_response]

        result = client.generate_with_tools("test prompt", repository_tools)

        assert result == '{"type":"fix"}'
        second_payload = mock_make_request.call_args_list[1].args[1]
        tool_content = second_payload["messages"][-1]["content"]
        assert len(tool_content) < 10_000
        assert tool_content.endswith("[tool output truncated]")

        serialized = json.dumps(
            {"messages": second_payload["messages"], "tools": second_payload["tools"]},
            ensure_ascii=False,
            separators=(",", ":"),
        )
        assert count_tokens(serialized, config.model, config.provider) <= (
            config.context_window_tokens - config.max_tokens - TOKEN_SAFETY_MARGIN
        )
        assert mock_make_request.call_count == 2
