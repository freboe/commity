import argparse
import subprocess
from importlib import metadata

from rich import print
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from rich.rule import Rule

from commity.config import get_llm_config
from commity.core import generate_prompt, get_git_diff
from commity.llm import LLMGenerationError, llm_client_factory
from commity.utils.commit_cleaner import clean_thinking_process
from commity.utils.prompt_organizer import summary_and_tokens_checker
from commity.utils.spinner import spinner
from commity.utils.token_counter import count_tokens


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


def _enforce_subject_limit(commit_msg: str, max_subject_chars: int | None) -> str:
    if not max_subject_chars or max_subject_chars <= 0:
        return commit_msg

    lines = commit_msg.splitlines()
    if not lines:
        return commit_msg

    subject = lines[0].strip()
    if len(subject) <= max_subject_chars:
        return commit_msg

    # truncated = subject[:max_subject_chars].rstrip()
    # lines[0] = truncated
    return "\n".join(lines).strip()


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
        print(
            Panel(
                str(config_dict),
                title="[bold blue]✅ Current Configuration[/bold blue]",
                border_style="blue",
            )
        )
        return

    client = llm_client_factory(config)

    diff = get_git_diff()
    if not diff:
        print(
            Panel(
                "[bold yellow]⚠️ No staged changes detected.[/bold yellow]",
                title="[bold yellow]Warning[/bold yellow]",
                border_style="yellow",
            )
        )
        return

    base_prompt = generate_prompt(
        "",
        language=args.language,
        emoji=args.emoji,
        type_=args.type,
        max_subject_chars=args.max_subject_chars,
    )
    system_prompt_tokens = count_tokens(base_prompt, config.model, config.provider)

    diff_token_budget = max(config.max_tokens - system_prompt_tokens, 100)
    diff = summary_and_tokens_checker(
        diff, max_output_tokens=diff_token_budget, model_name=config.model, provider=config.provider
    )

    prompt = generate_prompt(
        diff,
        language=args.language,
        emoji=args.emoji,
        type_=args.type,
        max_subject_chars=args.max_subject_chars,
    )
    try:
        with spinner("🚀 Generating commit message..."):
            commit_msg = client.generate(prompt)
        if commit_msg:
            commit_msg = clean_thinking_process(commit_msg.strip())
            commit_msg = _enforce_subject_limit(commit_msg, args.max_subject_chars)

            print(Rule("[bold green] Suggested Commit Message[/bold green]"))
            print(Markdown(commit_msg))
            print(Rule(style="green"))
            should_commit = True
            if args.confirm == "y":
                confirm_input = Prompt.ask(
                    "Do you want to commit with this message?", choices=["y", "n"], default="n"
                )
                should_commit = confirm_input.lower() == "y"

            if should_commit:
                if _run_commit(commit_msg):
                    push_input = Prompt.ask(
                        "Do you want to push changes?", choices=["y", "n"], default="n"
                    )
                    if push_input.lower() == "y":
                        _run_push()
            else:
                print(
                    Panel(
                        "[bold yellow]Commit aborted by user confirmation.[/bold yellow]",
                        title="[bold yellow]Cancelled[/bold yellow]",
                        border_style="yellow",
                    )
                )
        else:
            print(
                Panel(
                    "[bold red]❌ Failed to generate commit message.[/bold red]",
                    title="Error",
                    border_style="red",
                )
            )
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
