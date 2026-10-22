"""OpenRouter LLM client implementation."""

from commity.llm.chat_completions import ChatCompletionsClient


class OpenRouterClient(ChatCompletionsClient):
    """Client for OpenRouter LLM provider."""

    default_base_url = "https://openrouter.ai/api/v1"
    default_model = "qwen/qwen3-coder:free"

    def _request_headers(self) -> dict[str, str]:
        return {**super()._request_headers(), "X-Title": "Commity CLI"}
