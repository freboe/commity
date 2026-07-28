import argparse
import json
import os
import shlex
import subprocess
import tempfile
from importlib import metadata
from pathlib import Path

from rich import print
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from rich.rule import Rule

from commity.commit_message import (
    CommitMessageError,
    SubjectLengthError,
    parse_generated_commit,
    validate_commit_message,
)
from commity.config import LLMConfig, get_llm_config
from commity.core import (
    DEFAULT_MAX_SUBJECT_CHARS,
    ChangeGroup,
    detect_change_groups,
    generate_prompt,
    get_git_diff,
    get_repository_context,
)
from commity.llm import BaseLLMClient, LLMGenerationError, llm_client_factory
from commity.repository_tools import ReadOnlyRepositoryTools
from commity.utils.prompt_organizer import summary_and_tokens_checker
from commity.utils.spinner import spinner
from commity.utils.token_counter import TOKEN_SAFETY_MARGIN, count_tokens

MAX_TOOL_TOKEN_RESERVE = 8_192
MAX_SUBJECT_REWRITE_ATTEMPTS = 2


def _calculate_diff_token_budget(
    context_window_tokens: int,
    max_output_tokens: int,
    prompt_tokens: int,
    safety_margin: int = TOKEN_SAFETY_MARGIN,
) -> int:
    """Reserve model output separately from the prompt input budget."""
    budget = context_window_tokens - max_output_tokens - prompt_tokens - safety_margin
    if budget <= 0:
        raise ValueError(
            "Model context window cannot fit the base prompt, output reserve, and safety margin"
        )
    return budget


def _is_context_overflow(error: LLMGenerationError) -> bool:
    text = f"{error} {error.details or ''}".lower()
    markers = ("context length", "context window", "too many tokens", "token limit")
    return error.status_code in {400, 413} and any(marker in text for marker in markers)


def _subject_rewrite_guidance(error: SubjectLengthError) -> str:
    return (
        f"The previous generated commit message was {json.dumps(error.commit_msg)}. "
        f"It failed validation with this exact error: {json.dumps(str(error))}. "
        "Correct that validation failure. If you keep the same type and scope, the JSON subject "
        f"field must be at most {error.description_char_budget} characters. You may shorten or "
        "remove the scope to gain space. Rewrite the complete JSON response with a shorter, "
        "self-contained subject that preserves the umbrella outcome. Preserve useful body "
        "details. Do not truncate the phrase or return the previous subject unchanged."
    )


def _split_commit_message(commit_msg: str) -> list[str]:
    lines = [line.rstrip() for line in commit_msg.strip().splitlines()]
    paragraphs: list[str] = []
    block: list[str] = []

    for line in lines:
        if not line.strip():
            if block:
                paragraphs.append("\n".join(block).strip())
                block = []
            continue
        block.append(line)

    if block:
        paragraphs.append("\n".join(block).strip())

    return paragraphs or [commit_msg.strip()]


def _build_commit_command(commit_msg: str) -> list[str]:
    paragraphs = _split_commit_message(commit_msg)
    command = ["git", "commit"]
    for paragraph in paragraphs:
        command.extend(["-m", paragraph])
    return command


def _run_commit(commit_msg: str) -> bool:
    try:
        subprocess.run(
            _build_commit_command(commit_msg), check=True, capture_output=True, text=True
        )
        print(
            Panel(
                "[bold green]✅ Committed successfully.[/bold green]",
                title="Success",
                border_style="green",
            )
        )
        return True
    except subprocess.CalledProcessError as e:
        error_message = f"Failed to commit: {e.stderr.strip()}"
        print(Panel(f"[bold red]❌ {error_message}[/bold red]", title="Error", border_style="red"))
        return False


def _run_push() -> bool:
    try:
        subprocess.run(["git", "push"], check=True, capture_output=True, text=True)
        print(
            Panel(
                "[bold green]✅ Pushed successfully.[/bold green]",
                title="Success",
                border_style="green",
            )
        )
        return True
    except subprocess.CalledProcessError as e:
        error_message = f"Failed to push: {e.stderr.strip()}"
        print(Panel(f"[bold red]❌ {error_message}[/bold red]", title="Error", border_style="red"))
        return False


