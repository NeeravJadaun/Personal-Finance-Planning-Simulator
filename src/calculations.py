"""Deterministic financial calculations used throughout the simulator.

Every formula here is documented with a worked example in
`docs/calculations.md`. Nothing in this module calls an external service,
fetches market data, or makes a securities recommendation -- all figures are
derived from numbers the user enters for a synthetic household.

These functions raise ValueError on invalid input (negative amounts where a
negative value is not meaningful, non-positive durations, etc.) so that bad
data is caught immediately rather than silently producing a misleading
number. Ratios that are mathematically undefined when a denominator is zero
(e.g. savings rate with zero income) return None instead of raising, and
callers should render that as "N/A".
"""

from __future__ import annotations

from dataclasses import dataclass


def _require_non_negative(value: float, name: str) -> None:
    if value < 0:
        raise ValueError(f"{name} must be non-negative, got {value}")


def net_worth(total_assets: float, total_liabilities: float) -> float:
    """Net worth = total assets - total liabilities."""
    _require_non_negative(total_assets, "total_assets")
    _require_non_negative(total_liabilities, "total_liabilities")
    return total_assets - total_liabilities


def monthly_cash_flow(monthly_income: float, monthly_expenses: float) -> float:
    """Monthly surplus (or deficit) = monthly income - monthly expenses."""
    _require_non_negative(monthly_income, "monthly_income")
    _require_non_negative(monthly_expenses, "monthly_expenses")
    return monthly_income - monthly_expenses


def savings_rate(monthly_surplus: float, monthly_income: float) -> float | None:
    """Savings rate = monthly surplus / monthly income, as a fraction.

    Returns None when income is zero (undefined rather than divide-by-zero).
    monthly_surplus may be negative (a household spending more than it earns).
    """
    _require_non_negative(monthly_income, "monthly_income")
    if monthly_income == 0:
        return None
    return monthly_surplus / monthly_income


def debt_to_income(monthly_debt_payments: float, monthly_income: float) -> float | None:
    """Debt-to-income ratio = monthly debt payments / monthly gross income."""
    _require_non_negative(monthly_debt_payments, "monthly_debt_payments")
    _require_non_negative(monthly_income, "monthly_income")
    if monthly_income == 0:
        return None
    return monthly_debt_payments / monthly_income


def emergency_fund_months(liquid_assets: float, monthly_expenses: float) -> float | None:
    """Months of expenses covered by liquid (cash-like) assets."""
    _require_non_negative(liquid_assets, "liquid_assets")
    _require_non_negative(monthly_expenses, "monthly_expenses")
    if monthly_expenses == 0:
        return None
    return liquid_assets / monthly_expenses


def goal_funding_progress(current_savings: float, target_amount: float) -> float | None:
    """Fraction of a goal's target amount already saved (can exceed 1.0)."""
    _require_non_negative(current_savings, "current_savings")
    _require_non_negative(target_amount, "target_amount")
    if target_amount == 0:
        return None
    return current_savings / target_amount


def goal_funding_gap(target_amount: float, current_savings: float) -> float:
    """Remaining dollar amount needed to reach a goal (floored at 0)."""
    _require_non_negative(target_amount, "target_amount")
    _require_non_negative(current_savings, "current_savings")
    return max(target_amount - current_savings, 0.0)


def future_value_savings(
    current_savings: float,
    monthly_contribution: float,
    years: float,
    annual_return: float,
) -> float:
    """Projected balance after contributing monthly for `years` years.

    Uses the standard future-value-of-an-annuity formula with monthly
    compounding:

        FV = PV * (1 + r)^n + PMT * (((1 + r)^n - 1) / r)

    where r is the monthly rate (annual_return / 12) and n is the number of
    months (years * 12). When r == 0 this degenerates to simple addition.

    This is a deterministic projection, not a guarantee -- actual markets do
    not return a constant rate every month.
    """
    _require_non_negative(current_savings, "current_savings")
    _require_non_negative(monthly_contribution, "monthly_contribution")
    if years <= 0:
        raise ValueError(f"years must be positive, got {years}")
    if annual_return < -1:
        raise ValueError(f"annual_return cannot be less than -100%, got {annual_return}")

    months = years * 12
    monthly_rate = annual_return / 12

    if monthly_rate == 0:
        return current_savings + monthly_contribution * months

    growth_factor = (1 + monthly_rate) ** months
    return current_savings * growth_factor + monthly_contribution * (
        (growth_factor - 1) / monthly_rate
    )


