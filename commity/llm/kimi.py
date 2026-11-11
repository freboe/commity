"""kimi OpenAI-compatible client."""

from commity.llm.openai import OpenAIClient


class KimiClient(OpenAIClient):
    """Client for the kimi API."""

    default_base_url = "https://api.moonshot.cn/v1"
    default_model = "kimi-k3.1-pro"

    def _request_payload(self, messages: list[dict], tools: list[dict] | None = None) -> dict:
        payload = super()._request_payload(messages, tools)
        if self.config.model.lower().startswith("kimi-k3"):
            payload.pop("temperature", None)
            payload["max_completion_tokens"] = payload.pop("max_tokens")
            payload["reasoning_effort"] = "low"
        return payload
