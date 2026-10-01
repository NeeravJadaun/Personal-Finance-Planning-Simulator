"""Shared Streamlit helpers: DB connection, formatting, banners, charts."""

from __future__ import annotations

import sqlite3

import streamlit as st

from src import db, models, seed_data

# Validated default categorical palette (see dataviz skill reference palette).
# Fixed slot order -- never cycle or reassign per chart.
CATEGORICAL = [
    "#2a78d6",  # 1 blue
    "#eb6834",  # 2 orange
    "#1baf7a",  # 3 aqua
    "#eda100",  # 4 yellow
    "#e87ba4",  # 5 magenta
    "#008300",  # 6 green
    "#4a3aa7",  # 7 violet
    "#e34948",  # 8 red
]

# Six-step ordinal ramp (single blue hue, light -> dark) for the ordered
# CRM pipeline stages. Starts at step 250 to clear the 2:1 contrast floor
# on a light surface.
CRM_STAGE_RAMP = ["#86b6ef", "#5598e7", "#2a78d6", "#1c5cab", "#184f95", "#0d366b"]

STATUS_COLORS = {
    "good": "#0ca30c",
    "warning": "#fab219",
    "serious": "#ec835a",
    "critical": "#d03b3b",
}

SCENARIO_COLORS = {
    "baseline": CATEGORICAL[0],
    "optimistic": CATEGORICAL[2],
    "conservative": CATEGORICAL[1],
}

CHART_TEMPLATE = "plotly_white"


@st.cache_resource
def get_conn() -> sqlite3.Connection:
    conn = db.get_connection()
    db.init_db(conn)
    if not models.list_households(conn, include_archived=True):
        seed_data.seed_all(conn)
    return conn


def fmt_money(value: float | None) -> str:
    if value is None:
        return "N/A"
    return f"${value:,.2f}"


def fmt_pct(value: float | None) -> str:
    if value is None:
        return "N/A"
    return f"{value * 100:.1f}%"


def fmt_months(value: float | None) -> str:
    if value is None:
        return "N/A"
    return f"{value:.1f} months"


def synthetic_banner() -> None:
    st.caption("Synthetic educational example — no real clients, accounts, or financial advice.")


def professional_disclaimer() -> None:
    st.warning(
        "**Educational tool only.** Nothing on this page is personalized financial, tax, "
        "legal, or insurance advice. Specialized guidance must be reviewed by a licensed "
        "professional before any household acts on it.",
        icon="⚠️",
    )


def household_selector(
    conn: sqlite3.Connection, key: str = "selected_household_id", include_archived: bool = False
) -> int | None:
    """Render a sidebar household picker and return the selected household id."""
    households = models.list_households(conn, include_archived=include_archived)
    if not households:
        st.sidebar.info("No households yet. Create one on the Household Profile page.")
        return None

    ids = [h["id"] for h in households]
    labels = {h["id"]: f"{h['name']} — {h['crm_stage']}" for h in households}

    if key not in st.session_state or st.session_state[key] not in ids:
        st.session_state[key] = ids[0]

    return st.sidebar.selectbox(
        "Household",
        options=ids,
        format_func=lambda i: labels[i],
        key=key,
    )


def page_header(title: str, subtitle: str = "") -> None:
    st.title(title)
    synthetic_banner()
    if subtitle:
        st.caption(subtitle)
