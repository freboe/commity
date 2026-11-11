"""LLM client implementations for various providers.

This module provides a unified interface for different LLM providers.
To add a new provider:
1. Create a new file in this directory (e.g., newprovider.py)
2. Implement a client class inheriting from BaseLLMClient
3. Add it to the LLM_CLIENTS dict in factory.py
4. Export it here if needed
"""

from commity.llm.anthropic import AnthropicClient
from commity.llm.base import BaseLLMClient, LLMGenerationError, SensitiveDataError
from commity.llm.deepseek import DeepSeekClient
from commity.llm.factory import LLM_CLIENTS, llm_client_factory
from commity.llm.gemini import GeminiClient
from commity.llm.glm import GLMClient
from commity.llm.kimi import KimiClient
from commity.llm.nvidia import NvidiaClient
from commity.llm.ollama import OllamaClient
from commity.llm.openai import OpenAIClient
from commity.llm.openrouter import OpenRouterClient
from commity.llm.qwen import QwenClient

__all__ = [
    "LLM_CLIENTS",
    "AnthropicClient",
    "BaseLLMClient",
    "DeepSeekClient",
    "GLMClient",
    "GeminiClient",
    "KimiClient",
    "LLMGenerationError",
    "NvidiaClient",
    "OllamaClient",
    "OpenAIClient",
    "OpenRouterClient",
    "QwenClient",
    "SensitiveDataError",
    "llm_client_factory",
]
