"""Tests for config module."""

import json
import os
from typing import ClassVar

# from pathlib import Path
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from commity.config import (
    LLMConfig,
    get_llm_config,
    infer_context_window_tokens,
    load_config_from_file,
)


class TestLLMConfig:
    """Tests for LLMConfig model."""

    def test_valid_config(self):
        """Test creating a valid config."""
        config = LLMConfig(
            provider="ollama",
            base_url="http://localhost:11434",
            model="llama3",
        )
        assert config.provider == "ollama"
        assert config.base_url == "http://localhost:11434"
        assert config.model == "llama3"
        assert config.temperature == 0.2  # default
        assert config.max_tokens == 512  # default
        assert config.context_window_tokens == 32768
        assert config.allow_tools is False
        assert config.allowed_tools is None

    def test_config_with_all_fields(self):
        """Test creating config with all fields."""
        config = LLMConfig(
            provider="openai",
            base_url="https://api.openai.com/v1",
            model="gpt-3.5-turbo",
            api_key="test-key",
            temperature=0.7,
            max_tokens=2000,
            timeout=30,
            proxy="http://proxy:8080",
            debug=True,
            allow_tools=True,
            allowed_tools=["read_file", "get_commit"],
        )
        assert config.provider == "openai"
        assert config.api_key == "test-key"
        assert config.temperature == 0.7
        assert config.max_tokens == 2000
        assert config.timeout == 30
        assert config.proxy == "http://proxy:8080"
        assert config.debug is True
        assert config.allow_tools is True
        assert config.allowed_tools == ["read_file", "get_commit"]

    def test_rejects_unknown_repository_tools(self):
        with pytest.raises(ValidationError, match="Unknown repository tools: write_file"):
            LLMConfig(
                provider="ollama",
                base_url="http://localhost:11434",
                model="llama3",
                allowed_tools=["read_file", "write_file"],
            )

    def test_temperature_validation(self):
        """Test temperature range validation."""
        # Valid temperatures
        LLMConfig(provider="ollama", base_url="http://localhost", model="llama3", temperature=0.0)
        LLMConfig(provider="ollama", base_url="http://localhost", model="llama3", temperature=1.0)
        LLMConfig(provider="ollama", base_url="http://localhost", model="llama3", temperature=0.5)

        # Invalid temperatures
        with pytest.raises(ValidationError, match="less than or equal to 1"):
            LLMConfig(
                provider="ollama", base_url="http://localhost", model="llama3", temperature=1.5
            )

        with pytest.raises(ValidationError, match="greater than or equal to 0"):
            LLMConfig(
                provider="ollama", base_url="http://localhost", model="llama3", temperature=-0.1
            )

    def test_max_tokens_validation(self):
        """Test max_tokens validation."""
        # Valid
        LLMConfig(provider="ollama", base_url="http://localhost", model="llama3", max_tokens=100)

        # Invalid - must be > 0
        with pytest.raises(ValidationError, match="greater than 0"):
            LLMConfig(provider="ollama", base_url="http://localhost", model="llama3", max_tokens=0)

        with pytest.raises(ValidationError, match="greater than 0"):
            LLMConfig(provider="ollama", base_url="http://localhost", model="llama3", max_tokens=-1)

    def test_max_tokens_must_be_smaller_than_context_window(self):
        with pytest.raises(
            ValidationError,
            match="max_tokens must be smaller than context_window_tokens",
        ):
            LLMConfig(
                provider="ollama",
                base_url="http://localhost",
                model="llama3",
                max_tokens=1024,
                context_window_tokens=1024,
            )

    def test_timeout_validation(self):
        """Test timeout validation."""
        # Valid
        LLMConfig(provider="ollama", base_url="http://localhost", model="llama3", timeout=60)

        # Invalid - must be > 0
        with pytest.raises(ValidationError, match="greater than 0"):
            LLMConfig(provider="ollama", base_url="http://localhost", model="llama3", timeout=0)

    def test_api_key_required_for_openai(self):
        """Test that API key is required for OpenAI."""
        with pytest.raises(ValidationError, match="API key must be specified"):
            LLMConfig(
                provider="openai",
                base_url="https://api.openai.com/v1",
                model="gpt-3.5-turbo",
            )

        # Should work with API key
        config = LLMConfig(
            provider="openai",
            base_url="https://api.openai.com/v1",
            model="gpt-3.5-turbo",
            api_key="test-key",
        )
        assert config.api_key == "test-key"

    def test_api_key_required_for_gemini(self):
        """Test that API key is required for Gemini."""
        with pytest.raises(ValidationError, match="API key must be specified"):
            LLMConfig(
                provider="gemini",
                base_url="https://generativelanguage.googleapis.com",
                model="gemini-2.5-flash",
            )

    def test_api_key_required_for_openrouter(self):
        """Test that API key is required for OpenRouter."""
        with pytest.raises(ValidationError, match="API key must be specified"):
            LLMConfig(
                provider="openrouter",
                base_url="https://openrouter.ai/api/v1",
                model="qwen/qwen3-coder:free",
            )

    def test_api_key_required_for_nvidia(self):
        """Test that API key is required for NVIDIA."""
        with pytest.raises(ValidationError, match="API key must be specified"):
            LLMConfig(
                provider="nvidia",
                base_url="https://integrate.api.nvidia.com/v1",
                model="nvidia/llama-3.1-70b-instruct",
            )

        # Should work with API key
        config = LLMConfig(
            provider="nvidia",
            base_url="https://integrate.api.nvidia.com/v1",
            model="nvidia/llama-3.1-70b-instruct",
            api_key="test-key",
        )
        assert config.api_key == "test-key"

    def test_api_key_not_required_for_ollama(self):
        """Test that API key is not required for Ollama."""
        config = LLMConfig(
            provider="ollama",
            base_url="http://localhost:11434",
            model="llama3",
        )
        assert config.api_key is None


