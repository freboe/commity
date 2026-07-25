"""Tests for CLI prompt token budgeting."""

import pytest

from commity.cli import _calculate_diff_token_budget, _is_context_overflow
from commity.llm import LLMGenerationError


def test_output_limit_is_reserved_separately_from_context_window():
    small_output_budget = _calculate_diff_token_budget(32768, 128, 1000)
    large_output_budget = _calculate_diff_token_budget(32768, 512, 1000)

    assert small_output_budget == 31128
    assert large_output_budget == 30744
    assert large_output_budget > 30000


def test_rejects_budget_when_fixed_content_exceeds_context_window():
    with pytest.raises(ValueError, match="cannot fit the base prompt"):
        _calculate_diff_token_budget(1000, 512, 900)


def test_detects_context_overflow_errors():
    error = LLMGenerationError(
        "bad request",
        status_code=400,
        details="maximum context length exceeded",
    )

    assert _is_context_overflow(error) is True


def test_does_not_retry_unrelated_bad_requests():
    error = LLMGenerationError("invalid API key", status_code=400)

    assert _is_context_overflow(error) is False
