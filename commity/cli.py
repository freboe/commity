import argparse
import subprocess
from importlib import metadata
from rich import print
from rich.panel import Panel
from rich.markdown import Markdown
from rich.rule import Rule
from rich.prompt import Prompt
from commity.config import get_llm_config
from commity.core import get_git_diff, generate_prompt
from commity.llm import llm_client_factory
from commity.utils.prompt_organizer import summary_and_tokens_checker
from commity.utils.spinner import spinner

def main():
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
    parser.add_argument("--language", type=str, default="en", help="Language for commit message")
    parser.add_argument("--temperature", type=float, help="Temperature for generation")
    parser.add_argument("--max_tokens", type=int, help="Max tokens for generation")
    parser.add_argument("--timeout", type=int, help="Timeout in seconds")
    parser.add_argument("--proxy", type=str, help="Proxy URL")
    parser.add_argument("--emoji", action="store_true", help="Include emojis")
    parser.add_argument("--type", type=str, default="conventional", help="Commit style type")
    parser.add_argument("--show-config", action="store_true", help="Show current configuration")
    parser.add_argument("--confirm", type=str, default="y", choices=['y', 'n'], help="Confirm before committing (y/n)")

    args = parser.parse_args()
    config = get_llm_config(args)

    if args.show_config:
        config_dict = {k: v for k, v in config.__dict__.items() if v is not None}
        print(Panel(str(config_dict), title="[bold blue]✅ Current Configuration[/bold blue]", border_style="blue"))
        return

    client = llm_client_factory(config)

    diff = get_git_diff()
    if not diff:
        print(Panel("[bold yellow]⚠️ No staged changes detected.[/bold yellow]", title="[bold yellow]Warning[/bold yellow]", border_style="yellow"))
        return
    else:
        diff = summary_and_tokens_checker(diff, config.max_tokens, config.model)


    prompt = generate_prompt(diff, language=args.language, emoji=args.emoji, type_=args.type)
    try:
        with spinner("🚀 Generating commit message..."):
            commit_msg = client.generate(prompt)
        if commit_msg:
            # print(Panel(Markdown(commit_msg), title="[bold green]✅ Suggested Commit Message[/bold green]", border_style="none"))
            print(Rule("[bold green] Suggested Commit Message[/bold green]"))
            print(Markdown(commit_msg))
            print(Rule(style="green"))
            if args.confirm == 'y':
                # confirm_input = input("Do you want to commit with this message? (y/N): ")
                confirm_input = Prompt.ask("Do you want to commit with this message?", choices=["y", "n"], default="n")
                if confirm_input.lower() == "y":
                    try:
                        subprocess.run(["git", "commit", "-m", commit_msg], check=True)
                        print(Panel("[bold green]✅ Committed successfully.[/bold green]", title="Success", border_style="green"))
                    except subprocess.CalledProcessError as e:
                        print(Panel(f"[bold red]❌ Failed to commit: {e}[/bold red]", title="Error", border_style="red"))
        else:
            print(Panel("[bold red]❌ Failed to generate commit message.[/bold red]", title="Error", border_style="red"))
    except Exception as e:
        from rich.markup import escape
        error_message = escape(str(e))
        print(Panel("❌ An error occurred: " + error_message, title="Error", border_style="red"))

if __name__ == "__main__":
    main()