class TestLoadConfigFromFile:
    """Tests for load_config_from_file function."""

    def test_load_existing_config(self, temp_config_file, sample_config_data):
        """Test loading an existing config file."""
        temp_config_file.write_text(json.dumps(sample_config_data))

        with patch("commity.config.os.path.expanduser", return_value=str(temp_config_file)):
            config = load_config_from_file()
            assert config == sample_config_data

    def test_load_jsonc_config(self, tmp_path):
        """Test loading comments and trailing commas from a JSONC file."""
        config_file = tmp_path / "config.jsonc"
        config_file.write_text(
            """
            {
                // Keep URLs and comment markers inside strings unchanged.
                "PROVIDER": "ollama",
                "BASE_URL": "http://localhost:11434/*api*/",
                "ALLOWED_TOOLS": [
                    "read_file",
                ],
                /* A block comment may span
                   multiple lines. */
            }
            """
        )

        with patch("commity.config.os.path.expanduser", return_value=str(config_file)):
            config = load_config_from_file()

        assert config == {
            "PROVIDER": "ollama",
            "BASE_URL": "http://localhost:11434/*api*/",
            "ALLOWED_TOOLS": ["read_file"],
        }

    def test_jsonc_takes_priority_over_json(self, tmp_path):
        json_file = tmp_path / "config.json"
        jsonc_file = tmp_path / "config.jsonc"
        json_file.write_text('{"MODEL": "from-json"}')
        jsonc_file.write_text('{"MODEL": "from-jsonc"}')

        def resolve_config_path(path):
            return str(jsonc_file if path.endswith(".jsonc") else json_file)

        with patch("commity.config.os.path.expanduser", side_effect=resolve_config_path):
            config = load_config_from_file()

        assert config["MODEL"] == "from-jsonc"

    def test_falls_back_to_json(self, tmp_path):
        json_file = tmp_path / "config.json"
        json_file.write_text('{"MODEL": "from-json"}')

        def resolve_config_path(path):
            return str(tmp_path / "missing.jsonc") if path.endswith(".jsonc") else str(json_file)

        with patch("commity.config.os.path.expanduser", side_effect=resolve_config_path):
            config = load_config_from_file()

        assert config["MODEL"] == "from-json"

    def test_load_nonexistent_config(self, tmp_path):
        """Test loading when config file doesn't exist."""
        nonexistent = tmp_path / "nonexistent.json"
        with patch("commity.config.os.path.expanduser", return_value=str(nonexistent)):
            config = load_config_from_file()
            assert config == {}

    def test_load_invalid_json(self, temp_config_file, capsys):
        """Test loading invalid JSON file."""
        temp_config_file.write_text("{ invalid json }")

        with patch("commity.config.os.path.expanduser", return_value=str(temp_config_file)):
            config = load_config_from_file()
            assert config == {}
            captured = capsys.readouterr()
            assert "Warning: Could not decode JSON" in captured.out


