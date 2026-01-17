"""Factory for creating LLM clients."""

from typing import TYPE_CHECKING

from commity.llm.base import BaseLLMClient
from commity.llm.gemini import GeminiClient
from commity.llm.nvidia import NvidiaClient
from commity.llm.ollama import OllamaClient
from commity.llm.openai import OpenAIClient
from commity.llm.openrouter import OpenRouterClient

if TYPE_CHECKING:
    from commity.config import LLMConfig

LLM_CLIENTS = {
    "gemini": GeminiClient,
    "nvidia": NvidiaClient,
    "ollama": OllamaClient,
    "openai": OpenAIClient,
    "openrouter": OpenRouterClient,
}


def llm_client_factory(config: "LLMConfig") -> BaseLLMClient:
    """Create an LLM client based on the provider in config."""
    provider = config.provider
    if provider in LLM_CLIENTS:
        client_class = LLM_CLIENTS[provider]
        return client_class(config)  # type: ignore[abstract]
    raise NotImplementedError(f"Provider {provider} is not supported.")
