import re
from functools import lru_cache

import tiktoken


def check_diff_length(diff_text, threshold=15000):
    if len(diff_text) > threshold:
        return True, f"⚠️ Diff too long ({len(diff_text)} characters), it is recommended to submit in batches or simplify changes。"
    return False, ""


def generate_prompt_summary(diff_text):
    # 提取文件名和修改行数（示例用 git diff 结构）
    files = re.findall(r'diff --git a/(.+?) ', diff_text)
    summary = [f"- Change File：{file}" for file in files[:10]]  # 限制前10项
    return "📝 Change Summary：\n" + "\n".join(summary)


def compress_diff_to_bullets(diff_text, max_lines=200):
    lines = diff_text.splitlines()
    compressed = []

    for line in lines:
        if line.startswith('+') and not line.startswith('+++'):
            compressed.append(f"- Add：{line[1:].strip()}")
        elif line.startswith('-') and not line.startswith('---'):
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

    warning_triggered, warning_msg = check_diff_length(diff_text)
    prompt_summary = generate_prompt_summary(diff_text)
    compressed_diff = compress_diff_to_bullets(diff_text)

    # 构建最终提示
    prompt = f"{warning_msg}\n{prompt_summary}\n\n🔍 Change details (compressed version)：\n{compressed_diff}"

    final_prompt = prompt
    len_prompt = len(final_prompt)
    step_size = 100
    while count_tokens(final_prompt, model_name) > max_user_tokens and len_prompt > step_size:
        final_prompt = final_prompt[:(len_prompt - step_size)]
        len_prompt = len(final_prompt)
    has_truncated = len_prompt < len(prompt)
    if has_truncated:
        final_prompt = final_prompt + "\n...<truncated>"

    return final_prompt
