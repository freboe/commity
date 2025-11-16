"""Git Diff 组织和智能压缩工具.

提供三级压缩策略：
1. 原始 diff（如果在 token 限制内）
2. 结构化压缩（基于文件重要性优先级）
3. 简单行压缩（fallback）
"""

import re
from dataclasses import dataclass
from typing import Final

from unidiff import PatchSet

from commity.utils.token_counter import count_tokens

# ============================================================================
# 常量配置
# ============================================================================

MAX_DIFF_LENGTH: Final[int] = 15000  # 单个 diff 的最大字符数
MAX_FILES_IN_SUMMARY: Final[int] = 30  # 摘要中最多显示的文件数
MAX_COMPRESSED_LINES: Final[int] = 1000  # 压缩模式下的最大行数
MAX_HUNKS_PER_FILE: Final[int] = 5  # 每个文件最多显示的 hunk 数
MAX_LINES_PER_HUNK: Final[int] = 10  # 每个 hunk 最多显示的行数


# ============================================================================
# 数据结构
# ============================================================================


@dataclass
class FileImportance:
    """文件变更重要性评分."""

    path: str  # 文件路径
    score: int  # 重要性分数（越高越重要）
    added: int  # 新增行数
    removed: int  # 删除行数


# ============================================================================
# 第一部分：文件重要性评估
# ============================================================================


def calculate_file_importance(file_path: str, added: int, removed: int) -> int:
    """计算文件的重要性分数.

    评分规则：
    - 核心源代码文件（.py, .js, .ts 等）: 基础分 10
    - 配置文件（.json, .yaml 等）: 基础分 5
    - 测试和文档: 基础分 2
    - Lock 文件: 基础分 1
    - 变更行数贡献（上限 50）

    Args:
    ----
        file_path: 文件路径
        added: 新增行数
        removed: 删除行数

    Returns:
    -------
        重要性分数（越高越重要）

    """
    score = 0

    # 1. 根据文件类型评分
    if file_path.endswith((".py", ".js", ".ts", ".go", ".rs", ".java", ".cpp", ".c")):
        score += 10  # 核心源代码
    elif file_path.endswith((".json", ".yaml", ".yml", ".toml", ".ini", ".conf")):
        score += 5  # 配置文件
    elif "test" in file_path.lower() or file_path.endswith((".md", ".txt", ".rst")):
        score += 2  # 测试和文档
    elif file_path in ("package-lock.json", "yarn.lock", "Cargo.lock", "poetry.lock"):
        score += 1  # Lock 文件（最低优先级）

    # 2. 特殊文件加分
    if file_path in ("README.md", "pyproject.toml", "package.json", "Cargo.toml"):
        score += 8

    # 3. 变更规模贡献（上限 50）
    change_size = min(added + removed, 50)
    score += change_size

    return score


def rank_files_by_importance(patch: PatchSet) -> list[FileImportance]:
    """对所有变更文件按重要性排序.

    Args:
    ----
        patch: unidiff 解析的 PatchSet 对象

    Returns:
    -------
        按重要性降序排列的文件列表

    """
    file_list = []

    for patched_file in patch:
        score = calculate_file_importance(
            patched_file.path, patched_file.added, patched_file.removed
        )
        file_list.append(
            FileImportance(
                path=patched_file.path,
                score=score,
                added=patched_file.added,
                removed=patched_file.removed,
            )
        )

    # 按分数降序排序
    file_list.sort(key=lambda x: x.score, reverse=True)

    return file_list


# ============================================================================
# 第二部分：Diff 内容提取和格式化
# ============================================================================


def extract_hunk_context(hunk) -> str:
    """从 hunk 中提取函数/类名上下文.

    Args:
    ----
        hunk: unidiff 的 Hunk 对象

    Returns:
    -------
        格式化的上下文字符串，如 "  ↳ def function_name(...)"

    """
    if not hunk.section_header:
        return ""

    # 清理函数签名
    header = hunk.section_header.strip()
    # 移除常见的函数定义关键字
    header = re.sub(r"^(def|class|function|func|fn|public|private|protected)\s+", "", header)

    if header:
        return f"  ↳ {header}"

    return ""


