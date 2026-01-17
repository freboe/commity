"""NVIDIA LLM client implementation."""

from commity.llm.base import BaseLLMClient


class NvidiaClient(BaseLLMClient):
    """Client for NVIDIA LLM provider."""

    default_base_url = "https://integrate.api.nvidia.com/v1"
    default_model = "nvidia/llama-3.1-70b-instruct"

    def generate(self, prompt: str) -> str | None:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.config.api_key}",
        }
        payload = {
            "model": self.config.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
        }
        url = f"{self.config.base_url}/chat/completions"
        try:
            response = self._make_request(url, payload, headers)
            json_response = response.json()
            result = json_response["choices"][0]["message"]["content"]
            return result
        except Exception as e:
            self._handle_llm_error(e)
            return None
