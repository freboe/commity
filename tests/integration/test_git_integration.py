"""Integration tests for Git operations."""

import subprocess
from pathlib import Path

import pytest

from commity.core import get_git_diff

from .conftest import is_git_available


@pytest.mark.integration
@pytest.mark.skipif(not is_git_available(), reason="Git is not available")
class TestGitIntegration:
    """Integration tests for real Git operations."""

    def test_get_diff_with_real_git_repo(self, temp_git_repo: Path):
        """Test getting diff from a real Git repository."""
        # Create a new file
        test_file = temp_git_repo / "test.py"
        test_file.write_text("print('hello world')\n")

        # Stage the file
        subprocess.run(["git", "add", "test.py"], cwd=temp_git_repo, check=True)

        # Get the diff
        diff = get_git_diff()

        # Verify diff content
        assert diff != ""
        assert "test.py" in diff
        assert "print('hello world')" in diff
        assert "+++" in diff  # Git diff format

    def test_get_diff_with_no_staged_changes(self, temp_git_repo: Path):  # noqa: ARG002
        """Test getting diff when there are no staged changes."""
        # No staged changes
        diff = get_git_diff()

        # Should return empty string
        assert diff == ""

    def test_get_diff_with_modified_file(self, temp_git_repo: Path):
        """Test getting diff for a modified file."""
        # Modify existing file
        readme = temp_git_repo / "README.md"
        original_content = readme.read_text()
        readme.write_text(original_content + "\nNew line added\n")

        # Stage the change
        subprocess.run(["git", "add", "README.md"], cwd=temp_git_repo, check=True)

        # Get the diff
        diff = get_git_diff()

        # Verify diff content
        assert diff != ""
        assert "README.md" in diff
        assert "New line added" in diff
        assert "+New line added" in diff

    def test_get_diff_with_deleted_file(self, temp_git_repo: Path):
        """Test getting diff for a deleted file."""
        # Create and commit a file first
        test_file = temp_git_repo / "to_delete.txt"
        test_file.write_text("This will be deleted\n")
        subprocess.run(["git", "add", "to_delete.txt"], cwd=temp_git_repo, check=True)
        subprocess.run(
            ["git", "commit", "-m", "Add file to delete"],
            cwd=temp_git_repo,
            check=True,
            capture_output=True,
        )

        # Delete the file
        test_file.unlink()

        # Stage the deletion
        subprocess.run(["git", "add", "to_delete.txt"], cwd=temp_git_repo, check=True)

        # Get the diff
        diff = get_git_diff()

        # Verify diff content
        assert diff != ""
        assert "to_delete.txt" in diff
        assert "deleted file mode" in diff or "-This will be deleted" in diff

    def test_get_diff_with_multiple_files(self, temp_git_repo: Path):
        """Test getting diff with multiple staged files."""
        # Create multiple files
        file1 = temp_git_repo / "file1.py"
        file2 = temp_git_repo / "file2.py"
        file1.write_text("# File 1\nprint('file1')\n")
        file2.write_text("# File 2\nprint('file2')\n")

        # Stage both files
        subprocess.run(["git", "add", "file1.py", "file2.py"], cwd=temp_git_repo, check=True)

        # Get the diff
        diff = get_git_diff()

        # Verify both files are in the diff
        assert diff != ""
        assert "file1.py" in diff
        assert "file2.py" in diff
        assert "print('file1')" in diff
        assert "print('file2')" in diff

    def test_get_diff_with_binary_file(self, temp_git_repo: Path):
        """Test getting diff with a binary file."""
        # Create a binary file (simple bytes)
        binary_file = temp_git_repo / "image.bin"
        binary_file.write_bytes(b"\x00\x01\x02\x03\x04\x05")

        # Stage the file
        subprocess.run(["git", "add", "image.bin"], cwd=temp_git_repo, check=True)

        # Get the diff
        diff = get_git_diff()

        # Verify diff exists and mentions the file
        assert diff != ""
        assert "image.bin" in diff
