"""OpenAI LLM client implementation."""

import json

from commity.llm.base import LLMGenerationError
from commity.llm.chat_completions import ChatCompletionsClient
from commity.repository_tools import ReadOnlyRepositoryTools
from commity.utils.token_counter import (
    TOKEN_SAFETY_MARGIN,
    count_tokens,
)


class OpenAIClient(ChatCompletionsClient):
    """Client for OpenAI LLM provider."""

    default_base_url = "https://api.openai.com/v1"
    default_model = "gpt-3.5-turbo"

    def generate_with_tools(
        self, prompt: str, repository_tools: ReadOnlyRepositoryTools
    ) -> str | None:
        messages = [{"role": "user", "content": prompt}]
        for _ in range(repository_tools.max_calls):
            message = self._request_message(messages, tools=repository_tools.definitions)
            tool_calls = message.get("tool_calls") or []
            if not tool_calls:
                return message.get("content")

            messages.append(message)
            for tool_call in tool_calls:
                function = tool_call.get("function", {})
                try:
                    arguments = json.loads(function.get("arguments", "{}"))
                except (TypeError, json.JSONDecodeError):
                    result = json.dumps({"error": "tool arguments must be valid JSON"})
                else:
                    result = repository_tools.execute(function.get("name", ""), arguments)
                tool_message = {
                    "role": "tool",
                    "tool_call_id": tool_call.get("id", ""),
                    "content": "",
                }
                tool_message["content"] = self._truncate_tool_result(
                    result, messages, tool_message, repository_tools.definitions
                )
                messages.append(tool_message)

        messages.append(
            {
                "role": "user",
                "content": "The repository tool limit is reached. Return the commit JSON now.",
            }
        )
        return self._generate(messages)

    def _request_message(self, messages: list[dict], tools: list[dict] | None = None) -> dict:
        if self._remaining_input_tokens(messages, tools) < 0:
            raise LLMGenerationError(
                "Model context window exceeded before request",
                status_code=400,
                details="context window token budget exhausted",
            )
        return super()._request_message(messages, tools)

    def _request_payload(self, messages: list[dict], tools: list[dict] | None = None) -> dict:
        payload = super()._request_payload(messages, tools)
        if self.config.disable_thinking:
            payload["thinking"] = {"type": "disabled"}
        return payload

    def _truncate_tool_result(
        self,
        result: str,
        messages: list[dict],
        tool_message: dict,
        tools: list[dict],
    ) -> str:
        """Fit tool output using the serialized request, including JSON escaping."""

        def fits(content: str) -> bool:
            candidate = {**tool_message, "content": content}
            return self._remaining_input_tokens([*messages, candidate], tools) >= 0

        if fits(result):
            return result
        suffix = "\n[tool output truncated]"
        if not fits(suffix):
            suffix = ""
        low, high = 0, len(result)
        while low < high:
            middle = (low + high + 1) // 2
            if fits(result[:middle] + suffix):
                low = middle
            else:
                high = middle - 1
        return result[:low] + suffix

    def _remaining_input_tokens(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
    ) -> int:
        request_content = {
            "messages": messages,
            "tools": tools or [],
        }
        serialized = json.dumps(
            request_content,
            ensure_ascii=False,
            separators=(",", ":"),
        )
        used_tokens = count_tokens(serialized, self.config.model, self.config.provider)
        return (
            self.config.context_window_tokens
            - self.config.max_tokens
            - TOKEN_SAFETY_MARGIN
            - used_tokens
        )
