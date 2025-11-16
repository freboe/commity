"""Pytest configuration and fixtures."""

from pathlib import Path
from typing import Any

import pytest


@pytest.fixture
def temp_config_file(tmp_path: Path) -> Path:
    """Create a temporary config file for testing."""
    config_dir = tmp_path / ".commity"
    config_dir.mkdir(parents=True)
    config_file = config_dir / "config.json"
    return config_file


@pytest.fixture
def sample_config_data() -> dict[str, Any]:
    """Sample configuration data."""
    return {
        "PROVIDER": "ollama",
        "BASE_URL": "http://localhost:11434",
        "MODEL": "llama3",
        "TEMPERATURE": 0.5,
        "MAX_TOKENS": 2000,
        "TIMEOUT": 30,
    }


@pytest.fixture
def mock_git_diff() -> str:
    """Sample git diff output."""
    return """diff --git a/commity/config.py b/commity/config.py
index 1234567..abcdefg 100644
--- a/commity/config.py
+++ b/commity/config.py
@@ -1,5 +1,6 @@
 import json
 import os
+from typing import Any

 def load_config():
     pass
"""


@pytest.fixture
def mock_llm_response() -> str:
    """Sample LLM response."""
    return "feat(config): Add type hints to config module"
