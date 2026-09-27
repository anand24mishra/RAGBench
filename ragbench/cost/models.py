from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class TokenUsage(BaseModel):
    model_config = ConfigDict(frozen=True)

    input_tokens: int | None = Field(default=None, ge=0)
    output_tokens: int | None = Field(default=None, ge=0)
    total_tokens: int | None = Field(default=None, ge=0)

    @model_validator(mode="before")
    @classmethod
    def compute_total(cls, data: Any) -> Any:
        if isinstance(data, dict):
            in_t = data.get("input_tokens")
            out_t = data.get("output_tokens")
            tot = data.get("total_tokens")
            if tot is None and (in_t is not None or out_t is not None):
                d = dict(data)
                d["total_tokens"] = (in_t or 0) + (out_t or 0)
                return d
        return data


class ModelPricing(BaseModel):
    model_config = ConfigDict(frozen=True)

    model: str = Field(min_length=1)
    input_cost_per_1m_tokens: float = Field(ge=0.0)
    output_cost_per_1m_tokens: float = Field(ge=0.0)
    currency: str = Field(default="USD", min_length=1)
    effective_date: str = Field(min_length=1)


class QueryCost(BaseModel):
    model_config = ConfigDict(frozen=True)

    cost_status: Literal["available", "unavailable"]
    currency: str = "USD"
    input_cost: float | None = None
    output_cost: float | None = None
    total_cost: float | None = None
    model: str | None = None


class CostAccountingResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    cost_status: Literal["available", "unavailable"]
    currency: str = "USD"
    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None
    input_cost: float | None = None
    output_cost: float | None = None
    total_cost: float | None = None
    cost_per_query: float | None = None
