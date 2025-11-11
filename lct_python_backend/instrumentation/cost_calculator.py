"""
Cost calculation utilities for LLM API calls.

Supports pricing for:
- OpenAI models (GPT-4, GPT-3.5-turbo, GPT-4-turbo)
- Anthropic models (Claude Sonnet-4, Claude Opus, Claude Haiku)

Pricing data as of January 2025.
"""

from typing import Dict, Optional, Tuple
from decimal import Decimal
from dataclasses import dataclass


@dataclass
class ModelPricing:
    """Pricing information for a specific model."""
    input_cost_per_1k: Decimal  # Cost per 1000 input tokens
    output_cost_per_1k: Decimal  # Cost per 1000 output tokens
    provider: str
    model_name: str


# Pricing data (USD per 1K tokens)
# Updated as of January 2025
MODEL_PRICING: Dict[str, ModelPricing] = {
    # OpenAI Models
    "gpt-4": ModelPricing(
        input_cost_per_1k=Decimal("0.03"),
        output_cost_per_1k=Decimal("0.06"),
        provider="openai",
        model_name="gpt-4"
    ),
    "gpt-4-turbo": ModelPricing(
        input_cost_per_1k=Decimal("0.01"),
        output_cost_per_1k=Decimal("0.03"),
        provider="openai",
        model_name="gpt-4-turbo"
    ),
    "gpt-4-turbo-preview": ModelPricing(
        input_cost_per_1k=Decimal("0.01"),
        output_cost_per_1k=Decimal("0.03"),
        provider="openai",
        model_name="gpt-4-turbo-preview"
    ),
    "gpt-3.5-turbo": ModelPricing(
        input_cost_per_1k=Decimal("0.0005"),
        output_cost_per_1k=Decimal("0.0015"),
        provider="openai",
        model_name="gpt-3.5-turbo"
    ),
    "gpt-3.5-turbo-16k": ModelPricing(
        input_cost_per_1k=Decimal("0.001"),
        output_cost_per_1k=Decimal("0.002"),
        provider="openai",
        model_name="gpt-3.5-turbo-16k"
    ),

    # Anthropic Models
    "claude-3-opus-20240229": ModelPricing(
        input_cost_per_1k=Decimal("0.015"),
        output_cost_per_1k=Decimal("0.075"),
        provider="anthropic",
        model_name="claude-3-opus"
    ),
    "claude-3-sonnet-20240229": ModelPricing(
        input_cost_per_1k=Decimal("0.003"),
        output_cost_per_1k=Decimal("0.015"),
        provider="anthropic",
        model_name="claude-3-sonnet"
    ),
    "claude-sonnet-4-5-20250929": ModelPricing(
        input_cost_per_1k=Decimal("0.003"),
        output_cost_per_1k=Decimal("0.015"),
        provider="anthropic",
        model_name="claude-sonnet-4.5"
    ),
    "claude-3-haiku-20240307": ModelPricing(
        input_cost_per_1k=Decimal("0.00025"),
        output_cost_per_1k=Decimal("0.00125"),
        provider="anthropic",
        model_name="claude-3-haiku"
    ),
}


def get_model_pricing(model: str) -> Optional[ModelPricing]:
    """
    Get pricing information for a specific model.

    Args:
        model: Model identifier (e.g., "gpt-4", "claude-3-sonnet-20240229")

    Returns:
        ModelPricing object or None if model not found
    """
    # Try exact match first
    if model in MODEL_PRICING:
        return MODEL_PRICING[model]

    # Try fuzzy match (handle versioned model names)
    model_lower = model.lower()

    # GPT-4 variants
    if "gpt-4-turbo" in model_lower:
        return MODEL_PRICING["gpt-4-turbo"]
    elif "gpt-4" in model_lower:
        return MODEL_PRICING["gpt-4"]
    elif "gpt-3.5-turbo-16k" in model_lower:
        return MODEL_PRICING["gpt-3.5-turbo-16k"]
    elif "gpt-3.5" in model_lower:
        return MODEL_PRICING["gpt-3.5-turbo"]

    # Claude variants
    if "opus" in model_lower:
        return MODEL_PRICING["claude-3-opus-20240229"]
    elif "sonnet" in model_lower:
        return MODEL_PRICING["claude-sonnet-4-5-20250929"]
    elif "haiku" in model_lower:
        return MODEL_PRICING["claude-3-haiku-20240307"]

    return None


