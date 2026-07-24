import argparse
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
    parse_generated_commit,
    validate_commit_message,
)
from commity.config import get_llm_config
from commity.core import (
    detect_change_groups,
    generate_prompt,
    get_git_diff,
    get_repository_context,
)
from commity.llm import LLMGenerationError, llm_client_factory
from commity.utils.prompt_organizer import summary_and_tokens_checker
from commity.utils.spinner import spinner
from commity.utils.token_counter import count_tokens

TOKEN_SAFETY_MARGIN = 512


def _calculate_diff_token_budget(
    context_window_tokens: int,
    max_output_tokens: int,
    prompt_tokens: int,
    safety_margin: int = TOKEN_SAFETY_MARGIN,
) -> int:
    """Reserve model output separately from the prompt input budget."""
    return max(
        context_window_tokens - max_output_tokens - prompt_tokens - safety_margin,
        100,
    )


def _is_context_overflow(error: LLMGenerationError) -> bool:
    text = f"{error} {error.details or ''}".lower()
    markers = ("context length", "context window", "too many tokens", "token limit")
    return error.status_code in {400, 413} and any(marker in text for marker in markers)


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


def main() -> None:
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
        default=50,
        help="Max characters for the generated commit message (subject)",
    )
    parser.add_argument("--timeout", type=int, help="Timeout in seconds")
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
        "--confirm",
        type=str,
        default="y",
        choices=["y", "n"],
        help="Confirm before committing (y/n)",
    )

    args = parser.parse_args()
    config = get_llm_config(args)

    if args.show_config:
        config_dict = {k: v for k, v in config.__dict__.items() if v is not None}
        if config_dict.get("api_key"):
            config_dict["api_key"] = "***"
        print(
            Panel(
                str(config_dict),
                title="[bold blue]✅ Current Configuration[/bold blue]",
                border_style="blue",
            )
        )
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
    if len(change_groups) > 1:
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
        if args.confirm == "y":
            proceed = Prompt.ask(
                "Generate one message for all staged changes?", choices=["y", "n"], default="y"
            )
            if proceed == "n":
                return

    repository_context = get_repository_context()
    base_prompt = generate_prompt(
        "",
        language=args.language,
        emoji=args.emoji,
        type_=args.type,
        max_subject_chars=args.max_subject_chars,
        repository_context=repository_context,
    )
    system_prompt_tokens = count_tokens(base_prompt, config.model, config.provider)

    diff_token_budget = _calculate_diff_token_budget(
        config.context_window_tokens,
        config.max_tokens,
        system_prompt_tokens,
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
            "diff_budget_tokens": diff_token_budget,
            "original_diff_tokens": original_diff_tokens,
            "final_diff_tokens": final_diff_tokens,
            "diff_compressed": diff != original_diff,
            "change_groups": [group.name for group in change_groups],
        }
        print(Panel(str(diagnostics), title="Debug diagnostics", border_style="blue"))

    try:
        guidance = ""
        context_retry_used = False
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
                with spinner("🚀 Generating commit message..."):
                    raw_message = client.generate(prompt)
            except LLMGenerationError as error:
                if not context_retry_used and _is_context_overflow(error):
                    reduced_budget = max(
                        count_tokens(diff, config.model, config.provider) // 2, 100
                    )
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
                                f"Context overflow detected; retrying with {reduced_budget} "
                                "diff tokens.",
                                title="Debug diagnostics",
                                border_style="blue",
                            )
                        )
                    continue
                raise
            if not raw_message:
                raise CommitMessageError("model returned an empty response")

            try:
                commit_msg = parse_generated_commit(
                    raw_message,
                    max_subject_chars=args.max_subject_chars,
                    emoji=args.emoji,
                )
            except CommitMessageError as error:
                if args.confirm == "n":
                    raise
                print(Panel(str(error), title="Invalid generated message", border_style="yellow"))
                retry = Prompt.ask("Regenerate?", choices=["r", "n"], default="r")
                if retry == "r":
                    guidance = str(error)
                    continue
                return

            _show_commit_message(commit_msg)
            while True:
                action = "c"
                if args.confirm == "y":
                    action = Prompt.ask(
                        "Choose an action: commit, edit, regenerate, or cancel",
                        choices=["c", "e", "r", "n"],
                        default="n",
                    )

                if action == "r":
                    guidance = Prompt.ask(
                        "Optional guidance for regeneration", default="", show_default=False
                    )
                    break
                if action == "e":
                    edited = _edit_commit_message(commit_msg)
                    try:
                        commit_msg = validate_commit_message(edited, args.max_subject_chars)
                    except CommitMessageError as error:
                        print(
                            Panel(str(error), title="Invalid edited message", border_style="yellow")
                        )
                        continue
                    _show_commit_message(commit_msg)
                    if args.confirm == "y":
                        action = Prompt.ask(
                            "Commit the edited message?", choices=["c", "n"], default="n"
                        )
                if action == "n":
                    print(
                        Panel(
                            "[bold yellow]Commit cancelled.[/bold yellow]",
                            title="[bold yellow]Cancelled[/bold yellow]",
                            border_style="yellow",
                        )
                    )
                    return
                if action == "c":
                    if not _run_commit(commit_msg):
                        if args.confirm == "n":
                            return
                        continue
                    push_input = Prompt.ask(
                        "Do you want to push changes?", choices=["y", "n"], default="n"
                    )
                    if push_input.lower() == "y":
                        _run_push()
                    return
    except (EOFError, KeyboardInterrupt):
        print(
            Panel(
                "[bold yellow]Operation cancelled by user.[/bold yellow]",
                title="[bold yellow]Cancelled[/bold yellow]",
                border_style="yellow",
            )
        )
    except LLMGenerationError as e:
        from rich.markup import escape

        details = []
        if e.status_code is not None:
            details.append(f"Status: {e.status_code}")
        if e.details:
            details.append(e.details.strip())
        error_message = escape("\n".join(details) or str(e))
        print(
            Panel(
                "❌ LLM request failed:\n" + error_message,
                title="Error",
                border_style="red",
            )
        )
    except Exception as e:
        from rich.markup import escape

        error_message = escape(str(e))
        print(Panel("❌ An error occurred: " + error_message, title="Error", border_style="red"))


if __name__ == "__main__":
    main()
