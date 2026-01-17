"""LLM client implementations for various providers.

This module provides a unified interface for different LLM providers.
To add a new provider:
1. Create a new file in this directory (e.g., newprovider.py)
2. Implement a client class inheriting from BaseLLMClient
3. Add it to the LLM_CLIENTS dict in factory.py
4. Export it here if needed
"""

from commity.llm.base import BaseLLMClient, LLMGenerationError
from commity.llm.factory import LLM_CLIENTS, llm_client_factory
from commity.llm.gemini import GeminiClient
from commity.llm.nvidia import NvidiaClient
from commity.llm.ollama import OllamaClient
from commity.llm.openai import OpenAIClient
from commity.llm.openrouter import OpenRouterClient

__all__ = [
    "LLM_CLIENTS",
    "BaseLLMClient",
    "GeminiClient",
    "LLMGenerationError",
    "NvidiaClient",
    "OllamaClient",
    "OpenAIClient",
    "OpenRouterClient",
    "llm_client_factory",
]
