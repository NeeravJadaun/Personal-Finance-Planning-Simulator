"""Financial Snapshot -- net worth, cash flow, and goal-funding progress.

All formulas are documented transparently in docs/calculations.md.
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src import calculations, models
from src.ui_common import (
    CATEGORICAL,
    CHART_TEMPLATE,
    fmt_money,
    fmt_months,
    fmt_pct,
    get_conn,
    household_selector,
    page_header,
)

st.set_page_config(page_title="Financial Snapshot", page_icon="📊", layout="wide")

conn = get_conn()
page_header(
    "Financial Snapshot",
    "Transparent net-worth, cash-flow, and goal-funding figures. "
    "See docs/calculations.md for every formula and a worked example.",
)

household_id = household_selector(conn, include_archived=True)
if household_id is None:
    st.stop()

household = models.get_household(conn, household_id)
st.header(household["name"])

summary = models.get_financial_summary(conn, household_id)

st.subheader("Net worth")
c1, c2, c3 = st.columns(3)
c1.metric("Total assets", fmt_money(summary["total_assets"]))
c2.metric("Total liabilities", fmt_money(summary["total_liabilities"]))
c3.metric("Net worth", fmt_money(summary["net_worth"]))

fig = go.Figure(
    go.Bar(
        x=["Assets", "Liabilities"],
        y=[summary["total_assets"], summary["total_liabilities"]],
        marker_color=[CATEGORICAL[0], CATEGORICAL[7]],
        text=[fmt_money(summary["total_assets"]), fmt_money(summary["total_liabilities"])],
        textposition="outside",
    )
)
fig.update_layout(
    template=CHART_TEMPLATE,
    showlegend=False,
    margin=dict(t=10, b=10, l=10, r=10),
    height=300,
    yaxis_title="Dollars",
)
st.plotly_chart(fig, width='stretch')

st.subheader("Monthly cash flow")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Monthly income", fmt_money(summary["monthly_income"]))
c2.metric("Living expenses", fmt_money(summary["monthly_expenses"]))
c3.metric("Debt payments", fmt_money(summary["monthly_debt_payments"]))
c4.metric("Monthly surplus", fmt_money(summary["monthly_surplus"]))
st.caption(
    "Monthly surplus = income − (living expenses + debt payments). "
    "See *Section 2* of docs/calculations.md."
)

st.subheader("Key ratios")
c1, c2, c3 = st.columns(3)
c1.metric("Savings rate", fmt_pct(summary["savings_rate"]))
c2.metric("Debt-to-income ratio", fmt_pct(summary["debt_to_income"]))
c3.metric("Emergency-fund coverage", fmt_months(summary["emergency_fund_months"]))
st.caption(
    "Savings rate = surplus / income. Debt-to-income = debt payments / income. "
    "Emergency-fund coverage = liquid assets / living expenses. "
    "A ratio shows \"N/A\" when its denominator is $0 rather than dividing by zero. "
    "See *Sections 3-5* of docs/calculations.md."
)

st.divider()
st.subheader("Goal funding progress")
goals = models.list_goals(conn, household_id)
if not goals:
    st.info("No goals recorded for this household yet. Add one on the Household Profile page.")
else:
    rows = []
    for g in goals:
        progress = calculations.goal_funding_progress(g["current_savings"], g["target_amount"])
        gap = calculations.goal_funding_gap(g["target_amount"], g["current_savings"])
        rows.append(
            {
                "Goal": g["name"],
                "Type": g["goal_type"].replace("_", " ").title(),
                "Target amount": fmt_money(g["target_amount"]),
                "Target date": g["target_date"] or "—",
                "Current savings": fmt_money(g["current_savings"]),
                "Funding gap": fmt_money(gap),
                "Progress": fmt_pct(progress),
            }
        )
    st.dataframe(pd.DataFrame(rows), width='stretch', hide_index=True)

    fig = go.Figure()
    for idx, g in enumerate(goals):
        progress = calculations.goal_funding_progress(g["current_savings"], g["target_amount"]) or 0
        fig.add_trace(
            go.Bar(
                y=[g["name"]],
                x=[min(progress, 1.0) * 100],
                orientation="h",
                marker_color=CATEGORICAL[idx % len(CATEGORICAL)],
                name=g["name"],
                text=f"{progress * 100:.0f}%",
                textposition="inside",
                showlegend=False,
            )
        )
    fig.update_layout(
        template=CHART_TEMPLATE,
        xaxis_title="Percent funded",
        xaxis_range=[0, 100],
        margin=dict(t=10, b=10, l=10, r=10),
        height=120 + 40 * len(goals),
    )
    st.plotly_chart(fig, width='stretch')

st.caption(
    "Projections elsewhere in this app (Scenario Planner) are deterministic estimates, "
    "not guarantees of future performance."
)
