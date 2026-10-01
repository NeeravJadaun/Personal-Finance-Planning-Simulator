"""Scenario Planner -- deterministic retirement and major-purchase projections.

These are illustrative projections based on the assumptions shown on screen,
not guarantees of future performance and not a recommendation to buy or sell
any security. See docs/calculations.md for the underlying formulas.
"""

from __future__ import annotations

import datetime

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src import calculations, models
from src.ui_common import (
    CHART_TEMPLATE,
    SCENARIO_COLORS,
    fmt_money,
    fmt_pct,
    get_conn,
    household_selector,
    page_header,
)

st.set_page_config(page_title="Scenario Planner", page_icon="🧮", layout="wide")

conn = get_conn()
page_header(
    "Scenario Planner",
    "Deterministic baseline / optimistic / conservative projections. "
    "Not a guarantee of future results and not a securities recommendation.",
)

household_id = household_selector(conn, include_archived=True)
if household_id is None:
    st.stop()

household = models.get_household(conn, household_id)
st.header(household["name"])

tab_retirement, tab_purchase = st.tabs(["Retirement", "Major Purchase"])


def _years_until(target_date: str | None, fallback: float) -> float:
    if not target_date:
        return fallback
    try:
        target = datetime.date.fromisoformat(target_date)
    except ValueError:
        return fallback
    days = (target - datetime.date.today()).days
    return max(days / 365, 0.5)


def _scenario_table(results: dict, columns: list[tuple[str, str]]) -> pd.DataFrame:
    rows = []
    for scenario in ["baseline", "optimistic", "conservative"]:
        r = results[scenario]
        row = {"Scenario": scenario.title()}
        for key, label in columns:
            row[label] = r[key]
        rows.append(row)
    return pd.DataFrame(rows)


with tab_retirement:
    retirement_goals = models.list_goals(conn, household_id, goal_type="retirement")
    if not retirement_goals:
        st.info("No retirement goal recorded for this household. Add one on the Household Profile page.")
    else:
        goal = retirement_goals[0]
        st.caption(f"Based on goal: **{goal['name']}** (target {fmt_money(goal['target_amount'])})")

        c1, c2, c3 = st.columns(3)
        current_savings = c1.number_input(
            "Current retirement savings", min_value=0.0, value=float(goal["current_savings"]), step=1000.0
        )
        monthly_contribution = c2.number_input(
            "Monthly contribution", min_value=0.0, value=float(goal["monthly_contribution"]), step=50.0
        )
        default_years = _years_until(goal["target_date"], 20)
        years = c3.slider("Years to retirement", min_value=1, max_value=50, value=int(round(default_years)))

        assumptions = models.get_scenario_assumptions(conn, goal["id"])
        with st.expander("Adjust scenario assumptions"):
            adjusted = {}
            for scenario in ["baseline", "optimistic", "conservative"]:
                sc1, sc2 = st.columns(2)
                ret = sc1.slider(
                    f"{scenario.title()} annual return",
                    min_value=0.0,
                    max_value=0.15,
                    value=float(assumptions[scenario]["annual_return"]),
                    step=0.005,
                    format="%.3f",
                    key=f"ret_{scenario}",
                )
                wd = sc2.slider(
                    f"{scenario.title()} withdrawal rate",
                    min_value=0.01,
                    max_value=0.08,
                    value=float(assumptions[scenario]["withdrawal_rate"] or 0.04),
                    step=0.0025,
                    format="%.4f",
                    key=f"wd_{scenario}",
                )
                adjusted[scenario] = calculations.ScenarioAssumption(scenario, ret, wd)
            if st.button("Save these assumptions for this goal"):
                for scenario, a in adjusted.items():
                    models.set_scenario_assumption(
                        conn, goal["id"], scenario, annual_return=a.annual_return, withdrawal_rate=a.withdrawal_rate
                    )
                st.success("Saved.")
                st.rerun()

        scenario_assumptions = {
            name: calculations.ScenarioAssumption(name, a.annual_return, a.withdrawal_rate)
            for name, a in adjusted.items()
        }
        results = calculations.run_retirement_scenarios(
            current_savings, monthly_contribution, years, scenario_assumptions
        )

        df = _scenario_table(
            results,
            [
                ("annual_return", "Annual return"),
                ("withdrawal_rate", "Withdrawal rate"),
                ("projected_balance", "Projected balance"),
                ("annual_income", "Est. annual income"),
                ("monthly_income", "Est. monthly income"),
            ],
        )
        display_df = df.copy()
        display_df["Annual return"] = display_df["Annual return"].map(fmt_pct)
        display_df["Withdrawal rate"] = display_df["Withdrawal rate"].map(fmt_pct)
        display_df["Projected balance"] = display_df["Projected balance"].map(fmt_money)
        display_df["Est. annual income"] = display_df["Est. annual income"].map(fmt_money)
        display_df["Est. monthly income"] = display_df["Est. monthly income"].map(fmt_money)
        st.dataframe(display_df, width='stretch', hide_index=True)

        fig = go.Figure()
        for scenario in ["baseline", "optimistic", "conservative"]:
            fig.add_trace(
                go.Bar(
                    x=[scenario.title()],
                    y=[results[scenario]["projected_balance"]],
                    marker_color=SCENARIO_COLORS[scenario],
                    name=scenario.title(),
                    text=fmt_money(results[scenario]["projected_balance"]),
                    textposition="outside",
                )
            )
        fig.update_layout(
            template=CHART_TEMPLATE,
            showlegend=False,
            yaxis_title=f"Projected balance after {years} years",
            margin=dict(t=10, b=10, l=10, r=10),
            height=320,
        )
        st.plotly_chart(fig, width='stretch')

        st.caption(
            "Projection uses monthly-compounding future value of current savings plus "
            "contributions at a constant assumed annual return (docs/calculations.md, "
            "Section 7). Retirement income uses an explicit withdrawal-rate assumption "
            "(Section 8) -- not a personalized recommendation."
        )

