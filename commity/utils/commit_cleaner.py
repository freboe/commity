"""Utilities for cleaning and processing commit messages."""

import re


def clean_thinking_process(commit_msg: str) -> str:
    """Remove thinking process and analysis from commit message.

    Args:
        commit_msg: The raw commit message that may contain thinking process.

    Returns:
        The cleaned commit message with thinking process removed.

    """
    if not commit_msg:
        return commit_msg

    # Remove <think>...</think> blocks
    commit_msg = re.sub(
        r"<think>.*?</think>", "", commit_msg, flags=re.DOTALL | re.IGNORECASE
    ).strip()

    # Check for Conventional Commit format (e.g., feat: ..., fix(scope): ...)
    # Support optional emoji prefix (e.g., ✨ feat: ...)
    # If found, discard any preceding "thinking process" or analysis text.
    # Pattern explanation:
    # 1. Start of line (multi-line mode)
    # 2. Optional: Any character that is not a newline (to match emojis) followed by whitespace
    # 3. Word characters (type)
    # 4. Optional: (scope)
    # 5. Optional: !
    # 6. Colon and space
    # 7. Rest of the line
    convention_pattern = re.compile(
        r"^\s*(?:[^\"'•\*\-\w\n\r]+\s+)?([a-z0-9_]+)(\([\w\-\./]+\))?(!)?: .+",
        re.MULTILINE,
    )

    match = convention_pattern.search(commit_msg)
    if match:
        return commit_msg[match.start() :].strip()

    return commit_msg.strip()
