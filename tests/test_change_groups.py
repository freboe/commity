"""Tests for staged-change classification."""

import pytest

from commity.core import detect_change_groups


@pytest.mark.parametrize(
    ("files", "expected_groups"),
    [
        (
            [
                ("src/auth.py", "+return refreshed"),
                ("tests/test_auth.py", "+assert refreshed"),
            ],
            ["code"],
        ),
        ([("README.md", "+Installation")], ["docs"]),
        ([("pyproject.toml", '+requests = "2.0"'), ("uv.lock", "+locked")], ["build"]),
        (
            [
                ("src/auth.py", "+return refreshed"),
                ("README.md", "+Document refresh"),
                (".github/workflows/test.yml", "+run: pytest"),
            ],
            ["code", "ci", "docs"],
        ),
    ],
)
def test_detect_change_groups(files, expected_groups):
    diff = "".join(
        f"""diff --git a/{path} b/{path}
--- a/{path}
+++ b/{path}
@@ -1 +1 @@
-old
{change}
"""
        for path, change in files
    )

    assert [group.name for group in detect_change_groups(diff)] == expected_groups
