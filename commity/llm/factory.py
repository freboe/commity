"""Factory for creating LLM clients."""

from typing import TYPE_CHECKING

from commity.llm.anthropic import AnthropicClient
from commity.llm.base import BaseLLMClient
from commity.llm.deepseek import DeepSeekClient
from commity.llm.gemini import GeminiClient
from commity.llm.glm import GLMClient
from commity.llm.kimi import KimiClient
from commity.llm.nvidia import NvidiaClient
from commity.llm.ollama import OllamaClient
from commity.llm.openai import OpenAIClient
from commity.llm.openrouter import OpenRouterClient
from commity.llm.qwen import QwenClient

if TYPE_CHECKING:
    from commity.config import LLMConfig

LLM_CLIENTS = {
    "anthropic": AnthropicClient,
    "claude": AnthropicClient,
    "dashscope": QwenClient,
    "moonshot": KimiClient,
    "bigmodel": GLMClient,
    "deepseek": DeepSeekClient,
    "qwen": QwenClient,
    "kimi": KimiClient,
    "glm": GLMClient,
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
