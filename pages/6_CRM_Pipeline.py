"""CRM Pipeline -- track households through Prospect -> ... -> Ongoing Service."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from src import models
from src.db import CRM_STAGES
from src.ui_common import get_conn, household_selector, page_header

st.set_page_config(page_title="CRM Pipeline", page_icon="🔁", layout="wide")

conn = get_conn()
page_header("CRM Pipeline", "Track households through the practice's standard pipeline.")

st.subheader("Pipeline board")
households = models.list_households(conn, include_archived=False)
cols = st.columns(len(CRM_STAGES))
for col, stage in zip(cols, CRM_STAGES):
    with col:
        st.markdown(f"**{stage}**")
        stage_households = [h for h in households if h["crm_stage"] == stage]
        st.caption(f"{len(stage_households)} household(s)")
        for h in stage_households:
            st.markdown(f"- {h['name']}")

st.divider()

household_id = household_selector(conn, include_archived=True)
if household_id is None:
    st.stop()

household = models.get_household(conn, household_id)
st.header(household["name"])
st.write(f"Current stage: **{household['crm_stage']}**")

with st.form("change_stage_form"):
    c1, c2 = st.columns(2)
    new_stage = c1.selectbox(
        "New stage", CRM_STAGES, index=CRM_STAGES.index(household["crm_stage"])
    )
    actor = c2.text_input("Actor", value="Advisor")
    note = st.text_area("Note")
    if st.form_submit_button("Update stage"):
        if new_stage == household["crm_stage"]:
            st.warning("Household is already in this stage.")
        else:
            models.change_crm_stage(conn, household_id, new_stage, actor=actor, note=note)
            st.success(f"Moved to {new_stage}.")
            st.rerun()

st.subheader("Stage history")
history = models.get_crm_history(conn, household_id)
if history:
    st.dataframe(
        pd.DataFrame(
            [
                {"Date": h["changed_at"], "Stage": h["stage"], "Actor": h["actor"], "Note": h["note"] or ""}
                for h in history
            ]
        ),
        width='stretch',
        hide_index=True,
    )
else:
    st.caption("No stage history yet.")

st.divider()
col_a, col_b = st.columns(2)

with col_a:
    st.subheader("Stalled households")
    st.caption("No CRM stage change in more than 30 days (excludes Ongoing Service).")
    stalled = models.get_stalled_households(conn, days_threshold=30)
    if stalled:
        st.dataframe(
            pd.DataFrame(
                [
                    {"Household": s["name"], "Stage": s["crm_stage"], "Stage since": s["stage_since"] or "Unknown"}
                    for s in stalled
                ]
            ),
            width='stretch',
            hide_index=True,
        )
    else:
        st.caption("No stalled households.")

with col_b:
    st.subheader("Overdue follow-up (all households)")
    overdue = models.get_overdue_tasks(conn)
    if overdue:
        rows = []
        for t in overdue:
            h = models.get_household(conn, t["household_id"])
            rows.append(
                {
                    "Household": h["name"] if h else "—",
                    "Task": t["description"],
                    "Due": t["due_date"],
                    "Assigned to": t["assigned_to"],
                }
            )
        st.dataframe(pd.DataFrame(rows), width='stretch', hide_index=True)
    else:
        st.caption("No overdue tasks.")
