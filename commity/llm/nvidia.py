"""NVIDIA LLM client implementation."""

from commity.llm.chat_completions import ChatCompletionsClient


class NvidiaClient(ChatCompletionsClient):
    """Client for NVIDIA LLM provider."""

    default_base_url = "https://integrate.api.nvidia.com/v1"
    default_model = "nvidia/llama-3.1-70b-instruct"
