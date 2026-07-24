"""Read-only repository tools exposed to tool-capable models."""

import json
import subprocess
from collections.abc import Callable
from pathlib import Path
from typing import Any, ClassVar

REPOSITORY_TOOL_NAMES = (
    "get_staged_summary",
    "get_staged_diff",
    "list_recent_commits",
    "get_commit",
    "read_file",
)


class RepositoryToolError(Exception):
    """Raised when a repository tool request is invalid or cannot be completed."""


class ReadOnlyRepositoryTools:
    """Execute a small, read-only set of repository inspection operations."""

    max_result_chars = 30_000
    max_total_chars = 80_000
    max_calls = 5
    sensitive_names: ClassVar[set[str]] = {
        ".env",
        ".git-credentials",
        ".netrc",
        "id_dsa",
        "id_ed25519",
        "id_rsa",
    }

    all_definitions: ClassVar[list[dict[str, Any]]] = [
        {
            "type": "function",
            "function": {
                "name": "get_staged_summary",
                "description": "List staged files and their change statistics.",
                "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_staged_diff",
                "description": "Read the staged diff for all or selected staged files.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "paths": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Optional staged repository-relative paths.",
                        },
                        "context_lines": {
                            "type": "integer",
                            "minimum": 0,
                            "maximum": 20,
                            "default": 3,
                        },
                    },
                    "additionalProperties": False,
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "list_recent_commits",
                "description": "List recent commits, optionally limited to selected tracked paths.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "paths": {"type": "array", "items": {"type": "string"}},
                        "limit": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 20,
                            "default": 10,
                        },
                    },
                    "additionalProperties": False,
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_commit",
                "description": "Read the message and patch of a commit reachable from HEAD.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "commit": {"type": "string"},
                        "paths": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": ["commit"],
                    "additionalProperties": False,
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "read_file",
                "description": "Read a line range from a tracked text file in the repository.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string"},
                        "offset": {
                            "type": "integer",
                            "minimum": 1,
                            "default": 1,
                        },
                        "limit": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 400,
                            "default": 200,
                        },
                    },
                    "required": ["path"],
                    "additionalProperties": False,
                },
            },
        },
    ]

    def __init__(
        self,
        allowed_tools: list[str] | None = None,
        on_tool_use: Callable[[str], None] | None = None,
    ) -> None:
        self.root = Path(self._git(["rev-parse", "--show-toplevel"])).resolve()
        self.allowed_tools = (
            set(REPOSITORY_TOOL_NAMES) if allowed_tools is None else set(allowed_tools)
        )
        self.definitions = [
            definition
            for definition in self.all_definitions
            if definition["function"]["name"] in self.allowed_tools
        ]
        self.on_tool_use = on_tool_use
        self.calls = 0
        self.total_chars = 0

    def execute(self, name: str, arguments: dict[str, Any]) -> str:
        if self.calls >= self.max_calls:
            return self._error("repository tool call limit reached")
        if name not in self.allowed_tools:
            return self._error(f"repository tool is not allowed: {name}")

        self.calls += 1
        if self.on_tool_use is not None:
            self.on_tool_use(name)
        try:
            handlers = {
                "get_staged_summary": self._get_staged_summary,
                "get_staged_diff": self._get_staged_diff,
                "list_recent_commits": self._list_recent_commits,
                "get_commit": self._get_commit,
                "read_file": self._read_file,
            }
            handler = handlers.get(name)
            if handler is None:
                raise RepositoryToolError(f"unknown repository tool: {name}")
            result = handler(arguments)
        except (OSError, UnicodeError, subprocess.CalledProcessError, RepositoryToolError) as error:
            return self._error(str(error))

        remaining = self.max_total_chars - self.total_chars
        if remaining <= 0:
            return self._error("repository tool output budget exhausted")
        result = self._truncate(result, min(self.max_result_chars, remaining))
        self.total_chars += len(result)
        return result

    def _git(self, args: list[str]) -> str:
        result = subprocess.run(
            ["git", "-C", str(getattr(self, "root", Path.cwd())), "--no-pager", *args],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
        )
        return result.stdout.strip()

    def _get_staged_summary(self, arguments: dict[str, Any]) -> str:
        self._require_keys(arguments, set())
        names = self._git(["diff", "--staged", "--name-status"])
        stats = self._git(["diff", "--staged", "--numstat"])
        return f"Staged files:\n{names}\n\nLine statistics:\n{stats}".strip()

    def _get_staged_diff(self, arguments: dict[str, Any]) -> str:
        self._require_keys(arguments, {"paths", "context_lines"})
        paths = self._paths(arguments.get("paths", []), staged_only=True)
        context_lines = self._integer(arguments.get("context_lines", 3), 0, 20, "context_lines")
        args = [
            "diff",
            "--staged",
            "--no-ext-diff",
            "--no-textconv",
            f"--unified={context_lines}",
        ]
        if paths:
            args.extend(["--", *paths])
        return self._git(args)

    def _list_recent_commits(self, arguments: dict[str, Any]) -> str:
        self._require_keys(arguments, {"paths", "limit"})
        paths = self._paths(arguments.get("paths", []))
        limit = self._integer(arguments.get("limit", 10), 1, 20, "limit")
        args = ["log", f"-n{limit}", "--format=%H%x09%s%x09%b"]
        if paths:
            args.extend(["--", *paths])
        return self._git(args)

    def _get_commit(self, arguments: dict[str, Any]) -> str:
        self._require_keys(arguments, {"commit", "paths"})
        commit = arguments.get("commit")
        if not isinstance(commit, str) or not commit or commit.startswith("-"):
            raise RepositoryToolError("commit must be a non-option revision")
        resolved = self._git(["rev-parse", "--verify", f"{commit}^{{commit}}"])
        subprocess.run(
            ["git", "-C", str(self.root), "merge-base", "--is-ancestor", resolved, "HEAD"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            check=True,
        )
        paths = self._paths(arguments.get("paths", []))
        args = [
            "show",
            "--no-ext-diff",
            "--no-textconv",
            "--format=fuller",
            resolved,
        ]
        if paths:
            args.extend(["--", *paths])
        return self._git(args)

    def _read_file(self, arguments: dict[str, Any]) -> str:
        self._require_keys(arguments, {"path", "offset", "limit"})
        raw_path = arguments.get("path")
        if not isinstance(raw_path, str):
            raise RepositoryToolError("path must be a string")
        relative = self._paths([raw_path])[0]
        self._git(["ls-files", "--error-unmatch", "--", relative])
        path = (self.root / relative).resolve()
        if not path.is_relative_to(self.root) or not path.is_file():
            raise RepositoryToolError("path must resolve to a regular repository file")
        self._reject_sensitive(path)
        if b"\0" in path.read_bytes()[:8192]:
            raise RepositoryToolError("binary files cannot be read")

        offset = self._integer(arguments.get("offset", 1), 1, 1_000_000_000, "offset")
        limit = self._integer(arguments.get("limit", 200), 1, 400, "limit")
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        selected = lines[offset - 1 : offset - 1 + limit]
        return "\n".join(f"{number}: {line}" for number, line in enumerate(selected, offset))

    def _paths(self, values: Any, staged_only: bool = False) -> list[str]:
        if not isinstance(values, list) or not all(isinstance(value, str) for value in values):
            raise RepositoryToolError("paths must be an array of strings")
        paths = []
        for value in values:
            if not value or value.startswith("-") or Path(value).is_absolute():
                raise RepositoryToolError("paths must be non-option repository-relative paths")
            resolved = (self.root / value).resolve()
            if not resolved.is_relative_to(self.root):
                raise RepositoryToolError("path escapes the repository")
            relative = resolved.relative_to(self.root).as_posix()
            self._reject_sensitive(resolved)
            paths.append(relative)
        if staged_only and paths:
            staged = set(self._git(["diff", "--staged", "--name-only"]).splitlines())
            if any(path not in staged for path in paths):
                raise RepositoryToolError("get_staged_diff only accepts staged paths")
        return paths

    def _reject_sensitive(self, path: Path) -> None:
        relative = path.relative_to(self.root)
        if ".git" in relative.parts:
            raise RepositoryToolError(".git contents cannot be read")
        name = path.name.lower()
        if (
            name in self.sensitive_names
            or name.startswith(".env.")
            or name.endswith((".key", ".pem", ".p12", ".pfx"))
        ):
            raise RepositoryToolError("sensitive files cannot be read")

    @staticmethod
    def _require_keys(arguments: dict[str, Any], allowed: set[str]) -> None:
        if not isinstance(arguments, dict):
            raise RepositoryToolError("tool arguments must be an object")
        unknown = set(arguments) - allowed
        if unknown:
            raise RepositoryToolError(f"unsupported arguments: {', '.join(sorted(unknown))}")

    @staticmethod
    def _integer(value: Any, minimum: int, maximum: int, name: str) -> int:
        if not isinstance(value, int) or isinstance(value, bool) or not minimum <= value <= maximum:
            raise RepositoryToolError(f"{name} must be between {minimum} and {maximum}")
        return value

    @staticmethod
    def _truncate(value: str, limit: int) -> str:
        if len(value) <= limit:
            return value
        return value[:limit] + "\n[tool output truncated]"

    @staticmethod
    def _error(message: str) -> str:
        return json.dumps({"error": message})
