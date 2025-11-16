import re
from typing import Final

from commity.utils.token_counter import count_tokens

# Constants
MAX_DIFF_LENGTH: Final[int] = 15000
MAX_FILES_IN_SUMMARY: Final[int] = 30
MAX_COMPRESSED_LINES: Final[int] = 1000


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


def _get_chars_per_token_ratio(text: str, provider: str) -> float:
    """根据 provider 和文本内容估算字符/token 比率。

    Args:
    ----
        text: 要分析的文本
        provider: LLM provider

    Returns:
    -------
        字符/token 的估算比率

    """
    # 检测 CJK 字符占比
    cjk_count = sum(1 for char in text if ord(char) >= 0x4E00 and ord(char) <= 0x9FFF)
    cjk_ratio = cjk_count / len(text) if len(text) > 0 else 0

    # 根据 provider 和文本特征返回不同的比率
    if provider == "gemini":
        if cjk_ratio > 0.3:
            return 2.0  # 中文为主：约 2 字符/token
        return 3.5  # 英文/代码：约 3.5 字符/token

    if provider in ("openai", "openrouter"):
        if cjk_ratio > 0.3:
            return 2.5  # OpenAI 对中文的 token 化较粗
        return 4.0  # 英文标准：4 字符/token

    # Ollama 和其他 provider 使用保守估算
    return 3.5


def summary_and_tokens_checker(
    diff_text: str, max_output_tokens: int, model_name: str, provider: str = "openai"
) -> str:
    """添加总结和压缩版本的diff，构建有效长度的tokens的提示词语，避免过长导致模型生成失败

    采用三级压缩策略：
    1. 检查原始 diff 是否在限制内
    2. 压缩为 bullet points 格式
    3. 强制字符截断（保留关键信息）

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
    # 第一级：检查原始 diff
    token_count = count_tokens(diff_text, model_name, provider)
    if token_count <= max_output_tokens:
        return diff_text

    # 第二级：压缩为 bullet points
    _, warning_msg = check_diff_length(diff_text)
    prompt_summary = generate_prompt_summary(diff_text)
    compressed_diff = compress_diff_to_bullets(diff_text)

    compressed_prompt = f"{warning_msg}\n{prompt_summary}\n\n🔍 Change details (compressed version)：\n{compressed_diff}"

    # 检查压缩后的 token 数（缓存结果避免重复计算）
    compressed_token_count = count_tokens(compressed_prompt, model_name, provider)
    if compressed_token_count <= max_output_tokens:
        return compressed_prompt

    # 第三级：强制截断
    excess_tokens = compressed_token_count - max_output_tokens

    # 根据 provider 动态调整字符/token 比率
    chars_per_token = _get_chars_per_token_ratio(compressed_prompt, provider)
    chars_to_remove = int(excess_tokens * chars_per_token)

    if len(compressed_prompt) > chars_to_remove + 100:  # 保留至少 100 字符
        # 保留前 70% 和后 10%，删除中间部分（保留关键上下文）
        keep_start = int((len(compressed_prompt) - chars_to_remove) * 0.7)
        keep_end = int((len(compressed_prompt) - chars_to_remove) * 0.1)
        truncated_prompt = (
            compressed_prompt[:keep_start]
            + f"\n\n...<truncated {chars_to_remove} chars>...\n\n"
            + compressed_prompt[-keep_end:]
        )
        return truncated_prompt

    # 兜底：如果压缩后还是太长，返回压缩版本让模型尝试处理
    return compressed_prompt
