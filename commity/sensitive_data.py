"""Detect credential-like values before they are sent to an LLM."""

import re
from dataclasses import dataclass

_KNOWN_SECRET_PATTERNS = (
    ("OpenAI API key", re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_-]{20,}\b")),
    (
        "GitHub token",
        re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,})\b"),
    ),
    ("AWS access key", re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b")),
    ("Slack token", re.compile(r"\bxox(?:a|b|p|r|s)-[A-Za-z0-9-]{10,}\b")),
    ("private key", re.compile(r"-----BEGIN (?:[A-Z0-9 ]+ )?PRIVATE KEY-----")),
)
_ASSIGNMENT_PATTERN = re.compile(
    r"(?im)^\s*(?:[+-]\s*)?(?:export\s+)?"
    r"[A-Za-z_][A-Za-z0-9_-]*(?:KEY|TOKEN|SECRET|PASSWORD|PASSWD)[A-Za-z0-9_-]*"
    r"\s*[:=]\s*(?:[\"'])?(?P<value>[^\s\"'#]+)"
)
_SAFE_ASSIGNMENT_VALUES = re.compile(
    r"^(?:\$\{?[A-Za-z_][A-Za-z0-9_]*\}?|os\.environ(?:\.get)?|"
    r"getenv\(|<[^>]+>|your[-_]|example|changeme|replace[-_]|test[-_])",
    re.IGNORECASE,
)
_DIFF_HEADER_PATTERN = re.compile(r"^diff --git a/(?P<old>.+) b/(?P<new>.+)$")
_HUNK_HEADER_PATTERN = re.compile(r"^@@ -\d+(?:,\d+)? \+(?P<line>\d+)(?:,\d+)? @@")


@dataclass(frozen=True)
class SensitiveDataMatch:
    """A sensitive value location that is safe to include in an error message."""

    category: str
    content: str
    path: str | None = None
    line: int | None = None


def find_sensitive_data(value: str) -> tuple[str, ...]:
    """Return categories of credential-like values found in text, without exposing them."""
    return tuple(dict.fromkeys(match.category for match in find_sensitive_data_matches(value)))


def find_sensitive_data_matches(value: str) -> tuple[SensitiveDataMatch, ...]:
    """Return redacted credential matches and their Git diff locations when available."""
    findings: list[SensitiveDataMatch] = []
    path: str | None = None
    line: int | None = None

    for text_line in value.splitlines():
        if header := _DIFF_HEADER_PATTERN.match(text_line):
            path = header.group("new")
            line = None
            continue
        if hunk := _HUNK_HEADER_PATTERN.match(text_line):
            line = int(hunk.group("line"))
            continue

        content = text_line
        match_line = line if text_line.startswith(("+", " ")) else None
        known_secret_found = False
        for category, pattern in _KNOWN_SECRET_PATTERNS:
            for match in pattern.finditer(content):
                findings.append(
                    SensitiveDataMatch(category, _redact(match.group()), path, match_line)
                )
                known_secret_found = True

        if not known_secret_found:
            for match in _ASSIGNMENT_PATTERN.finditer(content):
                assigned_value = match.group("value")
                if len(assigned_value) >= 8 and not _SAFE_ASSIGNMENT_VALUES.match(assigned_value):
                    findings.append(
                        SensitiveDataMatch(
                            "credential assignment", _redact(assigned_value), path, match_line
                        )
                    )

        if line is not None and text_line[:1] in {"+", " "}:
            line += 1

    return tuple(dict.fromkeys(findings))


def _redact(value: str) -> str:
    if len(value) <= 10:
        return "[redacted]"
    return f"{value[:6]}…{value[-4:]}"
