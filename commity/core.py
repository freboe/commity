import subprocess


def get_git_diff() -> str:
    try:
        result = subprocess.run(["git", "diff", "--cached"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return result.stdout.strip()
    except Exception as e:
        print(f"[Git Error] {e}")
        return ""

def generate_prompt(diff: str, language: str = "en", emoji: bool = True, type_: str = "conventional", max_subject_chars: int = 50) -> str:
    prompt = f"""As an expert in writing clear, concise, and informative Git commit messages, your task is to generate a commit message in {language} based on the provided Git diff.

Follow these rules:
- First line (title) should briefly summarize the change in ≤{max_subject_chars} characters, starting with a type prefix, no period at the end.
- Leave one blank line after the title.
- Body (optional) should describe motivation, background, implementation details, or impact, in 1–3 paragraphs, with ≤72 characters per line.
- If related to an issue/task, reference it at the end of the body, e.g.:
   - Closes #123
   - Related to #456
"""
    if emoji:
        prompt += "- Include appropriate emojis in the subject line.\n"
    else:
        prompt += "- Do not include emojis in the subject line.\n"
    if type_ == "conventional":
        prompt += "- Use Conventional Commits style (e.g., 'feat: add new feature', 'fix: resolve bug').\n"

    prompt += f"""
Git Diff:
{diff}
    """

    return prompt
