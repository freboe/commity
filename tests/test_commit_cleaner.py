"""Tests for commit cleaner utility."""

from commity.utils.commit_cleaner import clean_thinking_process


class TestCleanThinkingProcess:
    """Tests for clean_thinking_process function."""

    def test_clean_thinking_process_standard(self):
        """Test with already clean standard commit message."""
        msg = "feat: simple"
        assert clean_thinking_process(msg) == "feat: simple"

    def test_clean_thinking_process_with_thinking(self):
        """Test removing thinking process text before commit message."""
        msg = """Thinking about this...
    I should change X.
    feat: implement X"""
        assert clean_thinking_process(msg) == "feat: implement X"

    def test_clean_thinking_process_with_scope(self):
        """Test removing thinking process with scoped conventional commit."""
        msg = """<think>analysis</think>
    fix(core): crash fix"""
        assert clean_thinking_process(msg) == "fix(core): crash fix"

    def test_clean_thinking_process_no_match(self):
        """Test with message that doesn't match conventional commit pattern."""
        msg = "just a random message"
        assert clean_thinking_process(msg) == "just a random message"

    def test_clean_thinking_process_breaking_change(self):
        """Test with breaking change convention."""
        msg = """output:
    refactor!: breaking api"""
        assert clean_thinking_process(msg) == "refactor!: breaking api"

    def test_clean_thinking_process_trailing_text(self):
        """Test that text after the commit message start is preserved."""
        msg = """Thinking...
    feat: start
    more lines
    even more lines"""
        expected = """feat: start
    more lines
    even more lines"""
        assert clean_thinking_process(msg) == expected

    def test_clean_thinking_process_explicit_tags(self):
        """Test removing <think> tags even without conventional commit match."""
        msg = """<think>
    deep thoughts
    </think>
    Simple update message"""
        expected = "Simple update message"
        assert clean_thinking_process(msg) == expected

    def test_clean_thinking_process_post_tags(self):
        """Test removing <think> tags that appear after commit message."""
        msg = """feat: new feature
    <think>
    ignored thoughts
    </think>"""
        expected = "feat: new feature"
        assert clean_thinking_process(msg) == expected

    def test_clean_thinking_process_empty(self):
        """Test with empty input."""
        assert clean_thinking_process("") == ""
        assert clean_thinking_process(None) is None

    def test_clean_thinking_process_custom_type(self):
        """Test removing thinking process with custom commit type."""
        msg = """<think>planning</think>
    infra: update terraform"""
        assert clean_thinking_process(msg) == "infra: update terraform"
