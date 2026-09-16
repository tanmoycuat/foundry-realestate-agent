"""Deterministic financial calculations and score aggregation."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Mapping


SCORE_WEIGHTS = {
    "comps": 0.25,
    "rental": 0.20,
    "neighborhood": 0.20,
    "investment": 0.20,
    "market": 0.15,
}


@dataclass(frozen=True)
class RentalMetrics:
    gross_annual_rent: float
    net_operating_income: float
    annual_debt_service: float
    annual_cash_flow: float
    monthly_cash_flow: float
    cap_rate: float
    cash_on_cash_return: float
    gross_rent_multiplier: float
    debt_service_coverage_ratio: float


def _require_nonnegative(name: str, value: float) -> None:
    if not isfinite(value) or value < 0:
        raise ValueError(f"{name} must be a finite non-negative number")


def mortgage_payment(principal: float, annual_rate_percent: float, years: int) -> float:
    """Return the monthly principal-and-interest payment."""
    _require_nonnegative("principal", principal)
    _require_nonnegative("annual_rate_percent", annual_rate_percent)
    if years <= 0:
        raise ValueError("years must be greater than zero")
    if principal == 0:
        return 0.0

    payments = years * 12
    monthly_rate = annual_rate_percent / 100 / 12
    if monthly_rate == 0:
        return principal / payments

    growth = (1 + monthly_rate) ** payments
    return principal * monthly_rate * growth / (growth - 1)


def rental_metrics(
    *,
    purchase_price: float,
    monthly_rent: float,
    monthly_operating_expenses: float,
    monthly_debt_service: float,
    cash_invested: float,
) -> RentalMetrics:
    """Calculate standard rental metrics from explicit monthly inputs."""
    for name, value in {
        "purchase_price": purchase_price,
        "monthly_rent": monthly_rent,
        "monthly_operating_expenses": monthly_operating_expenses,
        "monthly_debt_service": monthly_debt_service,
        "cash_invested": cash_invested,
    }.items():
        _require_nonnegative(name, value)

    if purchase_price == 0:
        raise ValueError("purchase_price must be greater than zero")

    gross_annual_rent = monthly_rent * 12
    net_operating_income = (monthly_rent - monthly_operating_expenses) * 12
    annual_debt_service = monthly_debt_service * 12
    annual_cash_flow = net_operating_income - annual_debt_service

    return RentalMetrics(
        gross_annual_rent=gross_annual_rent,
        net_operating_income=net_operating_income,
        annual_debt_service=annual_debt_service,
        annual_cash_flow=annual_cash_flow,
        monthly_cash_flow=annual_cash_flow / 12,
        cap_rate=net_operating_income / purchase_price * 100,
        cash_on_cash_return=(annual_cash_flow / cash_invested * 100) if cash_invested else 0,
        gross_rent_multiplier=(purchase_price / gross_annual_rent) if gross_annual_rent else 0,
        debt_service_coverage_ratio=(net_operating_income / annual_debt_service)
        if annual_debt_service
        else 0,
    )


def calculate_property_score(scores: Mapping[str, float]) -> float:
    """Calculate the weighted score, renormalizing when a specialist is missing."""
    available = {name: score for name, score in scores.items() if name in SCORE_WEIGHTS}
    if not available:
        raise ValueError("at least one recognized specialist score is required")
    for name, score in available.items():
        if not isfinite(score) or not 0 <= score <= 100:
            raise ValueError(f"{name} score must be between 0 and 100")

    available_weight = sum(SCORE_WEIGHTS[name] for name in available)
    weighted_sum = sum(scores[name] * SCORE_WEIGHTS[name] for name in available)
    return round(weighted_sum / available_weight, 1)


def score_grade(score: float) -> str:
    """Map a property score to the repository's grade scale."""
    if not 0 <= score <= 100:
        raise ValueError("score must be between 0 and 100")
    if score >= 85:
        return "A+"
    if score >= 70:
        return "A"
    if score >= 55:
        return "B"
    if score >= 40:
        return "C"
    if score >= 25:
        return "D"
    return "F"


def property_signal(score: float) -> str:
    """Map a property score to the repository's investment signal."""
    grade = score_grade(score)
    return {
        "A+": "STRONG BUY",
        "A": "BUY",
        "B": "HOLD / WATCH",
        "C": "CAUTION",
        "D": "PASS",
        "F": "AVOID",
    }[grade]
