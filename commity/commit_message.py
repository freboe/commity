"""Parse, validate, and render generated commit messages."""

import json
import re
import textwrap
from typing import Any

from commity.utils.commit_cleaner import clean_thinking_process

ALLOWED_TYPES = {
    "build",
    "chore",
    "ci",
    "docs",
    "feat",
    "fix",
    "perf",
    "refactor",
    "revert",
    "style",
    "test",
}
TYPE_EMOJIS = {
    "build": "📦",
    "chore": "🔧",
    "ci": "👷",
    "docs": "📚",
    "feat": "✨",
    "fix": "🐛",
    "perf": "🚀",
    "refactor": "🔨",
    "revert": "⏪",
    "style": "💎",
    "test": "🚨",
}
SUBJECT_PATTERN = re.compile(
    r"^(?P<type>[a-z]+)(?P<scope>\([\w\-./]+\))?(?P<breaking>!)?: (?P<description>.+)$"
)


class CommitMessageError(ValueError):
    """Raised when a generated commit message is not safe to use."""


class SubjectLengthError(CommitMessageError):
    """Raised when a generated subject exceeds the configured hard limit."""

    def __init__(self, commit_msg: str, max_subject_chars: int):
        self.commit_msg = commit_msg
        self.subject = commit_msg.splitlines()[0].strip()
        match = SUBJECT_PATTERN.fullmatch(self.subject)
        description_start = match.start("description") if match else len(self.subject)
        emoji_chars = 0
        if match:
            description = match.group("description")
            emoji_chars = next(
                (
                    len(marker)
                    for emoji in TYPE_EMOJIS.values()
                    if description.startswith(marker := emoji + " ")
                ),
                0,
            )
        self.description_char_budget = max(
            max_subject_chars - description_start - emoji_chars,
            0,
        )
        super().__init__(
            f"subject is {len(self.subject)} characters; maximum is {max_subject_chars}"
        )


def _parse_json(raw: str) -> dict[str, Any] | None:
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    try:
        value = json.loads(cleaned)
    except json.JSONDecodeError:
        return None
    return value if isinstance(value, dict) else None


def _render_json_message(data: dict[str, Any], emoji: bool) -> str:
    type_ = str(data.get("type", "")).strip().lower()
    scope = str(data.get("scope") or "").strip()
    subject = str(data.get("subject", "")).strip().rstrip(".")
    breaking = bool(data.get("breaking", False))

    if type_ not in ALLOWED_TYPES:
        raise CommitMessageError(f"unsupported commit type: {type_ or '<empty>'}")
    if scope and not re.fullmatch(r"[\w\-./]+", scope):
        raise CommitMessageError("scope contains unsupported characters")
    if not subject or "\n" in subject:
        raise CommitMessageError("subject must be one non-empty line")

    prefix = type_ + (f"({scope})" if scope else "") + ("!" if breaking else "")
    description = f"{TYPE_EMOJIS[type_]} {subject}" if emoji else subject
    lines = [f"{prefix}: {description}"]

    body = data.get("body") or []
    if isinstance(body, str):
        body = [body]
    if not isinstance(body, list):
        raise CommitMessageError("body must be a string or list of strings")
    body_lines = []
    for paragraph in body:
        text = str(paragraph).strip()
        if text:
            body_lines.extend(textwrap.wrap(text, width=72))
    if body_lines:
        lines.extend(["", *body_lines])

    return "\n".join(lines)


def validate_commit_message(commit_msg: str, max_subject_chars: int) -> str:
    """Validate the Conventional Commit fields used by git commit."""
    lines = commit_msg.strip().splitlines()
    if not lines:
        raise CommitMessageError("empty commit message")

    subject = lines[0].strip()
    match = SUBJECT_PATTERN.fullmatch(subject)
    if not match:
        raise CommitMessageError("subject does not follow Conventional Commits")
    if match.group("type") not in ALLOWED_TYPES:
        raise CommitMessageError(f"unsupported commit type: {match.group('type')}")
    if max_subject_chars > 0 and len(subject) > max_subject_chars:
        raise SubjectLengthError(commit_msg.strip(), max_subject_chars)
    if match.group("description").rstrip().endswith("."):
        raise CommitMessageError("subject must not end with a period")
    for line in lines[1:]:
        if len(line) > 72:
            raise CommitMessageError("body lines must not exceed 72 characters")
    return commit_msg.strip()


def parse_generated_commit(
    raw: str,
    max_subject_chars: int,
    emoji: bool,
) -> str:
    """Accept structured model output or a compatible plain-text message."""
    data = _parse_json(raw)
    if data is not None:
        commit_msg = _render_json_message(data, emoji)
    else:
        commit_msg = clean_thinking_process(raw)
    return validate_commit_message(commit_msg, max_subject_chars)
