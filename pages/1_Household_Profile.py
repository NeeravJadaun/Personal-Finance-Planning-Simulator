"""Household Profile -- create, read, update, and archive synthetic households."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from src import models
from src.audit import get_events
from src.models import FINANCIAL_CATEGORIES, GOAL_TYPES
from src.ui_common import fmt_money, get_conn, household_selector, page_header

st.set_page_config(page_title="Household Profile", page_icon="🏠", layout="wide")

conn = get_conn()
page_header("Household Profile", "Create and manage synthetic household records.")

with st.expander("+ Create a new household"):
    with st.form("create_household_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        name = c1.text_input("Household name")
        advisor = c2.text_input("Advisor", value="Avery Simmons")
        c3, c4 = st.columns(2)
        risk = c3.selectbox("Risk tolerance", ["Conservative", "Moderate", "Aggressive"])
        contact = c4.selectbox("Contact preference", ["Email", "Phone", "Text", "Mail"])
        notes = st.text_area("Notes")
        submitted = st.form_submit_button("Create household")
        if submitted:
            if not name.strip():
                st.error("Household name is required.")
            else:
                new_id = models.create_household(
                    conn,
                    name=name,
                    advisor=advisor,
                    risk_tolerance=risk,
                    contact_preference=contact,
                    notes=notes,
                )
                st.session_state["selected_household_id"] = new_id
                st.success(f"Created household '{name}'.")
                st.rerun()

household_id = household_selector(conn, include_archived=True)
if household_id is None:
    st.stop()

household = models.get_household(conn, household_id)
if household["archived"]:
    st.warning("This household is archived (read-only view below).")

st.header(household["name"])
left, right = st.columns([2, 1])

with left:
    st.subheader("Overview")
    with st.form("edit_household_form"):
        c1, c2 = st.columns(2)
        advisor = c1.text_input("Advisor", value=household["advisor"])
        risk = c2.selectbox(
            "Risk tolerance",
            ["Conservative", "Moderate", "Aggressive"],
            index=["Conservative", "Moderate", "Aggressive"].index(household["risk_tolerance"])
            if household["risk_tolerance"] in ["Conservative", "Moderate", "Aggressive"]
            else 1,
        )
        c3, c4 = st.columns(2)
        contact = c3.selectbox(
            "Contact preference",
            ["Email", "Phone", "Text", "Mail"],
            index=["Email", "Phone", "Text", "Mail"].index(household["contact_preference"])
            if household["contact_preference"] in ["Email", "Phone", "Text", "Mail"]
            else 0,
        )
        c4.text_input("CRM stage (change on CRM Pipeline page)", value=household["crm_stage"], disabled=True)
        notes = st.text_area("Notes", value=household["notes"] or "")
        save = st.form_submit_button("Save changes", disabled=bool(household["archived"]))
        if save:
            models.update_household(
                conn,
                household_id,
                advisor=advisor,
                risk_tolerance=risk,
                contact_preference=contact,
                notes=notes,
            )
            st.success("Household updated.")
            st.rerun()

with right:
    st.subheader("Status")
    st.write(f"**CRM stage:** {household['crm_stage']}")
    st.write(f"**Next meeting:** {household['next_meeting_date'] or 'Not scheduled'}")
    st.write(f"**Created:** {household['created_at']}")
    if household["archived"]:
        if st.button("Unarchive household"):
            models.set_archived(conn, household_id, False)
            st.rerun()
    else:
        if st.button("Archive household"):
            models.set_archived(conn, household_id, True)
            st.rerun()

st.divider()
st.subheader("Household members")
people = models.list_people(conn, household_id)
if people:
    st.dataframe(
        pd.DataFrame(
            [
                {
                    "Name": p["name"],
                    "Relationship": p["relationship"],
                    "Date of birth": p["date_of_birth"] or "—",
                    "Dependant": "Yes" if p["is_dependant"] else "No",
                }
                for p in people
            ]
        ),
        width='stretch',
        hide_index=True,
    )
    del_cols = st.columns(len(people)) if len(people) <= 6 else None
    with st.expander("Remove a household member"):
        to_remove = st.selectbox(
            "Member", options=[p["id"] for p in people], format_func=lambda i: next(p["name"] for p in people if p["id"] == i)
        )
        if st.button("Remove member"):
            models.delete_person(conn, to_remove)
            st.rerun()
else:
    st.caption("No household members recorded yet.")

with st.form("add_person_form", clear_on_submit=True):
    st.caption("Add a household member")
    c1, c2, c3, c4 = st.columns(4)
    p_name = c1.text_input("Name")
    p_rel = c2.selectbox("Relationship", ["Self", "Spouse", "Partner", "Child", "Other"])
    p_dob = c3.text_input("Date of birth (YYYY-MM-DD)", placeholder="1990-01-01")
    p_dependant = c4.checkbox("Dependant")
    if st.form_submit_button("Add member"):
        if not p_name.strip():
            st.error("Name is required.")
        else:
            models.add_person(
                conn,
                household_id,
                name=p_name,
                relationship=p_rel,
                date_of_birth=p_dob or None,
                is_dependant=p_dependant,
            )
            st.rerun()

st.divider()
st.subheader("Financial facts")
items = models.list_financial_items(conn, household_id)
if items:
    st.dataframe(
        pd.DataFrame(
            [
                {
                    "Category": i["category"].replace("_", " ").title(),
                    "Subcategory": i["subcategory"],
                    "Amount": fmt_money(i["amount"]),
                    "Frequency": i["frequency"],
                    "As of": i["as_of_date"],
                }
                for i in items
            ]
        ),
        width='stretch',
        hide_index=True,
    )
    with st.expander("Remove a financial item"):
        to_remove = st.selectbox(
            "Item",
            options=[i["id"] for i in items],
            format_func=lambda i: next(
                f"{it['category']}: {it['subcategory']} ({fmt_money(it['amount'])})"
                for it in items
                if it["id"] == i
            ),
        )
        if st.button("Remove financial item"):
            models.delete_financial_item(conn, to_remove)
            st.rerun()
else:
    st.caption("No financial facts recorded yet.")

with st.form("add_financial_item_form", clear_on_submit=True):
    st.caption("Add a financial fact")
    c1, c2, c3, c4 = st.columns(4)
    f_category = c1.selectbox("Category", FINANCIAL_CATEGORIES)
    f_subcategory = c2.text_input("Subcategory", placeholder="e.g. Cash & Checking")
    f_amount = c3.number_input("Amount", min_value=0.0, step=100.0)
    f_frequency = c4.selectbox("Frequency", ["one_time", "monthly", "annual"])
    if st.form_submit_button("Add financial item"):
        if not f_subcategory.strip():
            st.error("Subcategory is required.")
        else:
            models.add_financial_item(
                conn,
                household_id,
                category=f_category,
                subcategory=f_subcategory,
                amount=f_amount,
                frequency=f_frequency,
            )
            st.rerun()

st.divider()
st.subheader("Goals")
goals = models.list_goals(conn, household_id)
if goals:
    st.dataframe(
        pd.DataFrame(
            [
                {
                    "Name": g["name"],
                    "Type": g["goal_type"].replace("_", " ").title(),
                    "Target amount": fmt_money(g["target_amount"]),
                    "Target date": g["target_date"] or "—",
                    "Current savings": fmt_money(g["current_savings"]),
                    "Monthly contribution": fmt_money(g["monthly_contribution"]),
                    "Priority": g["priority"],
                }
                for g in goals
            ]
        ),
        width='stretch',
        hide_index=True,
    )
    with st.expander("Remove a goal"):
        to_remove = st.selectbox(
            "Goal", options=[g["id"] for g in goals], format_func=lambda i: next(g["name"] for g in goals if g["id"] == i)
        )
        if st.button("Remove goal"):
            models.delete_goal(conn, to_remove)
            st.rerun()
else:
    st.caption("No goals recorded yet.")

with st.form("add_goal_form", clear_on_submit=True):
    st.caption("Add a goal")
    c1, c2, c3 = st.columns(3)
    g_name = c1.text_input("Goal name")
    g_type = c2.selectbox("Type", GOAL_TYPES)
    g_priority = c3.selectbox("Priority", ["High", "Medium", "Low"])
    c4, c5, c6 = st.columns(3)
    g_target = c4.number_input("Target amount", min_value=0.0, step=1000.0)
    g_current = c5.number_input("Current savings", min_value=0.0, step=500.0)
    g_contribution = c6.number_input("Monthly contribution", min_value=0.0, step=50.0)
    g_date = st.text_input("Target date (YYYY-MM-DD)", placeholder="2045-01-01")
    if st.form_submit_button("Add goal"):
        if not g_name.strip():
            st.error("Goal name is required.")
        else:
            models.add_goal(
                conn,
                household_id,
                name=g_name,
                goal_type=g_type,
                target_amount=g_target,
                target_date=g_date or None,
                current_savings=g_current,
                monthly_contribution=g_contribution,
                priority=g_priority,
            )
            st.rerun()

st.divider()
st.subheader("Activity history")
events = get_events(conn, household_id=household_id, limit=100)
if events:
    st.dataframe(
        pd.DataFrame(
            [
                {
                    "Timestamp": e["timestamp"],
                    "Actor": e["actor"],
                    "Event": e["event_type"],
                    "Entity": e["entity_type"],
                    "Description": e["description"],
                }
                for e in events
            ]
        ),
        width='stretch',
        hide_index=True,
        height=300,
    )
else:
    st.caption("No activity recorded yet.")