def _edit_commit_message(commit_msg: str) -> str:
    """Open the suggested message in the user's configured editor."""
    editor = os.environ.get("GIT_EDITOR") or os.environ.get("VISUAL") or os.environ.get("EDITOR")
    if not editor:
        try:
            editor = subprocess.run(
                ["git", "var", "GIT_EDITOR"],
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
        except subprocess.CalledProcessError:
            editor = "vi"

    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".commit-message", encoding="utf-8", delete=False
        ) as file:
            file.write(commit_msg + "\n")
            temp_path = Path(file.name)
        subprocess.run([*shlex.split(editor), str(temp_path)], check=False)
        return temp_path.read_text(encoding="utf-8").strip()
    finally:
        if temp_path and temp_path.exists():
            temp_path.unlink()


def _show_commit_message(commit_msg: str) -> None:
    print(Rule("[bold green] Suggested Commit Message[/bold green]"))
    print(Markdown(commit_msg))
    print(Rule(style="green"))


def _show_tool_use(tool_name: str) -> None:
    print(f"[cyan]🔍 Model is using repository tool:[/cyan] [bold]{tool_name}[/bold]")


def _create_argument_parser() -> argparse.ArgumentParser:
    try:
        version = metadata.version("commity")
    except metadata.PackageNotFoundError:
        version = "unknown"

    parser = argparse.ArgumentParser(description="AI-powered git commit message generator")
    parser.add_argument("-v", "--version", action="version", version=f"%(prog)s {version}")
    parser.add_argument("--provider", type=str, help="LLM provider")
    parser.add_argument("--base_url", type=str, help="LLM base URL")
    parser.add_argument("--model", type=str, help="LLM model name")
    parser.add_argument("--api_key", type=str, help="LLM API key")
    parser.add_argument(
        "--language",
        "--lang",
        dest="language",
        type=str,
        default="en",
        help="Language for commit message",
    )
    parser.add_argument("--temperature", type=float, help="Temperature for generation")
    parser.add_argument("--max_tokens", type=int, help="Max tokens for LLM response generation")
    parser.add_argument(
        "--context_window_tokens",
        type=int,
        help="Maximum tokens accepted by the model context window",
    )
    parser.add_argument(
        "--max_subject_chars",
        type=int,
        default=DEFAULT_MAX_SUBJECT_CHARS,
        help="Max characters for the generated commit message (subject)",
    )
    parser.add_argument("--timeout", type=int, help="Timeout in seconds")
    parser.add_argument("--max_attempts", type=int, help="Maximum LLM request attempts")
    parser.add_argument("--proxy", type=str, help="Proxy URL")
    parser.add_argument("--emoji", action="store_true", help="Include emojis")
    parser.add_argument("--type", type=str, default="conventional", help="Commit style type")
    parser.add_argument("--show-config", action="store_true", help="Show current configuration")
    parser.add_argument(
        "--debug",
        action="store_true",
        default=None,
        help="Show prompt budgeting and diff compression diagnostics",
    )
    parser.add_argument(
        "--allow_tools",
        action="store_true",
        default=None,
        help="Allow the model to inspect the repository with read-only tools",
    )
    parser.add_argument(
        "--allowed_tools",
        nargs="+",
        help="Read-only repository tools available to the model",
    )
    parser.add_argument(
        "--confirm",
        type=str,
        default="y",
        choices=["y", "n"],
        help="Confirm before committing (y/n)",
    )
    return parser


def _show_config(config: LLMConfig) -> None:
    config_dict = {key: value for key, value in config.__dict__.items() if value is not None}
    if config_dict.get("api_key"):
        config_dict["api_key"] = "***"
    print(
        Panel(
            str(config_dict),
            title="[bold blue]✅ Current Configuration[/bold blue]",
            border_style="blue",
        )
    )


def _confirm_combined_changes(change_groups: list[ChangeGroup], confirm: str) -> bool:
    if len(change_groups) <= 1:
        return True

    group_summary = "\n".join(
        f"- {group.name}: {', '.join(group.files)}" for group in change_groups
    )
    print(
        Panel(
            "Potentially independent staged changes were detected:\n" + group_summary,
            title="Consider splitting this commit",
            border_style="yellow",
        )
    )
    if confirm == "n":
        return True

    proceed = Prompt.ask(
        "Generate one message for all staged changes?", choices=["y", "n"], default="y"
    )
    return proceed == "y"


