import os
import json
from dataclasses import dataclass
from typing import Optional

def load_config_from_file():
    config_path = os.path.expanduser("~/.commity/config.json")
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
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
    api_key: Optional[str] = None
    temperature: float = 0.3
    max_tokens: int = 1500
    timeout: int = 60
    proxy: Optional[str] = None
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
    base_url = _resolve_config("base_url", args, file_config, "https://generativelanguage.googleapis.com")
    model = _resolve_config("model", args, file_config, "gemini-2.5-flash")
    api_key = _resolve_config("api_key", args, file_config, None)
    temperature = _resolve_config("temperature", args, file_config, 0.3, float)
    max_tokens = _resolve_config("max_tokens", args, file_config, 1500, int)
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
