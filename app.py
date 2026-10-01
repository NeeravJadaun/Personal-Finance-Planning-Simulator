"""Practice Dashboard -- landing page of the Personal Financial Planning
Practice Simulator. All data shown is synthetic and for educational purposes.
"""

from __future__ import annotations

import datetime

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src import models
from src.db import CRM_STAGES
from src.ui_common import (
    CRM_STAGE_RAMP,
    CHART_TEMPLATE,
    get_conn,
    page_header,
)

st.set_page_config(page_title="Practice Dashboard", page_icon="📋", layout="wide")

conn = get_conn()
page_header(
    "Practice Dashboard",
    "Overview of every synthetic household in this demo practice.",
)

metrics = models.get_dashboard_metrics(conn)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Households", metrics["household_count"])
col2.metric("Upcoming meetings (14 days)", len(metrics["upcoming_meetings"]))
col3.metric("Overdue tasks", len(metrics["overdue_tasks"]))
col4.metric("Incomplete discovery profiles", len(metrics["incomplete_profiles"]))

st.subheader("CRM pipeline distribution")
stage_counts = metrics["stage_counts"]
fig = go.Figure(
    go.Bar(
        x=CRM_STAGES,
        y=[stage_counts.get(s, 0) for s in CRM_STAGES],
        marker_color=CRM_STAGE_RAMP,
        text=[stage_counts.get(s, 0) for s in CRM_STAGES],
        textposition="outside",
    )
)
fig.update_layout(
    template=CHART_TEMPLATE,
    yaxis_title="Households",
    xaxis_title=None,
    margin=dict(t=10, b=10, l=10, r=10),
    height=320,
)
st.plotly_chart(fig, width='stretch')

st.subheader("Households")
households = models.list_households(conn, include_archived=False)
advisors = sorted({h["advisor"] for h in households})

f1, f2, f3 = st.columns(3)
advisor_filter = f1.selectbox("Advisor", ["All"] + advisors)
stage_filter = f2.selectbox("CRM stage", ["All"] + CRM_STAGES)
meeting_filter = f3.selectbox(
    "Next meeting", ["All", "Next 7 days", "Next 14 days", "Next 30 days", "None scheduled"]
)

today = datetime.date.today()


def _meeting_matches(next_meeting_date: str | None) -> bool:
    if meeting_filter == "All":
        return True
    if meeting_filter == "None scheduled":
        return next_meeting_date is None
    if next_meeting_date is None:
        return False
    days = {"Next 7 days": 7, "Next 14 days": 14, "Next 30 days": 30}[meeting_filter]
    target = datetime.date.fromisoformat(next_meeting_date)
    return today <= target <= today + datetime.timedelta(days=days)


rows = []
for h in households:
    if advisor_filter != "All" and h["advisor"] != advisor_filter:
        continue
    if stage_filter != "All" and h["crm_stage"] != stage_filter:
        continue
    if not _meeting_matches(h["next_meeting_date"]):
        continue
    missing = models.discovery_completeness(conn, h["id"])
    rows.append(
        {
            "Household": h["name"],
            "Advisor": h["advisor"],
            "CRM Stage": h["crm_stage"],
            "Risk Tolerance": h["risk_tolerance"],
            "Next Meeting": h["next_meeting_date"] or "Not scheduled",
            "Discovery Complete": "Yes" if not missing else f"No ({len(missing)} item(s))",
        }
    )

if rows:
    st.dataframe(pd.DataFrame(rows), width='stretch', hide_index=True)
else:
    st.info("No households match the selected filters.")

col_a, col_b = st.columns(2)

with col_a:
    st.subheader("Upcoming meetings (next 14 days)")
    if metrics["upcoming_meetings"]:
        df = pd.DataFrame(
            [
                {
                    "Household": m["household_name"],
                    "Date": m["meeting_date"],
                    "Status": m["status"],
                }
                for m in metrics["upcoming_meetings"]
            ]
        )
        st.dataframe(df, width='stretch', hide_index=True)
    else:
        st.caption("No meetings scheduled in the next 14 days.")

with col_b:
    st.subheader("Overdue tasks")
    if metrics["overdue_tasks"]:
        rows = []
        for t in metrics["overdue_tasks"]:
            household = models.get_household(conn, t["household_id"])
            rows.append(
                {
                    "Household": household["name"] if household else "—",
                    "Task": t["description"],
                    "Due": t["due_date"],
                    "Assigned to": t["assigned_to"],
                }
            )
        st.dataframe(pd.DataFrame(rows), width='stretch', hide_index=True)
    else:
        st.caption("No overdue tasks. Nice work.")

st.divider()
st.caption(
    "This is a portfolio/demo application. All households, figures, and notes are "
    "fictional and generated for educational purposes only."
)
