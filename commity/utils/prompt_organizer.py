import re
from functools import lru_cache

import tiktoken


def check_diff_length(diff_text, threshold=15000):
    if len(diff_text) > threshold:
        return (
            True,
            f"⚠️ Diff too long ({len(diff_text)} characters), it is recommended to submit in batches or simplify changes。",
        )
    return False, ""


def generate_prompt_summary(diff_text):
    # 提取文件名和修改行数（示例用 git diff 结构）
    files = re.findall(r"diff --git a/(.+?) ", diff_text)
    summary = [f"- Change File：{file}" for file in files[:10]]  # 限制前10项
    return "📝 Change Summary：\n" + "\n".join(summary)


def compress_diff_to_bullets(diff_text, max_lines=200):
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


@lru_cache(maxsize=10)
def get_tokenizer(model_name: str):
    try:
        return tiktoken.encoding_for_model(model_name)
    except KeyError:
        return tiktoken.get_encoding("cl100k_base")


def count_tokens(text: str, model_name: str):
    tokenizer = get_tokenizer(model_name)
    return len(tokenizer.encode(text))


def summary_and_tokens_checker(diff_text: str, max_output_tokens: int, model_name: str):
    """添加总结和压缩版本的diff，构建有效长度的tokens的提示词语，避免过长导致模型生成失败
    :param diff_text:
    :param max_output_tokens:
    :return:
    """
    max_user_tokens = max_output_tokens * 1

    token_count = count_tokens(diff_text, model_name)
    if token_count <= max_user_tokens:
        return diff_text

    _, warning_msg = check_diff_length(diff_text)
    prompt_summary = generate_prompt_summary(diff_text)
    compressed_diff = compress_diff_to_bullets(diff_text)

    # 构建最终提示，优先使用压缩版本
    final_prompt = f"{warning_msg}\n{prompt_summary}\n\n🔍 Change details (compressed version)：\n{compressed_diff}"

    # 再次检查 token 数量，如果仍然过长，则进一步截断
    if count_tokens(final_prompt, model_name) > max_user_tokens:
        # 简单截断，保留开头部分
        # 计算需要截断的字符数
        current_tokens = count_tokens(final_prompt, model_name)
        excess_tokens = current_tokens - max_user_tokens
        # 估算每个 token 对应的字符数，这里简单假设一个 token 约等于 4 个字符（对于英文）
        # 这是一个粗略的估算，实际应根据具体模型和语言调整
        chars_to_remove = excess_tokens * 4

        if len(final_prompt) > chars_to_remove:
            final_prompt = final_prompt[: len(final_prompt) - chars_to_remove] + "\n...<truncated>"
        else:
            # 如果整个 prompt 都太长，只保留一个非常短的提示
            final_prompt = (
                "Diff is too large to process. Please stage fewer changes.\n...<truncated>"
            )

    return final_prompt
