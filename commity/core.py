import subprocess


def get_git_diff() -> str:
    try:
        result = subprocess.run(
            ["git", "diff", "--staged"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,  # Add check=True to raise CalledProcessError for non-zero exit codes
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"[Git Error] Command '{e.cmd}' failed with exit code {e.returncode}.")
        print(f"Stderr: {e.stderr.strip()}")
        return ""
    except Exception as e:
        print(f"[Git Error] An unexpected error occurred: {e}")
        return ""


def generate_prompt(
    diff: str,
    language: str = "en",
    emoji: bool = True,
    type_: str = "conventional",
    max_subject_chars: int = 50,
) -> str:
    base_rules = f"""You are a Git commit message generator. Generate a commit message in {language} based on the provided Git diff.

CRITICAL: Your response must contain ONLY the commit message text. Do NOT include:
- Any thinking process, analysis, or reasoning
- Phrases like "Let me analyze", "Looking at", "This appears to be", "Let me craft", "I'll focus on"
- Any explanation of your thought process
- Any preamble, introduction, or conclusion
- Any markdown formatting or code blocks

Start your response directly with the commit message. The first line should be the commit subject line.

Follow these rules:
- First line (title) should briefly summarize the change in ≤{max_subject_chars} characters, starting with a type prefix, no period at the end.
    - Type prefix must be lowercase.
    - Separate subject from body with a blank line.
- The body (optional) should provide more details, with each line not exceeding 72 characters.
- A footer (optional) can be used for `BREAKING CHANGE` or referencing issues (e.g., `Closes #123`).
- The output must be plain text, without any markdown syntax (e.g., no ` ``` `, `*`, `-`, etc.).
- Output the commit message directly, without any preamble or explanation."""

    conventional_rules = """
- The commit message must follow the Conventional Commits specification.
- The format is: `type(scope): description`.
  - `type`: Must be one of the following:
    - `feat`: A new feature.
    - `fix`: A bug fix.
    - `docs`: Documentation only changes.
    - `style`: Changes that do not affect the meaning of the code (white-space, formatting, missing semi-colons, etc).
    - `refactor`: A code change that neither fixes a bug nor adds a feature.
    - `perf`: A code change that improves performance.
    - `test`: Adding missing tests or correcting existing tests.
    - `build`: Changes that affect the build system or external dependencies.
    - `ci`: Changes to our CI configuration files and scripts.
    - `chore`: Other changes that don't modify src or test files.
    - `revert`: Reverts a previous commit.
  - `scope` (optional): A noun describing a section of the codebase.
  - `description`: A short summary of the code changes. Use the imperative, present tense (e.g., "add" not "added" nor "adds").
"""

    emoji_rules = """- Use emojis in the subject line, mapping the commit type to a specific emoji. Here is the mapping:
    - feat: ✨ (new feature)
    - fix: 🐛 (bug fix)
    - docs: 📚 (documentation)
    - style: 💎 (code style)
    - refactor: 🔨 (code refactoring)
    - perf: 🚀 (performance improvement)
    - test: 🚨 (tests)
    - build: 📦 (build system)
    - ci: 👷 (CI/CD)
    - chore: 🔧 (chores)
    - revert: ⏪ (revert)
"""

    no_emoji_rule = "- Do not include emojis.\n"

    prompt_parts = [base_rules]

    if type_ == "conventional":
        prompt_parts.append(conventional_rules)

    if emoji:
        prompt_parts.append(emoji_rules)
    else:
        prompt_parts.append(no_emoji_rule)

    prompt_parts.append(f"""
Git Diff:
{diff}

Remember: Output ONLY the commit message. No thinking, no analysis, no explanation. Start directly with the commit subject line.
""")

    return "".join(prompt_parts)
