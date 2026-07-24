"""Base classes and exceptions for LLM clients."""

from abc import ABC, abstractmethod
from time import sleep
from typing import TYPE_CHECKING

import requests

if TYPE_CHECKING:
    from commity.config import LLMConfig
    from commity.repository_tools import ReadOnlyRepositoryTools


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
    max_attempts: int = 3

    def __init__(self, config: "LLMConfig") -> None:
        self.config = config

    def _get_proxies(self) -> dict[str, str] | None:
        if self.config.proxy:
            return {"http": self.config.proxy, "https": self.config.proxy}
        return None

    def _handle_llm_error(self, e: Exception, response: requests.Response | None = None) -> None:
        """统一处理 LLM 相关的错误。"""
        if isinstance(e, LLMGenerationError):
            raise e

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
        for attempt in range(self.max_attempts):
            try:
                response = requests.post(
                    url,
                    json=payload,
                    headers=headers,
                    timeout=self.config.timeout,
                    proxies=self._get_proxies(),
                )
            except requests.RequestException as error:
                if attempt + 1 == self.max_attempts:
                    self._handle_llm_error(error)
                sleep(0.5 * 2**attempt)
                continue
            except Exception as error:
                self._handle_llm_error(error)

            if response.status_code == 200:
                return response
            if (response.status_code == 429 or response.status_code >= 500) and (
                attempt + 1 < self.max_attempts
            ):
                sleep(0.5 * 2**attempt)
                continue
            self._handle_llm_error(ValueError("Non-200 status code"), response)

        raise LLMGenerationError("LLM request failed after retries")

    @abstractmethod
    def generate(self, prompt: str) -> str | None:
        raise NotImplementedError

    def generate_with_tools(
        self, prompt: str, _repository_tools: "ReadOnlyRepositoryTools"
    ) -> str | None:
        return self.generate(prompt)
