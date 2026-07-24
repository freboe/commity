"""OpenAI LLM client implementation."""

import json

from commity.llm.base import BaseLLMClient
from commity.repository_tools import ReadOnlyRepositoryTools


class OpenAIClient(BaseLLMClient):
    """Client for OpenAI LLM provider."""

    default_base_url = "https://api.openai.com/v1"
    default_model = "gpt-3.5-turbo"

    def generate(self, prompt: str) -> str | None:
        return self._generate([{"role": "user", "content": prompt}])

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
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.get("id", ""),
                        "content": result,
                    }
                )

        messages.append(
            {
                "role": "user",
                "content": "The repository tool limit is reached. Return the commit JSON now.",
            }
        )
        return self._generate(messages)

    def _generate(self, messages: list[dict]) -> str | None:
        try:
            return self._request_message(messages).get("content")
        except Exception as e:
            self._handle_llm_error(e)
            return None

    def _request_message(self, messages: list[dict], tools: list[dict] | None = None) -> dict:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.config.api_key}",
        }
        payload = {
            "model": self.config.model,
            "messages": messages,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
        }
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"
        url = f"{self.config.base_url}/chat/completions"
        response = self._make_request(url, payload, headers)
        return response.json()["choices"][0]["message"]
