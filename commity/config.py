import json
import os
from dataclasses import dataclass

from commity.llm import LLM_CLIENTS


def load_config_from_file():
    config_path = os.path.expanduser("~/.commity/config.json")
    if os.path.exists(config_path):
        with open(config_path) as f:
            try:
                return json.load(f)
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

def _resolve_config(arg_name, args, file_config, default, type_cast=None):
    """Helper to resolve config values from args, env, or file."""
    env_key = f"COMMITY_{arg_name.upper()}"
    file_key = arg_name.upper()
    args_val = getattr(args, arg_name, None)

    value = args_val or os.getenv(env_key) or file_config.get(file_key) or default

    if value is not None and type_cast:
        return type_cast(value)
    return value

def get_llm_config(args) -> LLMConfig:
    file_config = load_config_from_file()

    provider = _resolve_config("provider", args, file_config, "gemini")

    client_class = LLM_CLIENTS.get(provider, LLM_CLIENTS["gemini"])
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

    return LLMConfig(
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