def extract_hunk_changes(hunk, max_lines: int = MAX_LINES_PER_HUNK) -> tuple[list[str], list[str]]:
    """提取 hunk 中的关键变更.

    Args:
    ----
        hunk: unidiff 的 Hunk 对象
        max_lines: 每个 hunk 最多提取的行数

    Returns:
    -------
        (removed_lines, added_lines) 元组

    """
    added_lines = []
    removed_lines = []
    line_count = 0

    for line in hunk:
        if line_count >= max_lines:
            break

        # 跳过 import 语句（通常不是关键变更）
        if line.value.strip().startswith(("import ", "from ")):
            continue

        if line.is_added:
            added_lines.append(f"    + {line.value.rstrip()}")
            line_count += 1
        elif line.is_removed:
            removed_lines.append(f"    - {line.value.rstrip()}")
            line_count += 1

    return removed_lines, added_lines


def format_file_summary(patched_file, max_hunks: int = MAX_HUNKS_PER_FILE) -> str:
    """格式化单个文件的变更摘要.

    输出格式：
    📄 **文件路径**
       +X -Y lines
      ↳ 函数/类上下文
        - 删除的行
        + 新增的行

    Args:
    ----
        patched_file: unidiff 的 PatchedFile 对象
        max_hunks: 最多显示的 hunk 数量

    Returns:
    -------
        格式化的文件摘要字符串

    """
    lines = [
        f"📄 **{patched_file.path}**",
        f"   +{patched_file.added} -{patched_file.removed} lines",
    ]

    for idx, hunk in enumerate(patched_file):
        if idx >= max_hunks:
            remaining = len(patched_file) - max_hunks
            lines.append(f"   ... +{remaining} more hunks")
            break

        # 添加上下文
        context = extract_hunk_context(hunk)
        if context:
            lines.append(context)

        # 提取变更
        removed_lines, added_lines = extract_hunk_changes(hunk)

        # 先显示删除，再显示新增（更符合 diff 习惯）
        lines.extend(removed_lines[:5])
        lines.extend(added_lines[:5])

    return "\n".join(lines)


# ============================================================================
# 第三部分：压缩策略实现
# ============================================================================


def compress_with_structure(diff_text: str, max_tokens: int, model_name: str, provider: str) -> str:
    """策略2：结构化压缩（基于优先级）.

    工作流程：
    1. 使用 unidiff 解析 diff 为结构化数据
    2. 计算每个文件的重要性分数
    3. 按优先级排序
    4. 逐个添加文件，直到达到 token 限制

    Args:
    ----
        diff_text: 原始 git diff 文本
        max_tokens: token 限制
        model_name: 模型名称
        provider: LLM provider

    Returns:
    -------
        结构化压缩后的 diff 文本

    """
    try:
        patch = PatchSet(diff_text)
    except Exception:
        # 解析失败，降级到简单压缩
        return compress_with_lines(diff_text, MAX_COMPRESSED_LINES)

    # 1. 评估并排序文件
    ranked_files = rank_files_by_importance(patch)

    if not ranked_files:
        return "No changes detected."

    # 2. 构建文件映射（方便查找）
    files_map = {pf.path: pf for pf in patch}

    # 3. 逐个添加文件（优先级高的先加）
    result_parts: list[str] = []
    total_files = len(ranked_files)

    for file_info in ranked_files:
        patched_file = files_map.get(file_info.path)
        if not patched_file:
            continue

        # 生成这个文件的摘要
        file_summary = format_file_summary(patched_file)

        # 尝试添加，检查是否超出限制
        test_content = "\n\n".join([*result_parts, file_summary])
        if count_tokens(test_content, model_name, provider) > max_tokens:
            # 如果一个文件都没添加，至少添加一个简化版本
            if not result_parts:
                minimal = (
                    f"📄 **{file_info.path}**\n   +{file_info.added} -{file_info.removed} lines"
                )
                result_parts.append(minimal)
            break

        result_parts.append(file_summary)

    # 4. 生成头部信息
    shown_files = len(result_parts)
    header_lines = [f"📝 Changes in {shown_files}/{total_files} files (sorted by importance):"]

    if shown_files < total_files:
        omitted = total_files - shown_files
        header_lines.append(f"⚠️ {omitted} files omitted due to space constraints")

    header = "\n".join(header_lines)

    return header + "\n\n" + "\n\n".join(result_parts)


