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
    # If found, discard any preceding "thinking process" or analysis text.
    convention_pattern = re.compile(
        r"^\s*\w+"
        r"(\([\w\-\./]+\))?(!)?: .+",
        re.IGNORECASE | re.MULTILINE,
    )

    match = convention_pattern.search(commit_msg)
    if match:
        return commit_msg[match.start() :].strip()

    return commit_msg.strip()
