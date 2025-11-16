"""Fixtures and utilities for integration tests."""

import os
import subprocess
from collections.abc import Generator
from pathlib import Path

import pytest
import requests

from commity.config import LLMConfig


def is_ollama_available() -> bool:
    """Check if Ollama is running and accessible."""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=2)
        return response.status_code == 200
    except Exception:
        return False


def is_git_available() -> bool:
    """Check if git is available."""
    try:
        subprocess.run(["git", "--version"], capture_output=True, check=True, timeout=2)
        return True
    except Exception:
        return False


@pytest.fixture()
def temp_git_repo(tmp_path: Path) -> Generator[Path, None, None]:
    """Create a temporary git repository for testing."""
    repo_dir = tmp_path / "test_repo"
    repo_dir.mkdir()

    # Initialize git repo
    subprocess.run(["git", "init"], cwd=repo_dir, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=repo_dir,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=repo_dir,
        check=True,
        capture_output=True,
    )

    # Create initial commit
    readme = repo_dir / "README.md"
    readme.write_text("# Test Repository\n")
    subprocess.run(["git", "add", "README.md"], cwd=repo_dir, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "Initial commit"],
        cwd=repo_dir,
        check=True,
        capture_output=True,
    )

    # Save current directory
    original_dir = Path.cwd()

    # Change to repo directory
    os.chdir(repo_dir)

    try:
        yield repo_dir
    finally:
        # Restore original directory
        os.chdir(original_dir)


@pytest.fixture()
def ollama_config() -> LLMConfig:
    """Create a config for Ollama testing."""
    return LLMConfig(
        provider="ollama",
        base_url="http://localhost:11434",
        model="gpt-oss:20b",  # Use locally installed model
        temperature=0.7,
        max_tokens=500,  # Limit tokens for faster tests
        timeout=30,
    )


@pytest.fixture()
def sample_diff() -> str:
    """Sample git diff for testing."""
    return """diff --git a/src/utils.py b/src/utils.py
index abc123..def456 100644
--- a/src/utils.py
+++ b/src/utils.py
@@ -1,5 +1,8 @@
 def calculate(x, y):
-    return x + y
+    \"\"\"Calculate the sum of two numbers.\"\"\"
+    if not isinstance(x, (int, float)) or not isinstance(y, (int, float)):
+        raise TypeError("Arguments must be numbers")
+    return x + y

 def process_data(data):
     return [item * 2 for item in data]
"""
