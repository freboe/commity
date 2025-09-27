from abc import ABC, abstractmethod
from typing import Any

import requests


class LLMGenerationError(Exception):
    """Custom exception for LLM generation failures."""

    def __init__(self, message: str, status_code: int | None = None, details: str | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.details = details


class BaseLLMClient(ABC):
    default_base_url: str = ""
    default_model: str = ""

    def __init__(self, config: Any) -> None:
        self.config = config

    def _get_proxies(self) -> dict[str, str] | None:
        if self.config.proxy:
            return {"http": self.config.proxy, "https": self.config.proxy}
        return None

    def _handle_llm_error(self, e: Exception, response: requests.Response | None = None) -> None:
        """统一处理 LLM 相关的错误。"""
        error_message = str(e)
        status_code = None
        details = None

        if response is not None:
            status_code = response.status_code
            details = response.text
            error_message = f"LLM API error: {status_code} - {details}"

        raise LLMGenerationError(error_message, status_code, details)

    def _make_request(self, url: str, payload: dict, headers: dict) -> requests.Response:
        """通用的请求方法，处理所有客户端的共同逻辑。"""
        try:
            response = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=self.config.timeout,
                proxies=self._get_proxies(),
            )
            if response.status_code != 200:
                self._handle_llm_error(ValueError("Non-200 status code"), response)
            response.raise_for_status()
            return response
        except Exception as e:
            self._handle_llm_error(e)
            # This line should never be reached because _handle_llm_error always raises
            # But we need it for mypy to satisfy the return type
            raise  # Re-raise the exception that was already raised in _handle_llm_error

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
            response = self._make_request(url, payload, headers)
            json_response = response.json()
            result = json_response.get("response", None)
            return result
        except Exception:
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
        url = (
            f"{self.config.base_url}/v1beta/models/"
            f"{self.config.model}:generateContent?key={self.config.api_key}"
        )
        try:
            response = self._make_request(url, payload, headers)
            json_response = response.json()
            candidates = json_response.get("candidates", [])
            parts = candidates[0]["content"]["parts"] if candidates else []
            # parts 第一个为"thought"，第二个为 answer
            return parts[-1]["text"] if parts else None
        except Exception:
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
            response = self._make_request(url, payload, headers)
            json_response = response.json()
            result = json_response["choices"][0]["message"]["content"]
            return result
        except Exception:
            return None


class OpenRouterClient(BaseLLMClient):
    default_base_url = "https://openrouter.ai/api/v1"
    default_model = "qwen/qwen3-coder:free"

    def generate(self, prompt: str) -> str | None:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.config.api_key}",
            # "HTTP-Referer": "https://github.com/freboe/commity",
            "X-Title": "Commity CLI",
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
        except Exception:
            return None


LLM_CLIENTS = {
    "gemini": GeminiClient,
    "ollama": OllamaClient,
    "openai": OpenAIClient,
    "openrouter": OpenRouterClient,
}


def llm_client_factory(config: Any) -> BaseLLMClient:
    provider = config.provider
    if provider in LLM_CLIENTS:
        client_class = LLM_CLIENTS[provider]
        return client_class(config)  # type: ignore[abstract]
    raise NotImplementedError(f"Provider {provider} is not supported.")