with tab_purchase:
    purchase_goals = models.list_goals(conn, household_id, goal_type="major_purchase")
    if not purchase_goals:
        st.info("No major-purchase goal recorded for this household. Add one on the Household Profile page.")
    else:
        goal = purchase_goals[0]
        st.caption(f"Based on goal: **{goal['name']}** (target {fmt_money(goal['target_amount'])})")

        c1, c2, c3, c4 = st.columns(4)
        target_cost = c1.number_input("Target cost", min_value=0.0, value=float(goal["target_amount"]), step=1000.0)
        current_savings = c2.number_input(
            "Current savings", min_value=0.0, value=float(goal["current_savings"]), step=500.0
        )
        monthly_contribution = c3.number_input(
            "Monthly contribution", min_value=0.0, value=float(goal["monthly_contribution"]), step=50.0
        )
        default_years = _years_until(goal["target_date"], 5)
        years = c4.slider("Years to purchase", min_value=1, max_value=30, value=int(round(default_years)))

        results = calculations.run_major_purchase_scenarios(
            target_cost, current_savings, years, monthly_contribution
        )

        df = _scenario_table(
            results,
            [
                ("annual_return", "Annual return"),
                ("projected_savings", "Projected savings"),
                ("funding_gap", "Funding gap"),
                ("fully_funded", "Fully funded?"),
            ],
        )
        display_df = df.copy()
        display_df["Annual return"] = display_df["Annual return"].map(fmt_pct)
        display_df["Projected savings"] = display_df["Projected savings"].map(fmt_money)
        display_df["Funding gap"] = display_df["Funding gap"].map(fmt_money)
        display_df["Fully funded?"] = display_df["Fully funded?"].map({True: "Yes", False: "No"})
        st.dataframe(display_df, width='stretch', hide_index=True)

        fig = go.Figure()
        for scenario in ["baseline", "optimistic", "conservative"]:
            fig.add_trace(
                go.Bar(
                    x=[scenario.title()],
                    y=[results[scenario]["projected_savings"]],
                    marker_color=SCENARIO_COLORS[scenario],
                    name=scenario.title(),
                    text=fmt_money(results[scenario]["projected_savings"]),
                    textposition="outside",
                )
            )
        fig.add_hline(
            y=target_cost,
            line_dash="dash",
            annotation_text=f"Target cost ({fmt_money(target_cost)})",
        )
        fig.update_layout(
            template=CHART_TEMPLATE,
            showlegend=False,
            yaxis_title=f"Projected savings after {years} years",
            margin=dict(t=10, b=10, l=10, r=10),
            height=320,
        )
        st.plotly_chart(fig, width='stretch')

        st.caption(
            "Projection uses the same monthly-compounding future-value formula as the "
            "retirement projection (docs/calculations.md, Sections 7 & 9)."
        )

st.divider()
st.caption(
    "These projections do not recommend any specific security, account, or investment "
    "product, and actual returns will vary from any constant-rate assumption shown here."
)
