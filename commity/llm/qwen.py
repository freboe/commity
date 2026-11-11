"""qwen OpenAI-compatible client."""

from commity.llm.openai import OpenAIClient


class QwenClient(OpenAIClient):
    """Client for the qwen API."""

    default_base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    default_model = "qwen-plus"

    def _request_payload(self, messages: list[dict], tools: list[dict] | None = None) -> dict:
        payload = super()._request_payload(messages, tools)
        # Commity consumes a non-streaming final answer.
        payload["enable_thinking"] = False
        return payload
