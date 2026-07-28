"""Tests for interactive CLI state transitions."""

from contextlib import nullcontext
from types import SimpleNamespace

import commity.cli as cli
from commity.cli import (
    _compress_diff,
    _confirm_combined_changes,
    _confirm_sensitive_data,
    _create_argument_parser,
    _handle_commit_actions,
    _run_generation_workflow,
    _show_config,
)
from commity.core import ChangeGroup
from commity.llm import LLMGenerationError, SensitiveDataError


def test_subject_limit_defaults_to_60_and_accepts_override():
    parser = _create_argument_parser()

    assert parser.parse_args([]).max_subject_chars == 60
    assert parser.parse_args(["--max_subject_chars", "72"]).max_subject_chars == 72
    assert parser.parse_args(["-y"]).yes is True


def test_yes_commits_and_pushes_without_prompts(mocker):
    config = SimpleNamespace(
        context_window_tokens=32768,
        debug=False,
        max_tokens=500,
        model="test-model",
        provider="ollama",
        allow_tools=False,
        allowed_tools=None,
    )
    client = mocker.Mock()
    client.generate.return_value = '{"type":"fix"}'

    mocker.patch("sys.argv", ["commity", "-y"])
    mocker.patch.object(cli, "get_llm_config", return_value=config)
    mocker.patch.object(cli, "llm_client_factory", return_value=client)
    mocker.patch.object(cli, "get_git_diff", return_value="diff")
    mocker.patch.object(cli, "detect_change_groups", return_value=[])
    mocker.patch.object(cli, "get_repository_context", return_value="")
    mocker.patch.object(cli, "count_tokens", return_value=10)
    mocker.patch.object(cli, "summary_and_tokens_checker", return_value="diff")
    mocker.patch.object(cli, "parse_generated_commit", return_value="fix: push automatically")
    mocker.patch.object(cli, "spinner", side_effect=lambda _text: nullcontext())
    commit = mocker.patch.object(cli, "_run_commit", return_value=True)
    push = mocker.patch.object(cli, "_run_push", return_value=True)
    prompt = mocker.patch.object(cli.Prompt, "ask")

    cli.main()

    commit.assert_called_once_with("fix: push automatically")
    push.assert_called_once_with()
    prompt.assert_not_called()