def compress_with_lines(diff_text: str, max_lines: int = MAX_COMPRESSED_LINES) -> str:
    """策略3：简单行压缩（fallback）.

    将 diff 压缩为简单的文件 + 变更列表格式。
    当结构化解析失败或需要更激进的压缩时使用。

    Args:
    ----
        diff_text: 原始 git diff 文本
        max_lines: 最多保留的行数

    Returns:
    -------
        行压缩后的 diff 文本

    """
    lines = diff_text.splitlines()
    compressed = []
    current_file = None

    for line in lines:
        # 识别文件头
        if line.startswith("diff --git"):
            match = re.search(r"diff --git a/(.+?) b/", line)
            if match:
                current_file = match.group(1)
                compressed.append(f"\n📄 {current_file}")

        # 提取变更行
        elif line.startswith("+") and not line.startswith("+++"):
            compressed.append(f"  + {line[1:].strip()}")
        elif line.startswith("-") and not line.startswith("---"):
            compressed.append(f"  - {line[1:].strip()}")

        # 达到行数限制
        if len(compressed) >= max_lines:
            compressed.append("\n...<truncated>")
            break

    return "\n".join(compressed)


# ============================================================================
# 第四部分：主入口函数
# ============================================================================


def summary_and_tokens_checker(
    diff_text: str, max_output_tokens: int, model_name: str, provider: str = "openai"
) -> str:
    """智能 Diff 压缩的主入口函数.

    三级压缩策略：
    ┌─────────────────────────────────┐
    │ 策略1: 原始 diff                │
    │ 条件: token_count ≤ limit      │
    │ 优点: 保留完整信息              │
    └─────────────────────────────────┘
              ↓ (超出限制)
    ┌─────────────────────────────────┐
    │ 策略2: 结构化压缩               │
    │ 方法: 优先级排序 + 选择性保留  │
    │ 优点: 保留重要文件和上下文      │
    └─────────────────────────────────┘
              ↓ (仍超出限制)
    ┌─────────────────────────────────┐
    │ 策略3: 简单行压缩               │
    │ 方法: 提取 +/- 行，限制行数     │
    │ 优点: 极限压缩，必定成功        │
    └─────────────────────────────────┘

    Args:
    ----
        diff_text: Git diff 文本
        max_output_tokens: token 上限
        model_name: 模型名称（用于 token 计数）
        provider: LLM provider（openai/gemini/ollama/openrouter）

    Returns:
    -------
        处理后的 diff 文本（确保在 token 限制内）

    """
    # 策略1：检查原始 diff 是否满足限制
    original_tokens = count_tokens(diff_text, model_name, provider)
    if original_tokens <= max_output_tokens:
        return diff_text

    # 策略2：结构化压缩
    compressed = compress_with_structure(diff_text, max_output_tokens, model_name, provider)
    compressed_tokens = count_tokens(compressed, model_name, provider)

    if compressed_tokens <= max_output_tokens:
        return compressed

    # 策略3：简单行压缩（fallback）
    # 估算可以保留的行数
    avg_tokens_per_line = compressed_tokens / max(len(compressed.splitlines()), 1)
    safe_lines = int(max_output_tokens / avg_tokens_per_line * 0.8)  # 80% 安全边界
    safe_lines = max(safe_lines, 50)  # 至少保留 50 行

    fallback = compress_with_lines(diff_text, max_lines=safe_lines)

    # 添加警告信息
    if len(diff_text) > MAX_DIFF_LENGTH:
        warning = (
            f"⚠️ Diff too long ({len(diff_text)} characters), "
            "it is recommended to submit in batches or simplify changes。\n\n"
        )
        return warning + fallback

    return fallback
