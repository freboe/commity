"""Tests for interactive CLI state transitions."""

from contextlib import nullcontext
from types import SimpleNamespace

import commity.cli as cli


def test_commit_failure_keeps_generated_message(mocker):
    config = SimpleNamespace(
        context_window_tokens=32768,
        debug=False,
        max_tokens=500,
        model="test-model",
        provider="ollama",
    )
    client = mocker.Mock()
    client.generate.return_value = '{"type":"fix"}'

    mocker.patch("sys.argv", ["commity"])
    mocker.patch.object(cli, "get_llm_config", return_value=config)
    mocker.patch.object(cli, "llm_client_factory", return_value=client)
    mocker.patch.object(cli, "get_git_diff", return_value="diff")
    mocker.patch.object(cli, "detect_change_groups", return_value=[])
    mocker.patch.object(cli, "get_repository_context", return_value="")
    mocker.patch.object(cli, "count_tokens", return_value=10)
    mocker.patch.object(cli, "summary_and_tokens_checker", return_value="diff")
    mocker.patch.object(cli, "parse_generated_commit", return_value="fix: keep message")
    mocker.patch.object(cli, "spinner", side_effect=lambda _text: nullcontext())
    commit = mocker.patch.object(cli, "_run_commit", return_value=False)
    mocker.patch.object(cli.Prompt, "ask", side_effect=["c", "n"])

    cli.main()

    client.generate.assert_called_once()
    commit.assert_called_once_with("fix: keep message")
