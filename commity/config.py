import json
import os
from dataclasses import dataclass
from typing import Any, cast

from commity.llm import LLM_CLIENTS, BaseLLMClient


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


@dataclass
class LLMConfig:
    provider: str
    base_url: str
    model: str
    api_key: str | None = None
    temperature: float = 0.3
    max_tokens: int = 3000
    timeout: int = 60
    proxy: str | None = None
    debug: bool = False


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


def _validate_config(config: LLMConfig) -> None:
    """Validate the LLM configuration."""
    if not config.provider:
        raise ValueError("Provider must be specified")

    if not config.base_url:
        raise ValueError("Base URL must be specified")

    if not config.model:
        raise ValueError("Model must be specified")

    if config.temperature < 0.0 or config.temperature > 1.0:
        raise ValueError("Temperature must be between 0.0 and 1.0")

    if config.max_tokens <= 0:
        raise ValueError("Max tokens must be greater than 0")

    if config.timeout <= 0:
        raise ValueError("Timeout must be greater than 0")


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
    timeout = _resolve_config("timeout", args, file_config, 60, int)
    proxy = _resolve_config("proxy", args, file_config, None)
    debug = file_config.get("DEBUG", False)

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

    _validate_config(config)

    return config
