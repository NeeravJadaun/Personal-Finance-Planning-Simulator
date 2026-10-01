"""Planning Checklists -- educational insurance, tax, estate, retirement, and
emergency checklists. These are discussion prompts, not professional advice.
"""

from __future__ import annotations

import streamlit as st

from src.db import CHECKLIST_CATEGORIES, CHECKLIST_STATUSES
from src import models
from src.ui_common import get_conn, household_selector, page_header, professional_disclaimer

st.set_page_config(page_title="Planning Checklists", page_icon="✅", layout="wide")

conn = get_conn()
page_header(
    "Planning Checklists",
    "Educational checklists to guide discovery conversations.",
)
professional_disclaimer()

household_id = household_selector(conn, include_archived=True)
if household_id is None:
    st.stop()

household = models.get_household(conn, household_id)
st.header(household["name"])

items = models.list_checklist_items(conn, household_id)
by_category = {cat: [i for i in items if i["category"] == cat] for cat in CHECKLIST_CATEGORIES}

status_icon = {"Not reviewed": "⚪", "Needs follow-up": "🟡", "Complete": "🟢"}

summary_cols = st.columns(len(CHECKLIST_CATEGORIES))
for col, cat in zip(summary_cols, CHECKLIST_CATEGORIES):
    cat_items = by_category[cat]
    complete = sum(1 for i in cat_items if i["status"] == "Complete")
    col.metric(cat, f"{complete}/{len(cat_items)} complete")

st.divider()

tabs = st.tabs(CHECKLIST_CATEGORIES)
for tab, category in zip(tabs, CHECKLIST_CATEGORIES):
    with tab:
        cat_items = by_category[category]
        if not cat_items:
            st.caption("No checklist items in this category.")
            continue
        for item in cat_items:
            with st.form(f"checklist_form_{item['id']}"):
                c1, c2 = st.columns([3, 1])
                c1.markdown(f"{status_icon.get(item['status'], '⚪')} **{item['item_name']}**")
                new_status = c2.selectbox(
                    "Status",
                    CHECKLIST_STATUSES,
                    index=CHECKLIST_STATUSES.index(item["status"]),
                    key=f"status_{item['id']}",
                    label_visibility="collapsed",
                )
                new_note = st.text_input(
                    "Note", value=item["note"] or "", key=f"note_{item['id']}", placeholder="Add a note..."
                )
                if st.form_submit_button("Save"):
                    models.update_checklist_item(conn, item["id"], status=new_status, note=new_note)
                    st.rerun()
                st.caption(f"Last updated: {item['updated_at']}")

st.divider()
st.info(
    "Checklist items marked **Needs follow-up** automatically appear on the next "
    "meeting agenda generated for this household (Meetings & Follow-up page)."
)
