import json
import os
from typing import Any, cast

import jsonc
from pydantic import BaseModel, Field, field_validator, model_validator

from commity.llm import LLM_CLIENTS, BaseLLMClient
from commity.repository_tools import REPOSITORY_TOOL_NAMES

PROVIDERS_REQUIRING_API_KEY = {"gemini", "nvidia", "openai", "openrouter"}


def infer_context_window_tokens(model: str) -> int:
    """Return a conservative context window for common model families."""
    name = model.lower()
    capabilities = (
        (("gemini-2.5", "gemini-1.5", "gpt-4.1"), 1_000_000),
        (("claude",), 200_000),
        (("gpt-4o", "llama-3.1", "llama3.1", "llama-3.2", "llama3.2"), 128_000),
        (("gpt-3.5",), 16_000),
    )
    for patterns, context_window in capabilities:
        if any(pattern in name for pattern in patterns):
            return context_window
    return 32_768


def _parse_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _parse_tools(value: Any) -> list[str] | None:
    if value is None or isinstance(value, list):
        return value
    return [name.strip() for name in str(value).split(",") if name.strip()]


def load_config_from_file() -> dict[str, Any]:
    config_paths = [
        os.path.expanduser("~/.commity/config.jsonc"),
        os.path.expanduser("~/.commity/config.json"),
    ]
    config_path = next((path for path in config_paths if os.path.exists(path)), None)
    if config_path:
        with open(config_path) as f:
            try:
                return cast("dict[str, Any]", jsonc.load(f))
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
        default=0.2, ge=0.0, le=1.0, description="Temperature for generation"
    )
    max_tokens: int = Field(default=512, gt=0, description="Maximum tokens for response")
    context_window_tokens: int = Field(
        default=32768, gt=0, description="Maximum tokens accepted by the model context window"
    )
    timeout: int = Field(default=90, gt=0, description="Request timeout in seconds")
    max_attempts: int = Field(default=3, gt=0, description="Maximum LLM request attempts")
    proxy: str | None = Field(default=None, description="Proxy URL")
    debug: bool = Field(default=False, description="Enable debug mode")
    allow_tools: bool = Field(default=False, description="Allow model repository tool use")
    allowed_tools: list[str] | None = Field(
        default=None,
        description="Repository tools available to the model; null enables all tools",
    )

    @field_validator("allowed_tools")
    @classmethod
    def validate_allowed_tools(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return value
        unknown = set(value) - set(REPOSITORY_TOOL_NAMES)
        if unknown:
            raise ValueError(f"Unknown repository tools: {', '.join(sorted(unknown))}")
        return list(dict.fromkeys(value))

    @model_validator(mode="after")
    def validate_api_key_for_provider(self) -> "LLMConfig":
        """Validate related model settings."""
        if self.provider in PROVIDERS_REQUIRING_API_KEY and not self.api_key:
            raise ValueError(f"API key must be specified for provider '{self.provider}'")
        if self.max_tokens >= self.context_window_tokens:
            raise ValueError("max_tokens must be smaller than context_window_tokens")
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
    temperature = _resolve_config("temperature", args, file_config, 0.2, float)
    max_tokens = _resolve_config("max_tokens", args, file_config, 512, int)
    context_window_tokens = _resolve_config(
        "context_window_tokens",
        args,
        file_config,
        infer_context_window_tokens(model),
        int,
    )
    timeout = _resolve_config("timeout", args, file_config, 90, int)
    max_attempts = _resolve_config("max_attempts", args, file_config, 3, int)
    proxy = _resolve_config("proxy", args, file_config, None)
    debug = _resolve_config("debug", args, file_config, default=False, type_cast=_parse_bool)
    allow_tools = _resolve_config(
        "allow_tools", args, file_config, default=False, type_cast=_parse_bool
    )
    allowed_tools = _resolve_config(
        "allowed_tools", args, file_config, default=None, type_cast=_parse_tools
    )

    # Pydantic will automatically validate all fields when creating the instance
    config = LLMConfig(
        provider=provider,
        base_url=base_url,
        model=model,
        api_key=api_key,
        temperature=temperature,
        max_tokens=max_tokens,
        context_window_tokens=context_window_tokens,
        timeout=timeout,
        max_attempts=max_attempts,
        proxy=proxy,
        debug=debug,
        allow_tools=allow_tools,
        allowed_tools=allowed_tools,
    )

    return config
