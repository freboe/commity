"""Prepare diff input within model limits, independently of CLI presentation."""

import json
from dataclasses import dataclass
from typing import TYPE_CHECKING

from commity.utils.prompt_organizer import summary_and_tokens_checker
from commity.utils.token_counter import TOKEN_SAFETY_MARGIN, count_tokens

if TYPE_CHECKING:
    from commity.config import LLMConfig

MAX_TOOL_TOKEN_RESERVE = 8_192


@dataclass(frozen=True)
class PreparedDiff:
    """Compressed input and diagnostics for the caller to present."""

    diff: str
    diagnostics: dict[str, object]


def calculate_diff_token_budget(
    context_window_tokens: int,
    max_output_tokens: int,
    prompt_tokens: int,
    safety_margin: int = TOKEN_SAFETY_MARGIN,
) -> int:
    """Reserve model output separately from the prompt input budget."""
    budget = context_window_tokens - max_output_tokens - prompt_tokens - safety_margin
    if budget <= 0:
        raise ValueError(
            "Model context window cannot fit the base prompt, output reserve, and safety margin"
        )
    return budget


def prepare_diff(
    original_diff: str,
    base_prompt: str,
    config: "LLMConfig",
    repository_context: str = "",
    tool_definitions: list[dict] | None = None,
) -> PreparedDiff:
    """Reserve output and tool capacity before compressing staged changes."""
    system_prompt_tokens = count_tokens(base_prompt, config.model, config.provider)
    tool_schema_tokens = 0
    tool_result_reserve = 0
    if tool_definitions is not None:
        serialized_tools = json.dumps(
            tool_definitions,
            ensure_ascii=False,
            separators=(",", ":"),
        )
        tool_schema_tokens = count_tokens(serialized_tools, config.model, config.provider)
        available_for_content = calculate_diff_token_budget(
            config.context_window_tokens,
            config.max_tokens,
            system_prompt_tokens + tool_schema_tokens,
        )
        tool_result_reserve = min(MAX_TOOL_TOKEN_RESERVE, available_for_content // 4)

    diff_token_budget = calculate_diff_token_budget(
        config.context_window_tokens,
        config.max_tokens,
        system_prompt_tokens + tool_schema_tokens + tool_result_reserve,
    )
    original_diff_tokens = count_tokens(original_diff, config.model, config.provider)
    diff = summary_and_tokens_checker(
        original_diff,
        max_output_tokens=diff_token_budget,
        model_name=config.model,
        provider=config.provider,
    )
    final_diff_tokens = count_tokens(diff, config.model, config.provider)

    diagnostics: dict[str, object] = {}
    if config.debug:
        diagnostics = {
            "provider": config.provider,
            "model": config.model,
            "context_window_tokens": config.context_window_tokens,
            "max_output_tokens": config.max_tokens,
            "repository_context_tokens": count_tokens(
                repository_context, config.model, config.provider
            ),
            "prompt_without_diff_tokens": system_prompt_tokens,
            "tool_schema_tokens": tool_schema_tokens,
            "tool_result_reserve": tool_result_reserve,
            "diff_budget_tokens": diff_token_budget,
            "original_diff_tokens": original_diff_tokens,
            "final_diff_tokens": final_diff_tokens,
            "diff_compressed": diff != original_diff,
        }

    return PreparedDiff(diff=diff, diagnostics=diagnostics)
