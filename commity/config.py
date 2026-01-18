import json
import os
from typing import Any, cast

from pydantic import BaseModel, Field, model_validator

from commity.llm import LLM_CLIENTS, BaseLLMClient

PROVIDERS_REQUIRING_API_KEY = {"gemini", "nvidia", "openai", "openrouter"}


def load_config_from_file() -> dict[str, Any]:
    config_path = os.path.expanduser("~/.commity/config.json")
    if os.path.exists(config_path):
        with open(config_path) as f:
            try:
                return cast("dict[str, Any]", json.load(f))
            except json.JSONDecodeError:
                print(f"Warning: Could not decode JSON from {config_path}")
                return {}
    return {}


class LLMConfig(BaseModel):
    """Configuration for LLM client."""

    provider: str = Field(..., description="LLM provider name")
    base_url: str = Field(..., description="Base URL for the LLM API")
    model: str = Field(..., description="Model name to use")
    api_key: str | None = Field(default=None, description="API key for authentication")
    temperature: float = Field(
        default=0.3, ge=0.0, le=1.0, description="Temperature for generation"
    )
    max_tokens: int = Field(default=3000, gt=0, description="Maximum tokens for response")
    timeout: int = Field(default=90, gt=0, description="Request timeout in seconds")
    proxy: str | None = Field(default=None, description="Proxy URL")
    debug: bool = Field(default=False, description="Enable debug mode")

    @model_validator(mode="after")
    def validate_api_key_for_provider(self) -> "LLMConfig":
        """Validate that providers requiring API keys have them."""
        if self.provider in PROVIDERS_REQUIRING_API_KEY and not self.api_key:
            raise ValueError(f"API key must be specified for provider '{self.provider}'")
        return self

    model_config = {"frozen": False, "validate_assignment": True}


def _resolve_config(
    arg_name: str, args: Any, file_config: dict[str, Any], default: Any, type_cast: Any = None
) -> Any:
    """Helper to resolve config values from args, env, or file."""
    env_key = f"COMMITY_{arg_name.upper()}"
    file_key = arg_name.upper()
    args_val = getattr(args, arg_name, None)

    # Priority: Command-line Arguments > Environment Variables > Configuration File > Default
    value = args_val
    if value is None:
        value = os.getenv(env_key)
    if value is None:
        value = file_config.get(file_key)
    if value is None:
        value = default

    # If we have a default of None and value is also None, that's okay
    if value is None and default is None:
        return None

    if value is not None and type_cast:
        try:
            return type_cast(value)
        except (ValueError, TypeError):
            print(
                f"Warning: Could not cast config value '{value}' for '{arg_name}' to type {type_cast.__name__}. Using default."
            )
            return default
    return value


def get_llm_config(args: Any) -> LLMConfig:
    file_config = load_config_from_file()

    provider = _resolve_config("provider", args, file_config, "gemini")

    client_class: type[BaseLLMClient] = cast(
        "type[BaseLLMClient]", LLM_CLIENTS.get(provider, LLM_CLIENTS["gemini"])
    )
    default_base_url = client_class.default_base_url
    default_model = client_class.default_model

    base_url = _resolve_config("base_url", args, file_config, default_base_url)
    model = _resolve_config("model", args, file_config, default_model)
    api_key = _resolve_config("api_key", args, file_config, None)
    temperature = _resolve_config("temperature", args, file_config, 0.3, float)
    max_tokens = _resolve_config("max_tokens", args, file_config, 3000, int)
    timeout = _resolve_config("timeout", args, file_config, 90, int)
    proxy = _resolve_config("proxy", args, file_config, None)
    debug = file_config.get("DEBUG", False)

    # Pydantic will automatically validate all fields when creating the instance
    config = LLMConfig(
        provider=provider,
        base_url=base_url,
        model=model,
        api_key=api_key,
        temperature=temperature,
        max_tokens=max_tokens,
        timeout=timeout,
        proxy=proxy,
        debug=debug,
    )

    return config
