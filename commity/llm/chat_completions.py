"""Shared request protocol for Chat Completions providers."""

from commity.llm.base import BaseLLMClient


class ChatCompletionsClient(BaseLLMClient):
    """Reuse the chat wire format while allowing provider-specific headers."""

    def generate(self, prompt: str) -> str | None:
        return self._generate([{"role": "user", "content": prompt}])

    def _generate(self, messages: list[dict]) -> str | None:
        try:
            return self._request_message(messages).get("content")
        except Exception as error:
            self._handle_llm_error(error)
            return None

    def _request_headers(self) -> dict[str, str]:
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.config.api_key}",
        }

    def _request_payload(self, messages: list[dict], tools: list[dict] | None = None) -> dict:
        payload = {
            "model": self.config.model,
            "messages": messages,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
        }
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"
        return payload

    def _request_message(self, messages: list[dict], tools: list[dict] | None = None) -> dict:
        response = self._make_request(
            f"{self.config.base_url}/chat/completions",
            self._request_payload(messages, tools),
            self._request_headers(),
        )
        return response.json()["choices"][0]["message"]
