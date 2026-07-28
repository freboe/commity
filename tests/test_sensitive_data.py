from unittest.mock import patch

import pytest

from commity.config import LLMConfig
from commity.llm import LLMGenerationError, OllamaClient
from commity.sensitive_data import (
    SensitiveDataMatch,
    find_sensitive_data,
    find_sensitive_data_matches,
)


@pytest.mark.parametrize(
    ("content", "expected"),
    [
        ("OPENAI_API_KEY=sk-proj-abcdefghijklmnopqrstuvwxyz", "OpenAI API key"),
        ("GITHUB_TOKEN=ghp_abcdefghijklmnopqrstuvwxyz123456", "GitHub token"),
        ("-----BEGIN PRIVATE KEY-----", "private key"),
        ("DATABASE_PASSWORD=correct-horse-battery-staple", "credential assignment"),
    ],
)
def test_detects_credential_like_values(content, expected):
    assert expected in find_sensitive_data(content)


def test_ignores_environment_variable_reference():
    assert find_sensitive_data("OPENAI_API_KEY=${OPENAI_API_KEY}") == ()


def test_reports_redacted_match_with_diff_location():
    diff = """diff --git a/tests/secrets.py b/tests/secrets.py
index 0000000..1111111 100644
--- a/tests/secrets.py
+++ b/tests/secrets.py
@@ -0,0 +1,2 @@
+OPENAI_API_KEY=sk-proj-abcdefghijklmnopqrstuvwxyz
+safe = True
"""

    assert find_sensitive_data_matches(diff) == (
        SensitiveDataMatch("OpenAI API key", "sk-pro…wxyz", "tests/secrets.py", 1),
    )


@patch("commity.llm.base.requests.post")
def test_blocks_request_before_network_call(mock_post):
    client = OllamaClient(
        LLMConfig(provider="ollama", base_url="http://localhost:11434", model="llama3")
    )

    with pytest.raises(
        LLMGenerationError,
        match=r"(?s)Sensitive data detected.*OpenAI API key: sk-pro…wxyz \(tests/secrets.py:1\)",
    ):
        client._make_request(  # noqa: SLF001
            "http://localhost:11434/api/generate",
            {
                "prompt": """Git Diff:
diff --git a/tests/secrets.py b/tests/secrets.py
@@ -0,0 +1 @@
+OPENAI_API_KEY=sk-proj-abcdefghijklmnopqrstuvwxyz
"""
            },
            {},
        )

    mock_post.assert_not_called()


@patch("commity.llm.base.requests.post")
def test_allows_only_one_explicitly_confirmed_sensitive_request(mock_post):
    client = OllamaClient(
        LLMConfig(provider="ollama", base_url="http://localhost:11434", model="llama3")
    )
    payload = {"prompt": "OPENAI_API_KEY=sk-proj-abcdefghijklmnopqrstuvwxyz"}
    mock_post.return_value.status_code = 200

    client.allow_sensitive_request_once()
    client._make_request("http://localhost:11434/api/generate", payload, {})  # noqa: SLF001

    with pytest.raises(LLMGenerationError, match="Sensitive data detected"):
        client._make_request("http://localhost:11434/api/generate", payload, {})  # noqa: SLF001

    mock_post.assert_called_once()