class TestGetLLMConfig:
    """Tests for get_llm_config function."""

    def test_config_from_defaults(self):
        """Test config with only defaults."""

        class Args:
            provider = None
            base_url = None
            model = None
            api_key = "test-key"  # Required for gemini
            temperature = None
            max_tokens = None
            timeout = None
            proxy = None

        with (
            patch("commity.config.load_config_from_file", return_value={}),
            patch.dict(os.environ, {}, clear=True),
        ):
            config = get_llm_config(Args())
            assert config.provider == "gemini"  # default
            assert config.temperature == 0.2
            assert config.max_tokens == 512
            assert config.context_window_tokens == 1_000_000
            assert config.timeout == 90
            assert config.allow_tools is False
            assert config.allowed_tools is None

    def test_config_from_args(self):
        """Test config from command line arguments."""

        class Args:
            provider = "ollama"
            base_url = "http://test:11434"
            model = "test-model"
            api_key = None
            temperature = 0.8
            max_tokens = 1500
            context_window_tokens = 16384
            timeout = 45
            proxy = "http://proxy:8080"
            allow_tools = True
            allowed_tools: ClassVar = ["read_file", "get_commit"]

        with (
            patch("commity.config.load_config_from_file", return_value={}),
            patch.dict(os.environ, {}, clear=True),
        ):
            config = get_llm_config(Args())
            assert config.provider == "ollama"
            assert config.base_url == "http://test:11434"
            assert config.model == "test-model"
            assert config.temperature == 0.8
            assert config.max_tokens == 1500
            assert config.context_window_tokens == 16384
            assert config.timeout == 45
            assert config.proxy == "http://proxy:8080"
            assert config.allow_tools is True
            assert config.allowed_tools == ["read_file", "get_commit"]

    def test_config_from_env(self):
        """Test config from environment variables."""

        class Args:
            provider = None
            base_url = None
            model = None
            api_key = None
            temperature = None
            max_tokens = None
            context_window_tokens = None
            timeout = None
            proxy = None

        env_vars = {
            "COMMITY_PROVIDER": "ollama",
            "COMMITY_BASE_URL": "http://env:11434",
            "COMMITY_MODEL": "env-model",
            "COMMITY_TEMPERATURE": "0.6",
            "COMMITY_MAX_TOKENS": "2500",
            "COMMITY_CONTEXT_WINDOW_TOKENS": "8192",
            "COMMITY_DEBUG": "true",
            "COMMITY_TIMEOUT": "50",
            "COMMITY_ALLOW_TOOLS": "true",
            "COMMITY_ALLOWED_TOOLS": "read_file, get_staged_diff",
        }

        with (
            patch("commity.config.load_config_from_file", return_value={}),
            patch.dict(os.environ, env_vars, clear=True),
        ):
            config = get_llm_config(Args())
            assert config.provider == "ollama"
            assert config.base_url == "http://env:11434"
            assert config.model == "env-model"
            assert config.temperature == 0.6
            assert config.max_tokens == 2500
            assert config.context_window_tokens == 8192
            assert config.debug is True
            assert config.timeout == 50
            assert config.allow_tools is True
            assert config.allowed_tools == ["read_file", "get_staged_diff"]

    def test_config_priority_args_over_env(self):
        """Test that args have priority over environment variables."""

        class Args:
            provider = "ollama"
            base_url = "http://args:11434"
            model = None
            api_key = None
            temperature = None
            max_tokens = None
            timeout = None
            proxy = None

        env_vars = {
            "COMMITY_PROVIDER": "openai",
            "COMMITY_BASE_URL": "http://env:11434",
            "COMMITY_MODEL": "env-model",
        }

        with (
            patch("commity.config.load_config_from_file", return_value={}),
            patch.dict(os.environ, env_vars, clear=True),
        ):
            config = get_llm_config(Args())
            assert config.provider == "ollama"  # from args
            assert config.base_url == "http://args:11434"  # from args
            assert config.model == "env-model"  # from env


@pytest.mark.parametrize(
    ("model", "expected"),
    [
        ("gemini-2.5-flash", 1_000_000),
        ("gpt-4o-mini", 128_000),
        ("claude-3.5-sonnet", 200_000),
        ("gpt-3.5-turbo", 16_000),
        ("unknown-model", 32_768),
    ],
)
def test_infer_context_window_tokens(model, expected):
    assert infer_context_window_tokens(model) == expected
