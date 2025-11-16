"""Base classes and exceptions for LLM clients."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

import requests

if TYPE_CHECKING:
    from commity.config import LLMConfig


class LLMGenerationError(Exception):
    """Custom exception for LLM generation failures."""

    def __init__(self, message: str, status_code: int | None = None, details: str | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.details = details


class BaseLLMClient(ABC):
    """Base class for all LLM clients."""

    default_base_url: str = ""
    default_model: str = ""

    def __init__(self, config: "LLMConfig") -> None:
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
