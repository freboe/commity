import subprocess


def get_git_diff() -> str:
    try:
        result = subprocess.run(["git", "diff", "--staged"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return result.stdout.strip()
    except Exception as e:
        print(f"[Git Error] {e}")
        return ""

def generate_prompt(diff: str, language: str = "en", emoji: bool = True, type_: str = "conventional", max_subject_chars: int = 50) -> str:
    prompt = f"""As an expert in writing clear, concise, and informative Git commit messages, your task is to generate a commit message in {language} based on the provided Git diff.

Follow these rules:
- The header (first line) must not exceed {max_subject_chars} characters.
- The body (optional) should provide more details, with each line not exceeding 72 characters.
- A footer (optional) can be used for `BREAKING CHANGE` or referencing issues (e.g., `Closes #123`)."""

    if type_ == "conventional":
        prompt += """
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

    if emoji:
        prompt += """- Use emojis in the subject line, mapping the commit type to a specific emoji. Here is the mapping:
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
    else:
        prompt += "- Do not include emojis.\n"

    prompt += f"""
Git Diff:
{diff}
    """

    return prompt