def _compress_diff(
    args: argparse.Namespace,
    config: LLMConfig,
    original_diff: str,
    repository_context: str,
    change_groups: list[ChangeGroup],
    repository_tools: ReadOnlyRepositoryTools | None = None,
) -> str:
    base_prompt = generate_prompt(
        "",
        language=args.language,
        emoji=args.emoji,
        type_=args.type,
        max_subject_chars=args.max_subject_chars,
        repository_context=repository_context,
    )
    system_prompt_tokens = count_tokens(base_prompt, config.model, config.provider)
    tool_schema_tokens = 0
    tool_result_reserve = 0
    if repository_tools is not None:
        serialized_tools = json.dumps(
            repository_tools.definitions,
            ensure_ascii=False,
            separators=(",", ":"),
        )
        tool_schema_tokens = count_tokens(serialized_tools, config.model, config.provider)
        available_for_content = _calculate_diff_token_budget(
            config.context_window_tokens,
            config.max_tokens,
            system_prompt_tokens + tool_schema_tokens,
        )
        tool_result_reserve = min(MAX_TOOL_TOKEN_RESERVE, available_for_content // 4)

    diff_token_budget = _calculate_diff_token_budget(
        config.context_window_tokens,
        config.max_tokens,
        system_prompt_tokens + tool_schema_tokens + tool_result_reserve,
    )
    original_diff_tokens = count_tokens(original_diff, config.model, config.provider)
    diff = summary_and_tokens_checker(
        original_diff,
        max_output_tokens=diff_token_budget,
        model_name=config.model,
        provider=config.provider,
    )
    final_diff_tokens = count_tokens(diff, config.model, config.provider)

    if config.debug:
        diagnostics = {
            "provider": config.provider,
            "model": config.model,
            "context_window_tokens": config.context_window_tokens,
            "max_output_tokens": config.max_tokens,
            "repository_context_tokens": count_tokens(
                repository_context, config.model, config.provider
            ),
            "prompt_without_diff_tokens": system_prompt_tokens,
            "tool_schema_tokens": tool_schema_tokens,
            "tool_result_reserve": tool_result_reserve,
            "diff_budget_tokens": diff_token_budget,
            "original_diff_tokens": original_diff_tokens,
            "final_diff_tokens": final_diff_tokens,
            "diff_compressed": diff != original_diff,
            "change_groups": [group.name for group in change_groups],
        }
        print(Panel(str(diagnostics), title="Debug diagnostics", border_style="blue"))

    return diff


def _generate_raw_message(
    client: BaseLLMClient,
    repository_tools: ReadOnlyRepositoryTools | None,
    prompt: str,
) -> str | None:
    with spinner("🚀 Generating commit message..."):
        if repository_tools is None:
            return client.generate(prompt)
        return client.generate_with_tools(prompt, repository_tools)


def _handle_commit_actions(
    commit_msg: str,
    confirm: str,
    max_subject_chars: int,
) -> str | None:
    """Commit the message or return guidance when regeneration is requested."""
    _show_commit_message(commit_msg)
    while True:
        action = "c"
        if confirm == "y":
            action = Prompt.ask(
                "Choose an action: commit, edit, regenerate, or cancel",
                choices=["c", "e", "r", "n"],
                default="n",
            )

        if action == "r":
            return Prompt.ask("Optional guidance for regeneration", default="", show_default=False)
        if action == "e":
            edited = _edit_commit_message(commit_msg)
            try:
                commit_msg = validate_commit_message(edited, max_subject_chars)
            except CommitMessageError as error:
                print(Panel(str(error), title="Invalid edited message", border_style="yellow"))
                continue
            _show_commit_message(commit_msg)
            if confirm == "y":
                action = Prompt.ask("Commit the edited message?", choices=["c", "n"], default="n")
        if action == "n":
            print(
                Panel(
                    "[bold yellow]Commit cancelled.[/bold yellow]",
                    title="[bold yellow]Cancelled[/bold yellow]",
                    border_style="yellow",
                )
            )
            return None
        if action == "c":
            if not _run_commit(commit_msg):
                if confirm == "n":
                    return None
                continue
            push_input = Prompt.ask("Do you want to push changes?", choices=["y", "n"], default="n")
            if push_input.lower() == "y":
                _run_push()
            return None


def _run_generation_workflow(
    args: argparse.Namespace,
    config: LLMConfig,
    client: BaseLLMClient,
    repository_tools: ReadOnlyRepositoryTools | None,
    original_diff: str,
    initial_diff: str,
    repository_context: str,
) -> None:
    diff = initial_diff
    guidance = ""
    context_retry_used = False
    subject_rewrite_attempts = 0

    while True:
        prompt = generate_prompt(
            diff,
            language=args.language,
            emoji=args.emoji,
            type_=args.type,
            max_subject_chars=args.max_subject_chars,
            repository_context=repository_context,
            guidance=guidance,
        )
        try:
            raw_message = _generate_raw_message(client, repository_tools, prompt)
        except LLMGenerationError as error:
            if context_retry_used or not _is_context_overflow(error):
                raise

            reduced_budget = max(count_tokens(diff, config.model, config.provider) // 2, 1)
            diff = summary_and_tokens_checker(
                original_diff,
                max_output_tokens=reduced_budget,
                model_name=config.model,
                provider=config.provider,
            )
            context_retry_used = True
            guidance = "Keep the response concise because the model context is limited."
            if config.debug:
                print(
                    Panel(
                        f"Context overflow detected; retrying with {reduced_budget} diff tokens.",
                        title="Debug diagnostics",
                        border_style="blue",
                    )
                )
            continue

        if not raw_message:
            raise CommitMessageError("model returned an empty response")

        try:
            commit_msg = parse_generated_commit(
                raw_message,
                max_subject_chars=args.max_subject_chars,
                emoji=args.emoji,
            )
        except CommitMessageError as error:
            if (
                isinstance(error, SubjectLengthError)
                and subject_rewrite_attempts < MAX_SUBJECT_REWRITE_ATTEMPTS
            ):
                subject_rewrite_attempts += 1
                _show_commit_message(error.commit_msg)
                print(
                    f"[yellow]Generated subject is {len(error.subject)} characters; asking the "
                    f"model to rewrite it ({subject_rewrite_attempts}/"
                    f"{MAX_SUBJECT_REWRITE_ATTEMPTS}).[/yellow]"
                )
                guidance = _subject_rewrite_guidance(error)
                continue
            if isinstance(error, SubjectLengthError):
                _show_commit_message(error.commit_msg)
            if args.confirm == "n":
                raise
            print(Panel(str(error), title="Invalid generated message", border_style="yellow"))
            retry = Prompt.ask("Regenerate?", choices=["r", "n"], default="r")
            if retry == "r":
                guidance = (
                    _subject_rewrite_guidance(error)
                    if isinstance(error, SubjectLengthError)
                    else str(error)
                )
                subject_rewrite_attempts = 0
                continue
            return

        regeneration_guidance = _handle_commit_actions(
            commit_msg,
            confirm=args.confirm,
            max_subject_chars=args.max_subject_chars,
        )
        if regeneration_guidance is None:
            return
        guidance = regeneration_guidance


def _show_llm_error(error: LLMGenerationError) -> None:
    from rich.markup import escape

    details = []
    if error.status_code is not None:
        details.append(f"Status: {error.status_code}")
    if error.details:
        details.append(error.details.strip())
    error_message = escape("\n".join(details) or str(error))
    print(
        Panel(
            "❌ LLM request failed:\n" + error_message,
            title="Error",
            border_style="red",
        )
    )


def main() -> None:
    parser = _create_argument_parser()
    args = parser.parse_args()
    config = get_llm_config(args)

    if args.show_config:
        _show_config(config)
        return

    client = llm_client_factory(config)
    original_diff = get_git_diff()
    if not original_diff:
        print(
            Panel(
                "[bold yellow]⚠️ No staged changes detected.[/bold yellow]",
                title="[bold yellow]Warning[/bold yellow]",
                border_style="yellow",
            )
        )
        return

    change_groups = detect_change_groups(original_diff)
    if not _confirm_combined_changes(change_groups, args.confirm):
        return

    repository_context = get_repository_context()
    repository_tools = (
        ReadOnlyRepositoryTools(config.allowed_tools, on_tool_use=_show_tool_use)
        if config.allow_tools
        else None
    )
    try:
        diff = _compress_diff(
            args,
            config,
            original_diff,
            repository_context,
            change_groups,
            repository_tools,
        )
        _run_generation_workflow(
            args,
            config,
            client,
            repository_tools,
            original_diff,
            diff,
            repository_context,
        )
    except (EOFError, KeyboardInterrupt):
        print(
            Panel(
                "[bold yellow]Operation cancelled by user.[/bold yellow]",
                title="[bold yellow]Cancelled[/bold yellow]",
                border_style="yellow",
            )
        )
    except LLMGenerationError as error:
        _show_llm_error(error)
    except Exception as error:
        from rich.markup import escape

        error_message = escape(str(error))
        print(Panel("❌ An error occurred: " + error_message, title="Error", border_style="red"))


if __name__ == "__main__":
    main()
