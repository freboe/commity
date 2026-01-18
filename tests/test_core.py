"""Tests for core module."""

import subprocess
from unittest.mock import Mock, patch

from commity.core import generate_prompt, get_git_diff


class TestGetGitDiff:
    """Tests for get_git_diff function."""

    @patch("commity.core.subprocess.run")
    def test_get_git_diff_success(self, mock_run):
        """Test successful git diff retrieval."""
        mock_result = Mock()
        mock_result.stdout = "diff --git a/file.py b/file.py\n+new line"
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        result = get_git_diff()
        assert result == "diff --git a/file.py b/file.py\n+new line"
        mock_run.assert_called_once_with(
            ["git", "diff", "--staged"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
        )

    @patch("commity.core.subprocess.run")
    def test_get_git_diff_empty(self, mock_run):
        """Test git diff with no changes."""
        mock_result = Mock()
        mock_result.stdout = "  \n  "
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        result = get_git_diff()
        assert result == ""

    @patch("commity.core.subprocess.run")
    def test_get_git_diff_error(self, mock_run, capsys):
        """Test git diff with error."""
        mock_run.side_effect = subprocess.CalledProcessError(
            returncode=128,
            cmd=["git", "diff", "--staged"],
            stderr="fatal: not a git repository",
        )

        result = get_git_diff()
        assert result == ""
        captured = capsys.readouterr()
        assert "[Git Error]" in captured.out

    @patch("commity.core.subprocess.run")
    def test_get_git_diff_unexpected_error(self, mock_run, capsys):
        """Test git diff with unexpected error."""
        mock_run.side_effect = Exception("Unexpected error")

        result = get_git_diff()
        assert result == ""
        captured = capsys.readouterr()
        assert "[Git Error]" in captured.out
        assert "unexpected error" in captured.out


class TestGeneratePrompt:
    """Tests for generate_prompt function."""

    def test_generate_prompt_basic(self):
        """Test basic prompt generation."""
        diff = "diff --git a/test.py b/test.py\n+print('hello')"
        prompt = generate_prompt(diff)

        assert "Git Diff:" in prompt
        assert diff in prompt
        assert "commit message" in prompt

    def test_generate_prompt_with_language(self):
        """Test prompt generation with custom language."""
        diff = "diff --git a/test.py b/test.py\n+print('hello')"
        prompt = generate_prompt(diff, language="zh")

        assert "zh" in prompt
        assert diff in prompt

    def test_generate_prompt_with_emoji(self):
        """Test prompt generation with emoji enabled."""
        diff = "diff --git a/test.py b/test.py\n+print('hello')"
        prompt = generate_prompt(diff, emoji=True)

        assert "emoji" in prompt.lower()
        assert "✨" in prompt  # feat emoji
        assert "🐛" in prompt  # fix emoji
        assert "type(scope): <emoji>" in prompt

    def test_generate_prompt_without_emoji(self):
        """Test prompt generation without emoji."""
        diff = "diff --git a/test.py b/test.py\n+print('hello')"
        prompt = generate_prompt(diff, emoji=False)

        assert "Do not include emojis" in prompt
        # Should not have emoji mapping
        assert "✨" not in prompt

    def test_generate_prompt_conventional_type(self):
        """Test prompt generation with conventional commits."""
        diff = "diff --git a/test.py b/test.py\n+print('hello')"
        prompt = generate_prompt(diff, type_="conventional")

        assert "Conventional Commits" in prompt
        assert "feat:" in prompt
        assert "fix:" in prompt
        assert "type(scope): description" in prompt

    def test_generate_prompt_custom_max_subject_chars(self):
        """Test prompt generation with custom max subject chars."""
        diff = "diff --git a/test.py b/test.py\n+print('hello')"
        prompt = generate_prompt(diff, max_subject_chars=72)

        assert "≤72 characters" in prompt

    def test_generate_prompt_all_options(self):
        """Test prompt generation with all options."""
        diff = "diff --git a/test.py b/test.py\n+print('hello')"
        prompt = generate_prompt(
            diff,
            language="zh",
            emoji=True,
            type_="conventional",
            max_subject_chars=60,
        )

        assert "zh" in prompt
        assert "emoji" in prompt.lower()
        assert "Conventional Commits" in prompt
        assert "≤60 characters" in prompt
        assert diff in prompt

    def test_generate_prompt_empty_diff(self):
        """Test prompt generation with empty diff."""
        prompt = generate_prompt("", language="en", emoji=True)

        assert "Git Diff:" in prompt
        assert "commit message" in prompt
        # Should still have the full prompt structure

    def test_generate_prompt_multiline_diff(self):
        """Test prompt generation with multiline diff."""
        diff = """diff --git a/file1.py b/file1.py
index 1234567..abcdefg 100644
--- a/file1.py
+++ b/file1.py
@@ -1,5 +1,6 @@
 import os
+import sys

 def main():
-    print('old')
+    print('new')
"""
        prompt = generate_prompt(diff)

        assert diff in prompt
        assert "import sys" in prompt
        assert "print('new')" in prompt
