"""
Tests for cost calculator module.

Run with: pytest tests/test_cost_calculator.py -v
"""

import pytest
from decimal import Decimal

from instrumentation.cost_calculator import (
    calculate_cost,
    calculate_cost_breakdown,
    get_model_pricing,
    estimate_tokens,
    estimate_cost,
    check_cost_threshold,
    format_cost,
)


class TestCostCalculation:
    """Tests for cost calculation functions."""

    def test_gpt4_cost_calculation(self):
        """Test GPT-4 cost calculation."""
        # GPT-4: $0.03/1K input, $0.06/1K output
        cost = calculate_cost("gpt-4", 1000, 500)

        expected = (1000 * 0.03 / 1000) + (500 * 0.06 / 1000)
        assert abs(cost - expected) < 0.0001
        assert abs(cost - 0.06) < 0.0001

    def test_gpt35_turbo_cost_calculation(self):
        """Test GPT-3.5-turbo cost calculation."""
        # GPT-3.5-turbo: $0.0005/1K input, $0.0015/1K output
        cost = calculate_cost("gpt-3.5-turbo", 2000, 1000)

        expected = (2000 * 0.0005 / 1000) + (1000 * 0.0015 / 1000)
        assert abs(cost - expected) < 0.00001
        assert abs(cost - 0.0025) < 0.00001

    def test_claude_sonnet_cost_calculation(self):
        """Test Claude Sonnet cost calculation."""
        # Claude Sonnet: $0.003/1K input, $0.015/1K output
        cost = calculate_cost("claude-sonnet-4-5-20250929", 1000, 1000)

        expected = (1000 * 0.003 / 1000) + (1000 * 0.015 / 1000)
        assert abs(cost - expected) < 0.00001
        assert abs(cost - 0.018) < 0.00001

    def test_cost_breakdown(self):
        """Test cost breakdown returns separate input/output costs."""
        input_cost, output_cost, total_cost = calculate_cost_breakdown(
            "gpt-4", 1000, 500
        )

        assert abs(input_cost - 0.03) < 0.0001
        assert abs(output_cost - 0.03) < 0.0001
        assert abs(total_cost - 0.06) < 0.0001

    def test_zero_tokens(self):
        """Test cost calculation with zero tokens."""
        cost = calculate_cost("gpt-4", 0, 0)
        assert cost == 0.0

    def test_large_token_counts(self):
        """Test cost calculation with large token counts."""
        cost = calculate_cost("gpt-4", 100000, 50000)

        expected = (100000 * 0.03 / 1000) + (50000 * 0.06 / 1000)
        assert abs(cost - expected) < 0.01
        assert abs(cost - 6.0) < 0.01

    def test_invalid_model_raises_error(self):
        """Test that invalid model name raises ValueError."""
        with pytest.raises(ValueError, match="Pricing not found"):
            calculate_cost("invalid-model-name", 1000, 500)


class TestModelPricing:
    """Tests for model pricing lookup."""

    def test_exact_model_match(self):
        """Test exact model name match."""
        pricing = get_model_pricing("gpt-4")

        assert pricing is not None
        assert pricing.provider == "openai"
        assert pricing.model_name == "gpt-4"
        assert pricing.input_cost_per_1k == Decimal("0.03")

    def test_fuzzy_model_match_gpt4(self):
        """Test fuzzy matching for GPT-4 variants."""
        pricing = get_model_pricing("gpt-4-0613")

        assert pricing is not None
        assert pricing.model_name == "gpt-4"

    def test_fuzzy_model_match_claude(self):
        """Test fuzzy matching for Claude variants."""
        pricing = get_model_pricing("claude-3-sonnet-20241022")

        assert pricing is not None
        assert "sonnet" in pricing.model_name.lower()

    def test_unknown_model_returns_none(self):
        """Test that unknown model returns None."""
        pricing = get_model_pricing("completely-unknown-model")
        assert pricing is None

    def test_all_supported_models_have_pricing(self):
        """Test that all documented models have pricing data."""
        models = [
            "gpt-4",
            "gpt-4-turbo",
            "gpt-3.5-turbo",
            "claude-3-opus-20240229",
            "claude-sonnet-4-5-20250929",
            "claude-3-haiku-20240307",
        ]

        for model in models:
            pricing = get_model_pricing(model)
            assert pricing is not None, f"No pricing for {model}"


