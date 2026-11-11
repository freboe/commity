"""Native Anthropic Messages API adapter."""

import json

from commity.llm.base import LLMGenerationError
from commity.llm.openai import OpenAIClient


class AnthropicClient(OpenAIClient):
    """Translate the shared repository tool loop to Anthropic content blocks."""

    default_base_url = "https://api.anthropic.com/v1"
    default_model = "claude-sonnet-4-5"

    def _request_payload(self, messages: list[dict], tools: list[dict] | None = None) -> dict:
        converted: list[dict] = []
        for message in messages:
            if message["role"] == "tool":
                block = {
                    "type": "tool_result",
                    "tool_use_id": message["tool_call_id"],
                    "content": message["content"],
                }
                if converted and converted[-1]["role"] == "user":
                    converted[-1]["content"].append(block)
                else:
                    converted.append({"role": "user", "content": [block]})
            else:
                content = message.get("native_content")
                if content is None:
                    content = [{"type": "text", "text": message["content"]}]
                converted.append({"role": message["role"], "content": content})
        payload = {
            "model": self.config.model,
            "messages": converted,
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature,
        }
        if tools:
            payload["tools"] = [
                {
                    "name": tool["function"]["name"],
                    "description": tool["function"].get("description", ""),
                    "input_schema": tool["function"]["parameters"],
                }
                for tool in tools
            ]
        return payload

    def _request_message(self, messages: list[dict], tools: list[dict] | None = None) -> dict:
        if self._remaining_input_tokens(messages, tools) < 0:
            raise LLMGenerationError(
                "Model context window exceeded before request", status_code=400
            )
        response = self._make_request(
            f"{self.config.base_url.rstrip('/')}/messages",
            self._request_payload(messages, tools),
            {
                "Content-Type": "application/json",
                "x-api-key": str(self.config.api_key),
                "anthropic-version": "2023-06-01",
            },
        ).json()
        if response.get("stop_reason") == "max_tokens":
            raise LLMGenerationError("Anthropic response exceeded max_tokens")
        blocks = response["content"]
        return {
            "role": "assistant",
            "content": "".join(block["text"] for block in blocks if block["type"] == "text"),
            "native_content": blocks,
            "tool_calls": [
                {
                    "id": block["id"],
                    "type": "function",
                    "function": {
                        "name": block["name"],
                        "arguments": json.dumps(block["input"]),
                    },
                }
                for block in blocks
                if block["type"] == "tool_use"
            ],
        }

    def _remaining_input_tokens(self, messages: list[dict], tools: list[dict] | None = None) -> int:
        # Count the native wire representation, including preserved thinking blocks.
        payload = self._request_payload(messages, tools)
        return super()._remaining_input_tokens(payload["messages"], payload.get("tools"))
