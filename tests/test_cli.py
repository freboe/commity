"""Tests for CLI module."""

from commity.utils.commit_cleaner import clean_thinking_process


class TestCleanThinkingProcess:
    """Tests for clean_thinking_process function."""

    def test_clean_thinking_with_analysis(self):
        """Test cleaning commit message with thinking process."""
        commit_msg = """Let me analyze the git diff to understand what changes were made:

 1 tests/test_base_llm.py: +116 lines added - Tests for BaseLLMClient

The main change is:
 • A large test file was split into multiple smaller files

🔨 refactor(tests): split monolithic test_llm.py into modular client tests

Refactored the monolithic test_llm.py file into separate test modules."""
        result = clean_thinking_process(commit_msg)
        assert "Let me analyze" not in result
        assert "The main change is" not in result
        assert "1 tests/test_base_llm.py" not in result
        assert "🔨 refactor(tests):" in result
        assert "Refactored the monolithic" in result

    def test_clean_thinking_with_let_me_craft(self):
        """Test cleaning commit message with 'Let me craft' phrase."""
        commit_msg = """Let me craft the commit message:

Type: refactor
Scope: tests

🔨 refactor(tests): split test files"""
        result = clean_thinking_process(commit_msg)
        assert "Let me craft" not in result
        assert "Type: refactor" not in result
        assert "Scope: tests" not in result
        assert "🔨 refactor(tests):" in result

    def test_clean_thinking_with_numbered_list(self):
        """Test cleaning numbered analysis list."""
        commit_msg = """Looking at the diff:

 1 tests/test_base_llm.py: +116 lines
 2 tests/test_factory.py: +84 lines

🔨 refactor(tests): split test files"""
        result = clean_thinking_process(commit_msg)
        assert "Looking at" not in result
        assert "1 tests/test_base_llm.py" not in result
        assert "2 tests/test_factory.py" not in result
        assert "🔨 refactor(tests):" in result

    def test_clean_thinking_with_bullet_points(self):
        """Test cleaning bullet point analysis."""
        commit_msg = """This appears to be a refactoring:

 • A large test file was split
 • New test files were created

🔨 refactor(tests): split test files"""
        result = clean_thinking_process(commit_msg)
        assert "This appears to be" not in result
        assert "• A large test file" not in result
        assert "🔨 refactor(tests):" in result

    def test_clean_thinking_preserves_valid_commit(self):
        """Test that valid commit messages are preserved."""
        commit_msg = """🔨 refactor(tests): split monolithic test_llm.py into modular client tests

Refactored the monolithic test_llm.py file into separate test modules."""
        result = clean_thinking_process(commit_msg)
        assert result == commit_msg

    def test_clean_thinking_with_mixed_content(self):
        """Test cleaning when thinking process is mixed with commit message."""
        commit_msg = """Let me analyze this:

I'll focus on the key changes.

🔨 refactor(tests): split test files

This improves organization."""
        result = clean_thinking_process(commit_msg)
        assert "Let me analyze" not in result
        assert "I'll focus on" not in result
        assert "🔨 refactor(tests):" in result
        assert "This improves organization" in result

    def test_clean_thinking_empty_input(self):
        """Test cleaning empty input."""
        result = clean_thinking_process("")
        assert result == ""

    def test_clean_thinking_only_thinking(self):
        """Test when input contains only thinking process."""
        commit_msg = """Let me analyze the git diff.
Looking at the changes.
This appears to be a refactoring."""
        result = clean_thinking_process(commit_msg)
        # Should return original if everything is removed
        assert result == commit_msg

    def test_clean_thinking_with_emoji_prefix(self):
        """Test that commit messages starting with emoji are preserved."""
        commit_msg = """✨ feat: add new feature

Add a new feature to the system."""
        result = clean_thinking_process(commit_msg)
        assert result == commit_msg

    def test_clean_thinking_with_type_prefix(self):
        """Test that commit messages starting with type prefix are preserved."""
        commit_msg = """feat: add new feature

Add a new feature to the system."""
        result = clean_thinking_process(commit_msg)
        assert result == commit_msg

    def test_clean_thinking_with_meta_analysis(self):
        """Test cleaning commit message with meta-analysis about the message itself."""
        commit_msg = """Let me analyze this Git diff to generate a proper commit message.

 • Multiple test files are being added

The type should be:
 • test - because we're adding/modifying tests

Wait, looking more carefully:
 • test_llm.py is being completely removed

The emoji for test is 🚨.

Subject line should be ≤60 characters, lowercase type prefix, no period at end.
 • "🚨 test: refactor test suite into separate client-specific test files"
That's about 66 characters, too long. Let me shorten:
 • "🚨 test: split monolithic test file into client-specific tests"
That's about 62 characters, still a bit long
 • "🚨 test: reorganize tests into separate client test files"
That's 53 characters - good!

🚨 test: reorganize tests into separate client test files

Split monolithic test_llm.py into dedicated test files."""
        result = clean_thinking_process(commit_msg)
        assert "Let me analyze" not in result
        assert "The type should be" not in result
        assert "Wait, looking more carefully" not in result
        assert "That's about" not in result
        assert "too long" not in result
        assert "still a bit long" not in result
        assert "That's 53 characters" not in result
        assert "🚨 test: reorganize tests" in result
        assert "Split monolithic test_llm.py" in result