def retirement_income(balance: float, withdrawal_rate: float) -> dict[str, float]:
    """Estimated sustainable income from a retirement balance.

    withdrawal_rate is an explicit, user-visible assumption (e.g. 0.04 for
    the traditional "4% rule"). This is an educational heuristic, not a
    personalized recommendation -- actual safe withdrawal rates depend on
    sequence of returns, longevity, and spending flexibility.
    """
    _require_non_negative(balance, "balance")
    if withdrawal_rate < 0:
        raise ValueError(f"withdrawal_rate must be non-negative, got {withdrawal_rate}")
    annual_income = balance * withdrawal_rate
    return {
        "annual_income": annual_income,
        "monthly_income": annual_income / 12,
        "withdrawal_rate": withdrawal_rate,
    }


def major_purchase_projection(
    target_cost: float,
    current_savings: float,
    years_to_purchase: float,
    monthly_contribution: float,
    annual_return: float,
) -> dict[str, float]:
    """Projected savings and funding gap for a major purchase goal."""
    _require_non_negative(target_cost, "target_cost")
    projected_savings = future_value_savings(
        current_savings, monthly_contribution, years_to_purchase, annual_return
    )
    gap = goal_funding_gap(target_cost, projected_savings)
    return {
        "projected_savings": projected_savings,
        "target_cost": target_cost,
        "funding_gap": gap,
        "fully_funded": gap <= 0,
    }


@dataclass(frozen=True)
class ScenarioAssumption:
    """A named set of return/withdrawal assumptions for scenario comparison."""

    scenario: str
    annual_return: float
    withdrawal_rate: float | None = None


#: Default baseline/optimistic/conservative assumptions used by the
#: scenario planner when a household has not customized its own. These are
#: illustrative, labelled assumptions -- not predictions.
DEFAULT_SCENARIOS: dict[str, ScenarioAssumption] = {
    "baseline": ScenarioAssumption("baseline", annual_return=0.06, withdrawal_rate=0.04),
    "optimistic": ScenarioAssumption("optimistic", annual_return=0.08, withdrawal_rate=0.045),
    "conservative": ScenarioAssumption("conservative", annual_return=0.04, withdrawal_rate=0.035),
}


def run_retirement_scenarios(
    current_savings: float,
    monthly_contribution: float,
    years_to_retirement: float,
    assumptions: dict[str, ScenarioAssumption] | None = None,
) -> dict[str, dict]:
    """Compute baseline/optimistic/conservative retirement projections."""
    assumptions = assumptions or DEFAULT_SCENARIOS
    results = {}
    for name, assumption in assumptions.items():
        balance = future_value_savings(
            current_savings, monthly_contribution, years_to_retirement, assumption.annual_return
        )
        income = retirement_income(balance, assumption.withdrawal_rate or 0.04)
        results[name] = {
            "annual_return": assumption.annual_return,
            "withdrawal_rate": assumption.withdrawal_rate,
            "projected_balance": balance,
            **income,
        }
    return results


def run_major_purchase_scenarios(
    target_cost: float,
    current_savings: float,
    years_to_purchase: float,
    monthly_contribution: float,
    assumptions: dict[str, ScenarioAssumption] | None = None,
) -> dict[str, dict]:
    """Compute baseline/optimistic/conservative major-purchase projections."""
    assumptions = assumptions or DEFAULT_SCENARIOS
    results = {}
    for name, assumption in assumptions.items():
        results[name] = {
            "annual_return": assumption.annual_return,
            **major_purchase_projection(
                target_cost,
                current_savings,
                years_to_purchase,
                monthly_contribution,
                assumption.annual_return,
            ),
        }
    return results
