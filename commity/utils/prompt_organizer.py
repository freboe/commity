import re
from typing import Final

from commity.utils.token_counter import count_tokens

# Constants
MAX_DIFF_LENGTH: Final[int] = 15000
MAX_FILES_IN_SUMMARY: Final[int] = 30
MAX_COMPRESSED_LINES: Final[int] = 1000
TOKEN_ESTIMATE_FACTOR: Final[int] = 4


def check_diff_length(diff_text, threshold=MAX_DIFF_LENGTH):
    if len(diff_text) > threshold:
        return (
            True,
            f"⚠️ Diff too long ({len(diff_text)} characters), it is recommended to submit in batches or simplify changes。",
        )
    return False, ""


def generate_prompt_summary(diff_text):
    # 提取文件名和修改行数（示例用 git diff 结构）
    files = re.findall(r"diff --git a/(.+?) ", diff_text)
    summary = [f"- Change File：{file}" for file in files[:MAX_FILES_IN_SUMMARY]]  # 限制前N项
    return "📝 Change Summary：\n" + "\n".join(summary)


def compress_diff_to_bullets(diff_text, max_lines=MAX_COMPRESSED_LINES):
    lines = diff_text.splitlines()
    compressed = []

    for line in lines:
        if line.startswith("+") and not line.startswith("+++"):
            compressed.append(f"- Add：{line[1:].strip()}")
        elif line.startswith("-") and not line.startswith("---"):
            compressed.append(f"- Delete：{line[1:].strip()}")

        if len(compressed) >= max_lines:
            # compressed.append("...内容已截断")
            compressed.append("...<truncated>")
            break

    return "\n".join(compressed)


def summary_and_tokens_checker(
    diff_text: str, max_output_tokens: int, model_name: str, provider: str = "openai"
) -> str:
    """添加总结和压缩版本的diff，构建有效长度的tokens的提示词语，避免过长导致模型生成失败

    Args:
    ----
        diff_text: Git diff text to check
        max_output_tokens: Maximum tokens allowed
        model_name: Model name for token counting
        provider: LLM provider (openai, gemini, ollama, openrouter)

    Returns:
    -------
        Original or compressed diff text that fits within token limit

    """
    max_user_tokens = max_output_tokens * 1

    token_count = count_tokens(diff_text, model_name, provider)
    if token_count <= max_user_tokens:
        return diff_text

    _, warning_msg = check_diff_length(diff_text)
    prompt_summary = generate_prompt_summary(diff_text)
    compressed_diff = compress_diff_to_bullets(diff_text)

    original_prompt = f"{warning_msg}\n{prompt_summary}\n\n🔍 Change details (compressed version)：\n{compressed_diff}"

    # 构建最终提示，优先使用压缩版本
    final_prompt = original_prompt

    # 再次检查 token 数量，如果仍然过长，则进一步截断
    if count_tokens(final_prompt, model_name, provider) > max_user_tokens:
        # 简单截断，保留开头部分
        # 计算需要截断的字符数
        current_tokens = count_tokens(final_prompt, model_name, provider)
        excess_tokens = current_tokens - max_user_tokens
        # 估算每个 token 对应的字符数，这里简单假设一个 token 约等于 4 个字符（对于英文）
        # 这是一个粗略的估算，实际应根据具体模型和语言调整
        chars_to_remove = excess_tokens * TOKEN_ESTIMATE_FACTOR

        if len(final_prompt) > chars_to_remove:
            final_prompt = final_prompt[: len(final_prompt) - chars_to_remove] + "\n...<truncated>"
        else:
            # 如果压缩后的内容仍然太长，返回 original_prompt 让模型处理，如果模型报错则展示错误信息
            return original_prompt

    return final_prompt
