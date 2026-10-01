"""Tests for src/calculations.py -- values must match docs/calculations.md."""

import pytest

from src.calculations import (
    debt_to_income,
    emergency_fund_months,
    future_value_savings,
    goal_funding_gap,
    goal_funding_progress,
    major_purchase_projection,
    monthly_cash_flow,
    net_worth,
    retirement_income,
    run_major_purchase_scenarios,
    run_retirement_scenarios,
    savings_rate,
)


def test_net_worth():
    assert net_worth(500_000, 200_000) == 300_000


def test_net_worth_rejects_negative():
    with pytest.raises(ValueError):
        net_worth(-1, 0)


def test_monthly_cash_flow():
    assert monthly_cash_flow(9_000, 7_000) == 2_000


def test_monthly_cash_flow_can_be_negative_deficit():
    assert monthly_cash_flow(3_000, 4_000) == -1_000


def test_savings_rate():
    assert savings_rate(2_000, 9_000) == pytest.approx(0.2222222222, rel=1e-6)


def test_savings_rate_zero_income_is_none():
    assert savings_rate(0, 0) is None


def test_savings_rate_rejects_negative_income():
    with pytest.raises(ValueError):
        savings_rate(100, -1)


def test_debt_to_income():
    assert debt_to_income(1_800, 9_000) == pytest.approx(0.2)


def test_debt_to_income_zero_income_is_none():
    assert debt_to_income(100, 0) is None


def test_emergency_fund_months():
    assert emergency_fund_months(24_000, 7_000) == pytest.approx(3.4285714286, rel=1e-6)


def test_emergency_fund_months_zero_expenses_is_none():
    assert emergency_fund_months(10_000, 0) is None


def test_goal_funding_progress():
    assert goal_funding_progress(40_000, 100_000) == pytest.approx(0.4)


def test_goal_funding_progress_zero_target_is_none():
    assert goal_funding_progress(100, 0) is None


def test_goal_funding_gap():
    assert goal_funding_gap(100_000, 40_000) == 60_000


def test_goal_funding_gap_floored_at_zero():
    assert goal_funding_gap(50_000, 90_000) == 0


def test_future_value_savings_matches_documented_example():
    result = future_value_savings(
        current_savings=50_000, monthly_contribution=1_000, years=20, annual_return=0.06
    )
    assert result == pytest.approx(627_551.12, rel=1e-6)


def test_future_value_savings_zero_return_is_simple_addition():
    result = future_value_savings(
        current_savings=50_000, monthly_contribution=1_000, years=20, annual_return=0.0
    )
    assert result == pytest.approx(50_000 + 1_000 * 240)


def test_future_value_savings_rejects_non_positive_years():
    with pytest.raises(ValueError):
        future_value_savings(1_000, 100, 0, 0.05)


def test_future_value_savings_rejects_negative_amounts():
    with pytest.raises(ValueError):
        future_value_savings(-1, 100, 10, 0.05)


def test_retirement_income_matches_documented_example():
    result = retirement_income(1_000_000, 0.04)
    assert result["annual_income"] == pytest.approx(40_000)
    assert result["monthly_income"] == pytest.approx(3_333.333333, rel=1e-6)
    assert result["withdrawal_rate"] == 0.04


def test_retirement_income_rejects_negative_withdrawal_rate():
    with pytest.raises(ValueError):
        retirement_income(1_000, -0.01)


def test_major_purchase_projection_matches_documented_example():
    result = major_purchase_projection(
        target_cost=60_000,
        current_savings=10_000,
        years_to_purchase=5,
        monthly_contribution=500,
        annual_return=0.05,
    )
    assert result["projected_savings"] == pytest.approx(46_836.63, rel=1e-5)
    assert result["funding_gap"] == pytest.approx(13_163.37, rel=1e-5)
    assert result["fully_funded"] is False


def test_major_purchase_projection_fully_funded_flag():
    result = major_purchase_projection(
        target_cost=1_000,
        current_savings=10_000,
        years_to_purchase=1,
        monthly_contribution=0,
        annual_return=0.0,
    )
    assert result["fully_funded"] is True
    assert result["funding_gap"] == 0


def test_run_retirement_scenarios_has_three_named_scenarios():
    results = run_retirement_scenarios(50_000, 1_000, 20)
    assert set(results.keys()) == {"baseline", "optimistic", "conservative"}
    assert results["baseline"]["projected_balance"] == pytest.approx(627_551.12, rel=1e-6)
    # Optimistic should project a higher balance than conservative.
    assert results["optimistic"]["projected_balance"] > results["conservative"]["projected_balance"]


def test_run_major_purchase_scenarios_has_three_named_scenarios():
    results = run_major_purchase_scenarios(60_000, 10_000, 5, 500)
    assert set(results.keys()) == {"baseline", "optimistic", "conservative"}
    assert results["optimistic"]["projected_savings"] > results["conservative"]["projected_savings"]
