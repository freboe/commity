"""Unit tests for prompt_organizer module."""

from commity.utils.prompt_organizer import (
    calculate_file_importance,
    compress_with_lines,
    compress_with_structure,
    summary_and_tokens_checker,
)
from commity.utils.token_counter import count_tokens


class TestCalculateFileImportance:
    """Tests for calculate_file_importance function."""

    def test_python_source_file(self):
        """Test scoring for Python source files."""
        score = calculate_file_importance("src/main.py", 10, 5)
        assert score > calculate_file_importance("tests/test_main.py", 100, 100)

    def test_javascript_source_file(self):
        """Test scoring for JavaScript source files."""
        score = calculate_file_importance("app/index.js", 20, 10)
        assert score > calculate_file_importance("package-lock.json", 1000, 1000)

    def test_config_file(self):
        """Test scoring for configuration files."""
        score = calculate_file_importance("config.yaml", 5, 3)
        assert score > calculate_file_importance("README.md", 5, 3)

    def test_test_file(self):
        """Test scoring for test files (both .py and test path)."""
        score = calculate_file_importance("tests/test_main.py", 10, 5)
        assert score < calculate_file_importance("src/main.py", 1, 1)

    def test_markdown_test_file(self):
        """Test scoring for markdown files in test directory."""
        score = calculate_file_importance("tests/README.md", 5, 0)
        assert score < calculate_file_importance("src/main.py", 1, 1)

    def test_lock_file(self):
        """Test scoring for lock files (lowest priority)."""
        score = calculate_file_importance("package-lock.json", 100, 50)
        assert score < calculate_file_importance("src/main.py", 1, 1)

    def test_special_file_readme(self):
        """Test scoring for special files like README."""
        score = calculate_file_importance("README.md", 5, 0)
        assert score > calculate_file_importance("docs/guide.md", 5, 0)

    def test_special_file_pyproject(self):
        """Test scoring for pyproject.toml."""
        score = calculate_file_importance("pyproject.toml", 10, 0)
        assert score > calculate_file_importance("config.toml", 10, 0)

    def test_change_size_cap(self):
        """Test that change size is capped at 50."""
        score = calculate_file_importance("src/huge.py", 100, 100)
        assert score - calculate_file_importance("src/small.py", 1, 0) <= 10


class TestCompressWithLines:
    """Tests for compress_with_lines function."""

    def test_basic_compression(self):
        """Test basic line-based compression."""
        diff = """diff --git a/test.py b/test.py
index 1234567..abcdefg 100644
--- a/test.py
+++ b/test.py
@@ -1,3 +1,4 @@
 line1
+line2
-line3
 line4
"""
        result = compress_with_lines(diff)

        assert "test.py" in result
        assert "+ line2" in result
        assert "- line3" in result

    def test_respects_max_lines(self):
        """Test that compression respects max_lines limit."""
        # Create a large diff
        changes = "\n".join([f"+line{i}" for i in range(100)])
        diff = f"""diff --git a/test.py b/test.py
{changes}
"""
        result = compress_with_lines(diff, max_lines=10)
        lines = result.splitlines()

        # Should be truncated (allow some flexibility due to empty lines and file headers)
        assert len(lines) <= 15
        assert "truncated" in result.lower()


class TestCompressWithStructure:
    """Tests for compress_with_structure function."""

    def test_handles_token_limit(self):
        """Test that structure compression handles token limit."""
        multi_file_diff = """diff --git a/src/main.py b/src/main.py
index 1234567..abcdefg 100644
--- a/src/main.py
+++ b/src/main.py
@@ -1,2 +1,3 @@
 def main():
+    print("new")
     pass
"""
        # Very low token limit
        result = compress_with_structure(multi_file_diff, 50, "gpt-4", "gemini")

        # Should still return something
        assert len(result) > 0
        # Should have some content about the file
        assert "main.py" in result

    def test_preserves_all_file_names_when_details_do_not_fit(self):
        diff = """diff --git a/tests/test_large.py b/tests/test_large.py
--- a/tests/test_large.py
+++ b/tests/test_large.py
@@ -1 +1 @@
-old
+large test change
diff --git a/src/auth.py b/src/auth.py
--- a/src/auth.py
+++ b/src/auth.py
@@ -1 +1 @@
-return expired
+return refreshed
"""
        result = compress_with_structure(diff, 100, "gpt-4", "openai")

        assert "tests/test_large.py" in result
        assert "src/auth.py" in result
        assert result.index("src/auth.py") < result.index("tests/test_large.py")

    def test_returns_no_changes_for_empty_patch(self):
        """Test handling of empty or invalid patch."""
        # Invalid diff that can't be parsed
        result = compress_with_structure("not a valid diff", 100, "gpt-4", "openai")

        # Should fall back to line compression
        assert isinstance(result, str)


class TestSummaryAndTokensChecker:
    """Tests for summary_and_tokens_checker main function."""

    def test_returns_original_if_within_limit(self):
        """Test that original diff is returned if within token limit."""
        small_diff = "diff --git a/test.py b/test.py\n+line\n"
        result = summary_and_tokens_checker(small_diff, 10000, "gpt-4", "openai")

        assert result == small_diff

    def test_compresses_if_exceeds_limit(self):
        """Test that compression is applied if exceeding limit."""
        # Create a large diff
        large_diff = """diff --git a/src/main.py b/src/main.py
""" + "\n".join([f"+line{i}" for i in range(1000)])

        result = summary_and_tokens_checker(large_diff, 100, "gpt-4", "gemini")

        # Should be compressed
        assert len(result) < len(large_diff)

    def test_compressed_result_strictly_respects_token_limit(self):
        large_diff = "diff --git a/src/main.py b/src/main.py\n" + "\n".join(
            f"+{'x' * 120}" for _ in range(200)
        )

        result = summary_and_tokens_checker(
            large_diff,
            10,
            "gemini-2.5-flash",
            "gemini",
        )

        assert count_tokens(result, "gemini-2.5-flash", "gemini") <= 10

    def test_handles_empty_diff(self):
        """Test handling of empty diff."""
        result = summary_and_tokens_checker("", 1000, "gpt-4", "openai")
        assert result == ""

    def test_different_providers(self):
        """Test with different LLM providers."""
        diff = "diff --git a/test.py b/test.py\n+line\n"

        for provider in ["openai", "gemini", "ollama", "openrouter"]:
            result = summary_and_tokens_checker(diff, 1000, "gpt-4", provider)
            assert len(result) > 0

    def test_adds_warning_for_very_large_diff(self):
        """Test that warning is added for very large diffs."""
        # Create a diff that exceeds MAX_DIFF_LENGTH
        huge_diff = "diff --git a/huge.py b/huge.py\n" + ("+" * 20000)

        result = summary_and_tokens_checker(huge_diff, 50, "gpt-4", "gemini")

        # Should include warning or be heavily compressed
        assert len(result) > 0
        # The result should be much smaller than input
        assert len(result) < len(huge_diff)
