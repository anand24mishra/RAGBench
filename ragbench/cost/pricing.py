from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from ragbench.cost.models import (
    CostAccountingResult,
    ModelPricing,
    QueryCost,
    TokenUsage,
)

DEFAULT_PRICING_PATH = Path("data/pricing.yaml")


class PricingRegistry:
    def __init__(self, pricings: dict[str, ModelPricing] | None = None) -> None:
        self._pricings: dict[str, ModelPricing] = dict(pricings or {})

    def register_pricing(self, pricing: ModelPricing) -> None:
        self._pricings[pricing.model.lower().strip()] = pricing

    def get_pricing(self, model: str | None) -> ModelPricing | None:
        if not model:
            return None
        cleaned = model.lower().strip()
        # Direct match
        if cleaned in self._pricings:
            return self._pricings[cleaned]
        # Prefix match (e.g. gpt-4o-mini-2024-07-18 -> gpt-4o-mini)
        for key, pricing in self._pricings.items():
            if cleaned.startswith(key):
                return pricing
        return None

    def calculate_cost(
        self,
        model: str | None,
        input_tokens: int | None,
        output_tokens: int | None,
    ) -> QueryCost:
        if (
            not model
            or input_tokens is None
            or output_tokens is None
            or input_tokens < 0
            or output_tokens < 0
        ):
            return QueryCost(cost_status="unavailable", model=model)

        pricing = self.get_pricing(model)
        if pricing is None:
            return QueryCost(cost_status="unavailable", model=model)

        input_cost = (input_tokens / 1_000_000.0) * pricing.input_cost_per_1m_tokens
        output_cost = (output_tokens / 1_000_000.0) * pricing.output_cost_per_1m_tokens
        total_cost = input_cost + output_cost

        return QueryCost(
            cost_status="available",
            currency=pricing.currency,
            input_cost=round(input_cost, 6),
            output_cost=round(output_cost, 6),
            total_cost=round(total_cost, 6),
            model=model,
        )

    def aggregate_costs(
        self,
        query_costs: list[QueryCost],
        token_usages: list[TokenUsage],
    ) -> CostAccountingResult:
        if not query_costs:
            return CostAccountingResult(cost_status="unavailable")

        total_input_tokens = 0
        total_output_tokens = 0
        has_token_data = True

        for u in token_usages:
            if u.input_tokens is None or u.output_tokens is None:
                has_token_data = False
                break
            total_input_tokens += u.input_tokens
            total_output_tokens += u.output_tokens

        # Check if all query costs are available
        all_available = all(c.cost_status == "available" for c in query_costs)
        if not all_available or not has_token_data:
            return CostAccountingResult(
                cost_status="unavailable",
                input_tokens=total_input_tokens if has_token_data else None,
                output_tokens=total_output_tokens if has_token_data else None,
                total_tokens=(total_input_tokens + total_output_tokens) if has_token_data else None,
            )

        currencies = {c.currency for c in query_costs}
        currency = currencies.pop() if len(currencies) == 1 else "USD"

        sum_input_cost = sum(c.input_cost or 0.0 for c in query_costs)
        sum_output_cost = sum(c.output_cost or 0.0 for c in query_costs)
        sum_total_cost = sum(c.total_cost or 0.0 for c in query_costs)
        cost_per_query = sum_total_cost / len(query_costs) if query_costs else 0.0

        return CostAccountingResult(
            cost_status="available",
            currency=currency,
            input_tokens=total_input_tokens,
            output_tokens=total_output_tokens,
            total_tokens=total_input_tokens + total_output_tokens,
            input_cost=round(sum_input_cost, 6),
            output_cost=round(sum_output_cost, 6),
            total_cost=round(sum_total_cost, 6),
            cost_per_query=round(cost_per_query, 6),
        )

    @classmethod
    def from_yaml(cls, path: Path | str) -> PricingRegistry:
        p = Path(path)
        if not p.is_file():
            return cls()
        data = yaml.safe_load(p.read_text(encoding="utf-8"))
        return cls.from_dict(data or {})

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PricingRegistry:
        registry = cls()
        models = data.get("models", [])
        if isinstance(models, list):
            for item in models:
                if isinstance(item, dict):
                    pricing = ModelPricing.model_validate(item)
                    registry.register_pricing(pricing)
        elif isinstance(models, dict):
            for model_name, item in models.items():
                if isinstance(item, dict):
                    item_data = dict(item)
                    item_data.setdefault("model", model_name)
                    pricing = ModelPricing.model_validate(item_data)
                    registry.register_pricing(pricing)
        return registry


_DEFAULT_REGISTRY: PricingRegistry | None = None


def get_pricing_registry(path: Path | str = DEFAULT_PRICING_PATH) -> PricingRegistry:
    global _DEFAULT_REGISTRY
    if _DEFAULT_REGISTRY is None:
        p = Path(path)
        if p.is_file():
            _DEFAULT_REGISTRY = PricingRegistry.from_yaml(p)
        else:
            _DEFAULT_REGISTRY = PricingRegistry()
    return _DEFAULT_REGISTRY
