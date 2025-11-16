"""Google Gemini LLM client implementation."""

from commity.llm.base import BaseLLMClient


class GeminiClient(BaseLLMClient):
    """Client for Google Gemini LLM provider."""

    default_base_url = "https://generativelanguage.googleapis.com"
    default_model = "gemini-2.5-flash"

    def generate(self, prompt: str) -> str | None:
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": self.config.temperature,
                "maxOutputTokens": self.config.max_tokens,
            },
        }
        url = (
            f"{self.config.base_url}/v1beta/models/"
            f"{self.config.model}:generateContent?key={self.config.api_key}"
        )
        try:
            response = self._make_request(url, payload, headers)
            json_response = response.json()
            candidates = json_response.get("candidates", [])
            parts = candidates[0]["content"]["parts"] if candidates else []
            # print(parts)
            # parts 第一个为"thought"，第二个为 answer
            return parts[-1]["text"] if parts else None
        except Exception as e:
            self._handle_llm_error(e)
            return None
