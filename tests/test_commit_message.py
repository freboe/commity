"""Tests for generated commit message parsing and validation."""

import pytest

from commity.commit_message import (
    CommitMessageError,
    SubjectLengthError,
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


def test_rejects_overlong_structured_subject():
    raw = '{"type":"fix","scope":"core","subject":"describe a very long correction","body":[]}'

    with pytest.raises(SubjectLengthError, match="maximum is 20") as exc_info:
        parse_generated_commit(
            raw,
            max_subject_chars=20,
            emoji=False,
        )

    assert exc_info.value.commit_msg == "fix(core): describe a very long correction"
    assert exc_info.value.subject == "fix(core): describe a very long correction"
    assert exc_info.value.description_char_budget == 9


def test_rejects_overlong_legacy_subject():
    with pytest.raises(SubjectLengthError, match="maximum is 20"):
        parse_generated_commit(
            "fix(core): describe a very long correction",
            max_subject_chars=20,
            emoji=False,
        )


def test_preserves_body_when_structured_subject_fits():
    raw = """{
        "type": "refactor",
        "scope": "prompt",
        "subject": "improve message accuracy",
        "body": ["Preserve the detailed explanation in the body."],
        "breaking": false
    }"""

    result = parse_generated_commit(raw, max_subject_chars=60, emoji=True)

    assert len(result.splitlines()[0]) <= 60
    assert result.startswith("refactor(prompt): 🔨 improve message accuracy")
    assert "Preserve the detailed explanation in the body." in result
