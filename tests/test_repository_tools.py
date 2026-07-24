"""Tests for read-only repository tools."""

import json
import subprocess
from unittest.mock import Mock

from commity.repository_tools import REPOSITORY_TOOL_NAMES, ReadOnlyRepositoryTools


def _git(path, *args):
    return subprocess.run(
        ["git", "-C", str(path), *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=True,
    ).stdout.strip()


def _repository(tmp_path, monkeypatch):
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "test@example.com")
    _git(tmp_path, "config", "user.name", "Test User")
    source = tmp_path / "app.py"
    source.write_text("def value():\n    return 1\n", encoding="utf-8")
    _git(tmp_path, "add", "app.py")
    _git(tmp_path, "commit", "-m", "feat: add value")
    source.write_text("def value():\n    return 2\n", encoding="utf-8")
    _git(tmp_path, "add", "app.py")
    monkeypatch.chdir(tmp_path)
    return ReadOnlyRepositoryTools()


def test_reads_staged_summary_and_diff(tmp_path, monkeypatch):
    tools = _repository(tmp_path, monkeypatch)

    summary = tools.execute("get_staged_summary", {})
    diff = tools.execute("get_staged_diff", {"paths": ["app.py"], "context_lines": 1})

    assert {item["function"]["name"] for item in tools.definitions} == set(REPOSITORY_TOOL_NAMES)
    assert "app.py" in summary
    assert "-    return 1" in diff
    assert "+    return 2" in diff


def test_reads_tracked_file_and_reachable_commit(tmp_path, monkeypatch):
    tools = _repository(tmp_path, monkeypatch)

    content = tools.execute("read_file", {"path": "app.py", "offset": 1, "limit": 2})
    history = tools.execute("list_recent_commits", {"paths": ["app.py"], "limit": 1})
    commit = tools.execute("get_commit", {"commit": "HEAD", "paths": ["app.py"]})

    assert "1: def value():" in content
    assert "feat: add value" in history
    assert "feat: add value" in commit


def test_rejects_sensitive_and_unstaged_paths(tmp_path, monkeypatch):
    tools = _repository(tmp_path, monkeypatch)
    secret = tmp_path / ".env"
    secret.write_text("TOKEN=secret\n", encoding="utf-8")
    _git(tmp_path, "add", ".env")

    sensitive = json.loads(tools.execute("read_file", {"path": ".env"}))
    unstaged = json.loads(tools.execute("get_staged_diff", {"paths": ["missing.py"]}))

    assert "sensitive" in sensitive["error"]
    assert "staged paths" in unstaged["error"]


def test_enforces_call_limit(tmp_path, monkeypatch):
    tools = _repository(tmp_path, monkeypatch)
    tools.max_calls = 1

    tools.execute("get_staged_summary", {})
    result = json.loads(tools.execute("get_staged_summary", {}))

    assert "call limit" in result["error"]


def test_exposes_and_executes_only_allowed_tools(tmp_path, monkeypatch):
    _repository(tmp_path, monkeypatch)
    tools = ReadOnlyRepositoryTools(["read_file"])

    names = [definition["function"]["name"] for definition in tools.definitions]
    denied = json.loads(tools.execute("get_staged_summary", {}))

    assert names == ["read_file"]
    assert "not allowed" in denied["error"]
    assert tools.calls == 0


def test_notifies_when_allowed_tool_is_used(tmp_path, monkeypatch):
    _repository(tmp_path, monkeypatch)
    on_tool_use = Mock()
    tools = ReadOnlyRepositoryTools(["read_file"], on_tool_use=on_tool_use)

    tools.execute("read_file", {"path": "app.py", "limit": 1})
    tools.execute("get_staged_summary", {})

    on_tool_use.assert_called_once_with("read_file")
