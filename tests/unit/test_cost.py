from __future__ import annotations

import pytest
from pydantic import ValidationError

from ragbench.cost.models import ModelPricing, TokenUsage
from ragbench.cost.pricing import PricingRegistry


def test_token_usage_total_calculation() -> None:
    usage = TokenUsage(input_tokens=150, output_tokens=50)
    assert usage.total_tokens == 200

    usage_explicit = TokenUsage(input_tokens=100, output_tokens=50, total_tokens=150)
    assert usage_explicit.total_tokens == 150

    usage_empty = TokenUsage()
    assert usage_empty.total_tokens is None


def test_pricing_lookup_exact_and_prefix() -> None:
    registry = PricingRegistry()
    registry.register_pricing(
        ModelPricing(
            model="gpt-4o-mini",
            input_cost_per_1m_tokens=0.15,
            output_cost_per_1m_tokens=0.60,
            currency="USD",
            effective_date="2024-07-18",
        )
    )

    exact = registry.get_pricing("gpt-4o-mini")
    assert exact is not None
    assert exact.input_cost_per_1m_tokens == 0.15

    prefix = registry.get_pricing("gpt-4o-mini-2024-07-18")
    assert prefix is not None
    assert prefix.model == "gpt-4o-mini"

    case_insensitive = registry.get_pricing("GPT-4O-MINI")
    assert case_insensitive is not None


def test_missing_pricing_returns_unavailable() -> None:
    registry = PricingRegistry()
    cost = registry.calculate_cost("unknown-model", 1000, 200)
    assert cost.cost_status == "unavailable"
    assert cost.input_cost is None
    assert cost.total_cost is None


def test_zero_usage_calculation() -> None:
    registry = PricingRegistry()
    registry.register_pricing(
        ModelPricing(
            model="gpt-4o-mini",
            input_cost_per_1m_tokens=0.15,
            output_cost_per_1m_tokens=0.60,
            currency="USD",
            effective_date="2024-07-18",
        )
    )
    cost = registry.calculate_cost("gpt-4o-mini", 0, 0)
    assert cost.cost_status == "available"
    assert cost.input_cost == 0.0
    assert cost.output_cost == 0.0
    assert cost.total_cost == 0.0


def test_invalid_pricing_rejected() -> None:
    with pytest.raises(ValidationError):
        ModelPricing(
            model="invalid-model",
            input_cost_per_1m_tokens=-1.0,
            output_cost_per_1m_tokens=0.5,
            currency="USD",
            effective_date="2024-01-01",
        )


def test_aggregate_costs() -> None:
    registry = PricingRegistry()
    registry.register_pricing(
        ModelPricing(
            model="test-model",
            input_cost_per_1m_tokens=1.0,
            output_cost_per_1m_tokens=2.0,
            currency="USD",
            effective_date="2024-01-01",
        )
    )

    c1 = registry.calculate_cost("test-model", 1_000_000, 500_000)
    c2 = registry.calculate_cost("test-model", 500_000, 250_000)
    u1 = TokenUsage(input_tokens=1_000_000, output_tokens=500_000)
    u2 = TokenUsage(input_tokens=500_000, output_tokens=250_000)

    agg = registry.aggregate_costs([c1, c2], [u1, u2])
    assert agg.cost_status == "available"
    assert agg.input_tokens == 1_500_000
    assert agg.output_tokens == 750_000
    assert agg.total_tokens == 2_250_000
    assert agg.input_cost == 1.5
    assert agg.output_cost == 1.5
    assert agg.total_cost == 3.0
    assert agg.cost_per_query == 1.5
