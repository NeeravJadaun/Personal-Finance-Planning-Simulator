# Calculation Reference

All formulas below are implemented in [`src/calculations.py`](../src/calculations.py)
and exercised by [`tests/test_calculations.py`](../tests/test_calculations.py).
Every number in this document comes from **synthetic example data** -- none
of it describes a real person or account.

These are transparent, deterministic formulas for educational purposes. They
are not personalized financial advice, and they do not guarantee any future
result. Actual markets, tax rules, and personal circumstances vary.

---

## 1. Net worth

```
net_worth = total_assets - total_liabilities
```

**Example:** assets = $500,000, liabilities = $200,000 → net worth = **$300,000**

## 2. Monthly cash flow

```
monthly_total_outflow = monthly_living_expenses + monthly_debt_payments
monthly_cash_flow      = monthly_income - monthly_total_outflow
```

Debt service (mortgage, auto loan, student loan, credit card payments) is
counted as a cash outflow here, in addition to being used separately for the
debt-to-income ratio below -- a dollar going to a loan payment is just as
unavailable for saving as a dollar spent on groceries.

**Example:** income = $9,000/mo, living expenses = $6,200/mo, debt payments =
$800/mo → total outflow = $7,000/mo → surplus = **$2,000/mo**

## 3. Savings rate

```
savings_rate = monthly_surplus / monthly_income
```

**Example:** surplus = $2,000, income = $9,000 → savings rate = **22.2%**

Undefined (returns `None` / shown as "N/A") when monthly income is $0.

## 4. Debt-to-income ratio (DTI)

```
debt_to_income = monthly_debt_payments / monthly_income
```

**Example:** debt payments = $1,800/mo, income = $9,000/mo → DTI = **20.0%**

## 5. Emergency-fund coverage

```
emergency_fund_months = liquid_assets / monthly_expenses
```

**Example:** liquid assets = $24,000, expenses = $7,000/mo → **3.43 months**

## 6. Goal funding progress & gap

```
goal_funding_progress = current_savings / target_amount
goal_funding_gap      = max(target_amount - current_savings, 0)
```

**Example:** saved = $40,000, target = $100,000 → progress = **40.0%**, gap = **$60,000**

## 7. Future value of savings (projection engine)

Used for both retirement balances and major-purchase goals. Standard
future-value-of-an-annuity formula with monthly compounding:

```
r = annual_return / 12          (monthly rate)
n = years * 12                  (number of months)

FV = PV * (1 + r)^n + PMT * (((1 + r)^n - 1) / r)
```

When `r = 0` this degenerates to `FV = PV + PMT * n`.

**Example:** current savings = $50,000, contribution = $1,000/mo, 20 years,
6% annual return → projected balance = **$627,551.12**

This is a deterministic projection assuming a constant annual return. Real
investment returns vary year to year; this is not a guarantee of future
performance.

## 8. Retirement income (withdrawal-rate assumption)

```
annual_income  = balance * withdrawal_rate
monthly_income = annual_income / 12
```

The withdrawal rate is always shown explicitly next to the result (e.g. the
traditional illustrative "4% rule": `withdrawal_rate = 0.04`). It is a
simplifying educational heuristic, not personalized advice -- a real safe
withdrawal rate depends on longevity, sequence-of-returns risk, and spending
flexibility, and should be reviewed with a licensed professional.

**Example:** balance = $1,000,000, withdrawal rate = 4% → annual income =
**$40,000**, monthly income = **$3,333.33**

## 9. Major-purchase goal projection

```
projected_savings = future_value_savings(current_savings, monthly_contribution, years, annual_return)
funding_gap        = max(target_cost - projected_savings, 0)
fully_funded        = funding_gap <= 0
```

**Example:** target cost = $60,000, current savings = $10,000, contribution =
$500/mo, 5 years, 5% annual return → projected savings = **$46,836.63**,
gap = **$13,163.37**, not fully funded.

## 10. Scenario comparison (baseline / optimistic / conservative)

The scenario planner runs the same projection three times with different,
clearly labelled assumptions:

| Scenario | Annual return | Withdrawal rate |
|---|---|---|
| Baseline | 6% | 4.0% |
| Optimistic | 8% | 4.5% |
| Conservative | 4% | 3.5% |

These defaults can be overridden per household in `scenario_assumptions`.
They are illustrative anchor points for discussion, not predictions of any
specific household's actual results.

**Example (retirement):** current savings = $50,000, contribution = $1,000/mo,
20 years:

| Scenario | Projected balance | Annual income |
|---|---|---|
| Baseline | $627,551.12 | $25,102.04 |
| Optimistic | $835,360.55 | $37,591.22 |
| Conservative | $477,903.73 | $16,726.63 |

**Example (major purchase):** target cost = $60,000, current savings =
$10,000, contribution = $500/mo, 5 years:

| Scenario | Projected savings | Funding gap |
|---|---|---|
| Baseline | $48,373.52 | $11,626.48 |
| Optimistic | $51,636.89 | $8,363.11 |
| Conservative | $45,359.46 | $14,640.54 |

---

## Invalid-input handling

- Negative amounts for assets, liabilities, income, expenses, or contributions
  raise `ValueError` immediately rather than producing a misleading number.
- A non-positive time horizon (`years <= 0`) raises `ValueError`.
- Ratios with a zero denominator (e.g. savings rate with $0 income) return
  `None`, which the UI renders as "N/A" rather than crashing or showing
  infinity.
