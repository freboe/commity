import requests
from typing import Optional
from abc import ABC, abstractmethod
from rich import print

class BaseLLMClient(ABC):
    def __init__(self, config):
        self.config = config

    def _get_proxies(self):
        if self.config.proxy:
            return {"http": self.config.proxy, "https": self.config.proxy}
        return None

    @abstractmethod
    def generate(self, prompt: str) -> Optional[str]:
        raise NotImplementedError

class OllamaClient(BaseLLMClient):
    def generate(self, prompt: str) -> Optional[str]:
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
            response = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=self.config.timeout,
                proxies=self._get_proxies(),
            )
            if response.status_code != 200:
                print(f"[LLM Error] {response.status_code} - {response.text}")
                return None
            response.raise_for_status()
            json_response = response.json()
            result = json_response.get("response", None)
            return result
        except Exception as e:
            print(f"[LLM Error] {e}")
            return None

class GeminiClient(BaseLLMClient):
    def generate(self, prompt: str) -> Optional[str]:
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": self.config.temperature,
                "maxOutputTokens": self.config.max_tokens,
            },
        }
        url = f"{self.config.base_url}/v1beta/models/{self.config.model}:generateContent?key={self.config.api_key}"
        try:
            response = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=self.config.timeout,
                proxies=self._get_proxies(),
            )
            if response.status_code != 200:
                print(f"[LLM Error] {response.status_code} - {response.text}")
                return None
            response.raise_for_status()
            json_response = response.json()
            candidates = json_response.get("candidates", [])
            return candidates[0]["content"]["parts"][0]["text"] if candidates else None
        except Exception as e:
            print(f"[LLM Error] {e}")
            return None

def llm_client_factory(config) -> BaseLLMClient:
    if config.provider == "gemini":
        return GeminiClient(config)
    elif config.provider == "ollama":
        return OllamaClient(config)
    else:
        raise NotImplementedError(f"Provider {config.provider} is not supported.")