class TestTokenEstimation:
    """Tests for token estimation utilities."""

    def test_estimate_tokens_short_text(self):
        """Test token estimation for short text."""
        text = "Hello world"
        tokens = estimate_tokens(text)

        # ~4 chars per token
        assert 2 <= tokens <= 4

    def test_estimate_tokens_long_text(self):
        """Test token estimation for long text."""
        text = "This is a longer text " * 100
        tokens = estimate_tokens(text)

        # Should be roughly length / 4
        expected = len(text) // 4
        assert abs(tokens - expected) < 100

    def test_estimate_cost(self):
        """Test cost estimation from text."""
        text = "Analyze this transcript" * 100
        cost = estimate_cost("gpt-4", text, estimated_output_tokens=500)

        assert cost > 0
        # Should be reasonable for ~500 input tokens + 500 output
        assert 0.02 < cost < 0.1


class TestCostUtilities:
    """Tests for cost utility functions."""

    def test_check_cost_threshold_under(self):
        """Test threshold check when under limit."""
        result = check_cost_threshold(50.0, 100.0, "daily")
        assert result is False

    def test_check_cost_threshold_over(self):
        """Test threshold check when over limit."""
        result = check_cost_threshold(150.0, 100.0, "daily")
        assert result is True

    def test_check_cost_threshold_exact(self):
        """Test threshold check at exact limit."""
        result = check_cost_threshold(100.0, 100.0, "daily")
        assert result is True

    def test_format_cost(self):
        """Test cost formatting."""
        formatted = format_cost(0.06789)
        assert formatted == "$0.0679"

        formatted = format_cost(123.456789)
        assert formatted == "$123.4568"


class TestEdgeCases:
    """Tests for edge cases and error conditions."""

    def test_negative_tokens_not_allowed(self):
        """Test that negative tokens are handled."""
        # Implementation should handle this gracefully
        # Either raise error or treat as 0
        try:
            cost = calculate_cost("gpt-4", -100, 500)
            # If no error, should be treating negatives as valid or as 0
            assert cost >= 0
        except ValueError:
            # Also acceptable to raise error
            pass

    def test_very_small_costs(self):
        """Test calculation with very small token counts."""
        cost = calculate_cost("gpt-3.5-turbo", 1, 1)

        assert cost > 0
        assert cost < 0.001

    def test_mixed_case_model_names(self):
        """Test that model name matching is case-insensitive."""
        cost1 = calculate_cost("GPT-4", 1000, 500)
        cost2 = calculate_cost("gpt-4", 1000, 500)

        # Should produce same result
        assert abs(cost1 - cost2) < 0.0001


class TestPricingAccuracy:
    """Tests to ensure pricing matches published rates."""

    def test_gpt4_pricing_accuracy(self):
        """Verify GPT-4 pricing is correct."""
        # As of January 2025: $0.03/1K input, $0.06/1K output
        pricing = get_model_pricing("gpt-4")

        assert pricing.input_cost_per_1k == Decimal("0.03")
        assert pricing.output_cost_per_1k == Decimal("0.06")

    def test_claude_sonnet_pricing_accuracy(self):
        """Verify Claude Sonnet pricing is correct."""
        # As of January 2025: $0.003/1K input, $0.015/1K output
        pricing = get_model_pricing("claude-sonnet-4-5-20250929")

        assert pricing.input_cost_per_1k == Decimal("0.003")
        assert pricing.output_cost_per_1k == Decimal("0.015")

    def test_realistic_conversation_cost(self):
        """Test cost calculation for realistic conversation."""
        # Typical conversation: 10K input tokens, 2K output tokens
        cost = calculate_cost("gpt-4", 10000, 2000)

        # Expected: (10K * $0.03/1K) + (2K * $0.06/1K) = $0.30 + $0.12 = $0.42
        assert abs(cost - 0.42) < 0.01


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
