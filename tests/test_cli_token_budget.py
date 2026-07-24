"""Tests for CLI prompt token budgeting."""

from commity.cli import _calculate_diff_token_budget


def test_output_limit_is_reserved_separately_from_context_window():
    small_output_budget = _calculate_diff_token_budget(32768, 128, 1000)
    large_output_budget = _calculate_diff_token_budget(32768, 512, 1000)

    assert small_output_budget == 31128
    assert large_output_budget == 30744
    assert large_output_budget > 30000
