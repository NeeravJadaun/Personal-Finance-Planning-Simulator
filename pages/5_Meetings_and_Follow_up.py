"""Meetings and Follow-up -- schedule meetings, generate agendas, record notes,
and track follow-up tasks."""

from __future__ import annotations

import datetime

import pandas as pd
import streamlit as st

from src import models
from src.ui_common import get_conn, household_selector, page_header

st.set_page_config(page_title="Meetings & Follow-up", page_icon="🗓️", layout="wide")

conn = get_conn()
page_header("Meetings & Follow-up", "Schedule meetings, prepare agendas, and track tasks.")

household_id = household_selector(conn, include_archived=True)
if household_id is None:
    st.stop()

household = models.get_household(conn, household_id)
st.header(household["name"])

tab_meetings, tab_tasks = st.tabs(["Meetings", "Tasks"])

with tab_meetings:
    with st.expander("+ Schedule a new meeting", expanded=False):
        with st.form("create_meeting_form", clear_on_submit=True):
            meeting_date = st.date_input("Meeting date", value=datetime.date.today() + datetime.timedelta(days=7))
            preview_agenda = models.generate_agenda(conn, household_id)
            st.text_area("Agenda preview (auto-generated from discovery gaps, goals, and checklist follow-ups)",
                         value=preview_agenda, height=200, disabled=True)
            if st.form_submit_button("Schedule meeting"):
                models.create_meeting(
                    conn, household_id, meeting_date=meeting_date.isoformat(), agenda=preview_agenda
                )
                st.success("Meeting scheduled.")
                st.rerun()

    meetings = models.list_meetings(conn, household_id)
    if not meetings:
        st.info("No meetings recorded for this household yet.")
    else:
        for m in meetings:
            with st.container(border=True):
                c1, c2 = st.columns([3, 1])
                c1.markdown(f"**{m['meeting_date']}** — {m['status']}")
                with st.expander("View agenda"):
                    st.text(m["agenda"] or "(no agenda)")
                with st.form(f"meeting_update_{m['id']}"):
                    new_status = st.selectbox(
                        "Status",
                        ["Scheduled", "Completed", "Cancelled"],
                        index=["Scheduled", "Completed", "Cancelled"].index(m["status"])
                        if m["status"] in ["Scheduled", "Completed", "Cancelled"]
                        else 0,
                        key=f"status_{m['id']}",
                    )
                    notes = st.text_area("Meeting notes", value=m["notes"] or "", key=f"notes_{m['id']}")
                    recs = st.text_area(
                        "Recommendations for further professional review",
                        value=m["recommendations"] or "",
                        key=f"recs_{m['id']}",
                        help="e.g. 'Recommend household consult a licensed tax professional about...'",
                    )
                    if st.form_submit_button("Save meeting"):
                        models.update_meeting(
                            conn, m["id"], status=new_status, notes=notes, recommendations=recs
                        )
                        st.success("Saved.")
                        st.rerun()

with tab_tasks:
    with st.form("create_task_form", clear_on_submit=True):
        st.caption("Create a follow-up task")
        c1, c2, c3 = st.columns(3)
        description = c1.text_input("Description")
        assigned_to = c2.text_input("Assigned to", value="Advisor")
        due_date = c3.date_input("Due date", value=datetime.date.today() + datetime.timedelta(days=7))
        meeting_ids = [m["id"] for m in models.list_meetings(conn, household_id)]
        linked_meeting = st.selectbox(
            "Link to meeting (optional)",
            options=[None] + meeting_ids,
            format_func=lambda i: "None" if i is None else f"Meeting on {models.get_meeting(conn, i)['meeting_date']}",
        )
        if st.form_submit_button("Create task"):
            if not description.strip():
                st.error("Description is required.")
            else:
                models.create_task(
                    conn,
                    household_id,
                    description=description,
                    assigned_to=assigned_to,
                    due_date=due_date.isoformat(),
                    meeting_id=linked_meeting,
                )
                st.success("Task created.")
                st.rerun()

    st.divider()
    tasks = models.list_tasks(conn, household_id)
    open_tasks = [t for t in tasks if t["status"] == "Open"]
    complete_tasks = [t for t in tasks if t["status"] == "Complete"]

    st.subheader(f"Open tasks ({len(open_tasks)})")
    today = datetime.date.today().isoformat()
    if open_tasks:
        for t in open_tasks:
            overdue = t["due_date"] and t["due_date"] < today
            c1, c2 = st.columns([4, 1])
            label = f"{'🔴' if overdue else '⚪'} **{t['description']}** — assigned to {t['assigned_to']}, due {t['due_date'] or 'unscheduled'}"
            c1.markdown(label)
            if c2.button("Mark complete", key=f"complete_{t['id']}"):
                models.complete_task(conn, t["id"])
                st.rerun()
    else:
        st.caption("No open tasks.")

    st.subheader(f"Completed tasks ({len(complete_tasks)})")
    if complete_tasks:
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "Description": t["description"],
                        "Assigned to": t["assigned_to"],
                        "Completed at": t["completed_at"],
                    }
                    for t in complete_tasks
                ]
            ),
            width='stretch',
            hide_index=True,
        )
    else:
        st.caption("No completed tasks yet.")