def calculate_cost(
    model: str,
    input_tokens: int,
    output_tokens: int,
) -> float:
    """
    Calculate the cost of an LLM API call.

    Args:
        model: Model identifier (e.g., "gpt-4", "claude-3-sonnet-20240229")
        input_tokens: Number of input (prompt) tokens
        output_tokens: Number of output (completion) tokens

    Returns:
        Cost in USD (float)

    Raises:
        ValueError: If model pricing is not found

    Example:
        >>> calculate_cost("gpt-4", 1000, 500)
        0.06  # (1000 * $0.03/1K) + (500 * $0.06/1K)
    """
    pricing = get_model_pricing(model)

    if pricing is None:
        raise ValueError(
            f"Pricing not found for model '{model}'. "
            f"Supported models: {', '.join(MODEL_PRICING.keys())}"
        )

    # Calculate costs using Decimal for precision
    input_cost = (Decimal(input_tokens) / Decimal(1000)) * pricing.input_cost_per_1k
    output_cost = (Decimal(output_tokens) / Decimal(1000)) * pricing.output_cost_per_1k

    total_cost = input_cost + output_cost

    # Convert to float for compatibility with database
    return float(total_cost)


def calculate_cost_breakdown(
    model: str,
    input_tokens: int,
    output_tokens: int,
) -> Tuple[float, float, float]:
    """
    Calculate cost with breakdown of input and output costs.

    Args:
        model: Model identifier
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens

    Returns:
        Tuple of (input_cost, output_cost, total_cost) in USD

    Example:
        >>> calculate_cost_breakdown("gpt-4", 1000, 500)
        (0.03, 0.03, 0.06)
    """
    pricing = get_model_pricing(model)

    if pricing is None:
        raise ValueError(
            f"Pricing not found for model '{model}'. "
            f"Supported models: {', '.join(MODEL_PRICING.keys())}"
        )

    input_cost = (Decimal(input_tokens) / Decimal(1000)) * pricing.input_cost_per_1k
    output_cost = (Decimal(output_tokens) / Decimal(1000)) * pricing.output_cost_per_1k
    total_cost = input_cost + output_cost

    return (float(input_cost), float(output_cost), float(total_cost))


def estimate_tokens(text: str) -> int:
    """
    Rough estimation of token count for a given text.

    Uses rule of thumb: ~4 characters per token (for English text).
    For accurate counting, use tiktoken library.

    Args:
        text: Input text

    Returns:
        Estimated token count

    Note:
        This is a rough approximation. For production use, consider
        using tiktoken for OpenAI models or Anthropic's tokenizer.
    """
    # Rough approximation: 1 token ≈ 4 characters
    return len(text) // 4


def estimate_cost(
    model: str,
    input_text: str,
    estimated_output_tokens: int = 500,
) -> float:
    """
    Estimate cost for a given input text and expected output length.

    Args:
        model: Model identifier
        input_text: Input text to be sent to model
        estimated_output_tokens: Expected output length (default 500)

    Returns:
        Estimated cost in USD

    Example:
        >>> estimate_cost("gpt-4", "Analyze this transcript...", 1000)
        0.08
    """
    input_tokens = estimate_tokens(input_text)
    return calculate_cost(model, input_tokens, estimated_output_tokens)


# Cost tracking utilities

def get_average_cost_per_conversation(
    total_cost: float,
    num_conversations: int
) -> float:
    """Calculate average cost per conversation."""
    if num_conversations == 0:
        return 0.0
    return total_cost / num_conversations


def calculate_monthly_projection(
    daily_cost: float,
    days_in_month: int = 30
) -> float:
    """Project monthly costs based on daily average."""
    return daily_cost * days_in_month


def check_cost_threshold(
    current_cost: float,
    threshold: float,
    threshold_type: str = "daily"
) -> bool:
    """
    Check if cost has exceeded threshold.

    Args:
        current_cost: Current cost in USD
        threshold: Threshold value in USD
        threshold_type: Type of threshold ("daily", "weekly", "monthly")

    Returns:
        True if threshold exceeded, False otherwise
    """
    return current_cost >= threshold


def format_cost(cost: float) -> str:
    """Format cost as currency string."""
    return f"${cost:.4f}"