def test_commit_failure_keeps_generated_message(mocker):
    config = SimpleNamespace(
        context_window_tokens=32768,
        debug=False,
        max_tokens=500,
        model="test-model",
        provider="ollama",
        allow_tools=False,
        allowed_tools=None,
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
    client.generate_with_tools.assert_not_called()
    commit.assert_called_once_with("fix: keep message")


def test_enabled_tools_are_filtered_and_passed_to_client(mocker):
    config = SimpleNamespace(
        context_window_tokens=32768,
        debug=False,
        max_tokens=500,
        model="test-model",
        provider="openai",
        allow_tools=True,
        allowed_tools=["read_file"],
    )
    client = mocker.Mock()
    client.generate_with_tools.return_value = '{"type":"fix"}'
    repository_tools = mocker.Mock()
    repository_tools.definitions = [{"type": "function", "function": {"name": "read_file"}}]

    mocker.patch("sys.argv", ["commity"])
    mocker.patch.object(cli, "get_llm_config", return_value=config)
    mocker.patch.object(cli, "llm_client_factory", return_value=client)
    mocker.patch.object(cli, "get_git_diff", return_value="diff")
    mocker.patch.object(cli, "detect_change_groups", return_value=[])
    mocker.patch.object(cli, "get_repository_context", return_value="")
    mocker.patch.object(cli, "count_tokens", return_value=10)
    mocker.patch.object(cli, "summary_and_tokens_checker", return_value="diff")
    mocker.patch.object(cli, "parse_generated_commit", return_value="fix: inspect context")
    mocker.patch.object(cli, "spinner", side_effect=lambda _text: nullcontext())
    tools_class = mocker.patch.object(cli, "ReadOnlyRepositoryTools", return_value=repository_tools)
    mocker.patch.object(cli, "_run_commit", return_value=False)
    mocker.patch.object(cli.Prompt, "ask", side_effect=["c", "n"])

    cli.main()

    tools_class.assert_called_once_with(["read_file"], on_tool_use=mocker.ANY)
    client.generate_with_tools.assert_called_once_with(mocker.ANY, repository_tools)
    client.generate.assert_not_called()


def test_combined_changes_respect_confirmation_mode(mocker):
    groups = [
        ChangeGroup(name="code", files=("commity/cli.py",)),
        ChangeGroup(name="docs", files=("README.md",)),
    ]
    prompt = mocker.patch.object(cli.Prompt, "ask", return_value="n")
    mocker.patch.object(cli, "print")

    assert _confirm_combined_changes(groups, confirm="n") is True
    prompt.assert_not_called()

    assert _confirm_combined_changes(groups, confirm="y") is False
    prompt.assert_called_once()


def test_compress_diff_uses_available_context_budget(mocker):
    args = SimpleNamespace(
        language="en",
        emoji=False,
        type="conventional",
        max_subject_chars=50,
    )
    config = SimpleNamespace(
        context_window_tokens=1000,
        debug=False,
        max_tokens=100,
        model="test-model",
        provider="ollama",
    )
    mocker.patch.object(cli, "generate_prompt", return_value="base prompt")
    mocker.patch.object(cli, "count_tokens", side_effect=[100, 800, 200])
    compress = mocker.patch.object(
        cli,
        "summary_and_tokens_checker",
        return_value="compressed diff",
    )

    result = _compress_diff(args, config, "original diff", "repository", [])

    assert result == "compressed diff"
    compress.assert_called_once_with(
        "original diff",
        max_output_tokens=288,
        model_name="test-model",
        provider="ollama",
    )


def test_generation_workflow_retries_context_overflow_once(mocker):
    args = SimpleNamespace(
        language="en",
        emoji=False,
        type="conventional",
        max_subject_chars=50,
        confirm="n",
    )
    config = SimpleNamespace(debug=False, model="test-model", provider="ollama")
    client = mocker.Mock()
    overflow = LLMGenerationError(
        "request failed",
        status_code=400,
        details="maximum context length exceeded",
    )
    generate = mocker.patch.object(
        cli,
        "_generate_raw_message",
        side_effect=[overflow, '{"type":"fix"}'],
    )
    mocker.patch.object(
        cli,
        "generate_prompt",
        side_effect=lambda diff, **kwargs: f"{diff}|{kwargs['guidance']}",
    )
    mocker.patch.object(cli, "count_tokens", return_value=500)
    compress = mocker.patch.object(
        cli,
        "summary_and_tokens_checker",
        return_value="smaller diff",
    )
    mocker.patch.object(cli, "parse_generated_commit", return_value="fix: handle overflow")
    actions = mocker.patch.object(cli, "_handle_commit_actions", return_value=None)

    _run_generation_workflow(
        args,
        config,
        client,
        None,
        "original diff",
        "initial diff",
        "repository",
    )

    assert [call.args[2] for call in generate.call_args_list] == [
        "initial diff|",
        "smaller diff|Keep the response concise because the model context is limited.",
    ]
    compress.assert_called_once_with(
        "original diff",
        max_output_tokens=250,
        model_name="test-model",
        provider="ollama",
    )
    actions.assert_called_once_with(
        "fix: handle overflow",
        confirm="n",
        max_subject_chars=50,
    )


def test_sensitive_data_confirmation_retries_once_after_explicit_consent(mocker):
    args = SimpleNamespace(
        language="en",
        emoji=False,
        type="conventional",
        max_subject_chars=50,
        confirm="n",
    )
    config = SimpleNamespace(debug=False, model="test-model", provider="ollama")
    client = mocker.Mock()
    generate = mocker.patch.object(
        cli,
        "_generate_raw_message",
        side_effect=[SensitiveDataError("Sensitive data detected"), '{"type":"fix"}'],
    )
    mocker.patch.object(cli, "_confirm_sensitive_data", return_value=True)
    mocker.patch.object(cli, "parse_generated_commit", return_value="fix: send after consent")
    mocker.patch.object(cli, "_handle_commit_actions", return_value=None)

    _run_generation_workflow(
        args,
        config,
        client,
        None,
        "original diff",
        "initial diff",
        "repository",
    )

    assert generate.call_count == 2
    client.allow_sensitive_request_once.assert_called_once_with()


def test_sensitive_data_confirmation_defaults_to_no(mocker):
    error = SensitiveDataError("Sensitive data detected")
    output = mocker.patch.object(cli, "print")
    prompt = mocker.patch.object(cli.Prompt, "ask", return_value="n")

    assert _confirm_sensitive_data(error) is False
    assert "The request was not sent" in str(output.call_args.args[0].renderable)
    prompt.assert_called_once_with(
        "Sensitive data may be sent to the LLM. Continue?", choices=["y", "n"], default="n"
    )


def test_generation_workflow_rewrites_overlong_subject_once(mocker):
    args = SimpleNamespace(
        language="en",
        emoji=False,
        type="conventional",
        max_subject_chars=40,
        confirm="n",
    )
    config = SimpleNamespace(debug=False, model="test-model", provider="ollama")
    client = mocker.Mock()
    generate = mocker.patch.object(
        cli,
        "_generate_raw_message",
        side_effect=[
            (
                '{"type":"fix","scope":"token-budget",'
                '"subject":"truncate tool and diff outputs",'
                '"body":["Keep useful implementation details."]}'
            ),
            ('{"type":"fix","scope":"budget","subject":"enforce context limits","body":[]}'),
        ],
    )
    prompts = mocker.patch.object(
        cli,
        "generate_prompt",
        side_effect=lambda _diff, **kwargs: kwargs["guidance"],
    )
    show_message = mocker.patch.object(cli, "_show_commit_message")
    output = mocker.patch.object(cli, "print")
    actions = mocker.patch.object(cli, "_handle_commit_actions", return_value=None)

    _run_generation_workflow(
        args,
        config,
        client,
        None,
        "original diff",
        "initial diff",
        "repository",
    )

    assert generate.call_count == 2
    retry_guidance = prompts.call_args_list[1].kwargs["guidance"]
    assert (
        '"fix(token-budget): truncate tool and diff outputs\\n\\n'
        'Keep useful implementation details."' in retry_guidance
    )
    assert '"subject is 49 characters; maximum is 40"' in retry_guidance
    assert "JSON subject field must be at most 21 characters" in retry_guidance
    assert "preserves the umbrella outcome" in retry_guidance
    show_message.assert_called_once_with(
        "fix(token-budget): truncate tool and diff outputs\n\nKeep useful implementation details."
    )
    assert "asking the model to rewrite it (1/2)" in output.call_args.args[0]
    actions.assert_called_once_with(
        "fix(budget): enforce context limits",
        confirm="n",
        max_subject_chars=40,
    )


def test_generation_workflow_rejects_subject_after_bounded_rewrites(mocker):
    args = SimpleNamespace(
        language="en",
        emoji=False,
        type="conventional",
        max_subject_chars=30,
        confirm="y",
    )
    config = SimpleNamespace(debug=False, model="test-model", provider="ollama")
    client = mocker.Mock()
    raw = (
        '{"type":"fix","scope":"budget","subject":"enforce strict context window limits","body":[]}'
    )
    generate = mocker.patch.object(cli, "_generate_raw_message", side_effect=[raw, raw, raw])
    mocker.patch.object(cli, "generate_prompt", return_value="prompt")
    show_message = mocker.patch.object(cli, "_show_commit_message")
    mocker.patch.object(cli, "print")
    mocker.patch.object(cli.Prompt, "ask", return_value="n")
    actions = mocker.patch.object(cli, "_handle_commit_actions")

    _run_generation_workflow(
        args,
        config,
        client,
        None,
        "original diff",
        "initial diff",
        "repository",
    )

    assert generate.call_count == 3
    assert show_message.call_args_list == [
        mocker.call("fix(budget): enforce strict context window limits"),
        mocker.call("fix(budget): enforce strict context window limits"),
        mocker.call("fix(budget): enforce strict context window limits"),
    ]
    actions.assert_not_called()


def test_commit_actions_return_regeneration_guidance(mocker):
    mocker.patch.object(cli, "_show_commit_message")
    commit = mocker.patch.object(cli, "_run_commit")
    mocker.patch.object(cli.Prompt, "ask", side_effect=["r", "focus on tests"])

    guidance = _handle_commit_actions(
        "refactor(cli): split workflow",
        confirm="y",
        max_subject_chars=50,
    )

    assert guidance == "focus on tests"
    commit.assert_not_called()


def test_show_config_masks_api_key(mocker):
    config = SimpleNamespace(provider="openai", api_key="super-secret")
    output = mocker.patch.object(cli, "print")

    _show_config(config)

    panel = output.call_args.args[0]
    assert "super-secret" not in panel.renderable
    assert "'api_key': '***'" in panel.renderable
