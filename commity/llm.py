from abc import ABC, abstractmethod

import requests
from rich import print


class BaseLLMClient(ABC):
    def __init__(self, config):
        self.config = config

    def _get_proxies(self):
        if self.config.proxy:
            return {"http": self.config.proxy, "https": self.config.proxy}
        return None

    @abstractmethod
    def generate(self, prompt: str) -> str | None:
        raise NotImplementedError

class OllamaClient(BaseLLMClient):
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

class OpenAIClient(BaseLLMClient):
    default_base_url = "https://api.openai.com/v1"
    default_model = "gpt-3.5-turbo"

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
            result = json_response["choices"][0]["message"]["content"]
            return result
        except Exception as e:
            print(f"[LLM Error] {e}")
            return None

LLM_CLIENTS = {
    "gemini": GeminiClient,
    "ollama": OllamaClient,
    "openai": OpenAIClient,
}


def llm_client_factory(config) -> BaseLLMClient:
    provider = config.provider
    if provider in LLM_CLIENTS:
        client_class = LLM_CLIENTS[provider]
        return client_class(config)
    raise NotImplementedError(f"Provider {provider} is not supported.")
