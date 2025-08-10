import subprocess

def get_git_diff() -> str:
    try:
        result = subprocess.run(["git", "diff", "--cached"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return result.stdout.strip()
    except Exception as e:
        print(f"[Git Error] {e}")
        return ""

def generate_prompt(diff: str, language: str = "en", emoji: bool = True, type_: str = "conventional") -> str:
    prompt = f"Generate a concise git commit message in {language} based on the following diff:\n\n{diff}\n"
    if emoji:
        prompt += "Include appropriate emojis.\n"
    if type_ == "conventional":
        prompt += "Use Conventional Commits style."
    return prompt
