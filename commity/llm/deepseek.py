"""deepseek OpenAI-compatible client."""

from commity.llm.openai import OpenAIClient


class DeepSeekClient(OpenAIClient):
    """Client for the deepseek API."""

    default_base_url = "https://api.deepseek.com"
    default_model = "deepseek-flash"

    def _request_payload(self, messages: list[dict], tools: list[dict] | None = None) -> dict:
        payload = super()._request_payload(messages, tools)
        if self.config.model.lower().startswith(("deepseek-flash", "deepseek-v4")):
            payload["thinking"] = {"type": "disabled"}
        return payload
