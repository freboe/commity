"""Ollama LLM client implementation."""

from commity.llm.base import BaseLLMClient


class OllamaClient(BaseLLMClient):
    """Client for Ollama LLM provider."""

    default_base_url = "http://localhost:11434"
    default_model = "llama3"

    def generate(self, prompt: str) -> str | None:
        headers = {"Content-Type": "application/json"}
        payload = {
            "model": self.config.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": self.config.temperature,
                "num_predict": self.config.max_tokens,
            },
        }
        url = f"{self.config.base_url}/api/generate"
        try:
            response = self._make_request(url, payload, headers)
            json_response = response.json()
            result = json_response.get("response", None)
            return result
        except Exception as e:
            self._handle_llm_error(e)
            return None
