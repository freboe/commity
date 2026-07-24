"""Tests for generated commit message parsing and validation."""

import pytest

from commity.commit_message import (
    CommitMessageError,
    parse_generated_commit,
    validate_commit_message,
)


def test_renders_structured_commit_message():
    raw = """{
        "type": "fix",
        "scope": "auth",
        "subject": "preserve refreshed sessions",
        "body": ["Reuse refreshed credentials when rebuilding the session."],
        "breaking": false
    }"""

    result = parse_generated_commit(raw, max_subject_chars=60, emoji=False)

    assert result.startswith("fix(auth): preserve refreshed sessions")
    assert "Reuse refreshed credentials" in result


def test_adds_emoji_deterministically():
    raw = '{"type":"feat","scope":"","subject":"add retry controls","body":[]}'

    result = parse_generated_commit(raw, max_subject_chars=50, emoji=True)

    assert result == "feat: ✨ add retry controls"


def test_accepts_legacy_conventional_commit():
    result = parse_generated_commit(
        "fix(core): handle empty responses", max_subject_chars=50, emoji=False
    )

    assert result == "fix(core): handle empty responses"


@pytest.mark.parametrize(
    "message",
    [
        "change(core): use unsupported type",
        "fix(core) missing colon",
        "fix: subject ends with.",
    ],
)
def test_rejects_invalid_plain_text(message):
    with pytest.raises(CommitMessageError):
        validate_commit_message(message, 50)


def test_compacts_generated_subject_to_limit():
    result = parse_generated_commit(
        '{"type":"fix","scope":"core","subject":"describe a very long correction","body":[]}',
        max_subject_chars=20,
        emoji=False,
    )

    assert result == "fix(core): describe"
    assert len(result.splitlines()[0]) <= 20


def test_compacts_generated_subject_with_emoji_and_preserves_body():
    raw = """{
        "type": "refactor",
        "scope": "prompt",
        "subject": "improve generated commit message accuracy and validation",
        "body": ["Preserve the detailed explanation in the body."],
        "breaking": false
    }"""

    result = parse_generated_commit(raw, max_subject_chars=60, emoji=True)

    assert len(result.splitlines()[0]) <= 60
    assert result.startswith("refactor(prompt): 🔨 improve generated commit message")
    assert "Preserve the detailed explanation in the body." in result
