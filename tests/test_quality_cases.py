"""Semantic regression cases for staged-change classification."""

import pytest

from commity.core import detect_change_groups
from commity.utils.prompt_organizer import compress_with_structure


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
def test_detect_change_groups_quality_cases(files, expected_groups):
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


def test_large_test_file_does_not_hide_small_production_fix():
    diff = """diff --git a/tests/test_auth.py b/tests/test_auth.py
--- a/tests/test_auth.py
+++ b/tests/test_auth.py
@@ -1 +1 @@
-old test
+many test assertions
diff --git a/src/auth.py b/src/auth.py
--- a/src/auth.py
+++ b/src/auth.py
@@ -1 +1 @@
-return expired
+return refreshed
"""

    summary = compress_with_structure(diff, 100, "gpt-4", "openai")

    assert summary.index("src/auth.py") < summary.index("tests/test_auth.py")
