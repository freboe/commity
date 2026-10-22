"""Behavioral checks for prompt budgeting without CLI interaction."""

import pytest

from commity.config import LLMConfig
from commity.prompt_budget import prepare_diff
from commity.utils.token_counter import TOKEN_SAFETY_MARGIN, count_tokens


@pytest.mark.parametrize("context_window", [4_000, 100_000])
def test_reserves_tool_capacity_before_compressing(mocker, context_window):
    config = LLMConfig(
        provider="ollama",
        base_url="http://localhost:11434",
        model="llama3",
        max_tokens=512,
        context_window_tokens=context_window,
        debug=True,
    )
    compress = mocker.patch(
        "commity.prompt_budget.summary_and_tokens_checker", return_value="compressed diff"
    )
    prepared = prepare_diff(
        "large diff",
        "base prompt including repository context",
        config,
        repository_context="repository context",
        tool_definitions=[{"type": "function", "function": {"name": "read_file"}}],
    )
    diagnostics = prepared.diagnostics
    available = (
        context_window
        - config.max_tokens
        - TOKEN_SAFETY_MARGIN
        - diagnostics["prompt_without_diff_tokens"]
        - diagnostics["tool_schema_tokens"]
    )
    expected_reserve = min(8192, available // 4)

    assert diagnostics["tool_result_reserve"] == expected_reserve
    assert diagnostics["diff_budget_tokens"] == available - expected_reserve
    assert diagnostics["diff_compressed"] is True
    assert prepared.diff == "compressed diff"
    compress.assert_called_once_with(
        "large diff",
        max_output_tokens=available - expected_reserve,
        model_name="llama3",
        provider="ollama",
    )


def test_small_diff_is_preserved_without_tools():
    config = LLMConfig(
        provider="ollama", base_url="http://localhost:11434", model="llama3", debug=True
    )
    prepared = prepare_diff("small diff", "base prompt", config)

    assert prepared.diff == "small diff"
    assert prepared.diagnostics["tool_schema_tokens"] == 0
    assert prepared.diagnostics["tool_result_reserve"] == 0
    assert prepared.diagnostics["diff_compressed"] is False


def test_large_diff_fits_budget_without_presentation():
    config = LLMConfig(
        provider="ollama",
        base_url="http://localhost:11434",
        model="llama3",
        context_window_tokens=2_000,
        debug=True,
    )
    prepared = prepare_diff("line of changes\n" * 2_000, "base prompt", config)

    assert prepared.diff
    assert (
        count_tokens(prepared.diff, config.model, config.provider)
        <= prepared.diagnostics["diff_budget_tokens"]
    )


def test_impossible_budget_fails_before_compression(mocker):
    config = LLMConfig(
        provider="ollama",
        base_url="http://localhost:11434",
        model="llama3",
        max_tokens=500,
        context_window_tokens=600,
    )
    compress = mocker.patch("commity.prompt_budget.summary_and_tokens_checker")

    with pytest.raises(ValueError, match="cannot fit the base prompt"):
        prepare_diff("diff", "base prompt", config)

    compress.assert_not_called()
