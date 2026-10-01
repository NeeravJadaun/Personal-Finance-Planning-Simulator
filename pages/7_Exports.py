"""Exports -- advisor Excel workbook and client-friendly plan summary."""

from __future__ import annotations

import datetime

import streamlit as st

from src import exports, models
from src.ui_common import get_conn, household_selector, page_header

st.set_page_config(page_title="Exports", page_icon="📤", layout="wide")

conn = get_conn()
page_header(
    "Exports",
    "Generate an advisor workbook and a client-ready plan summary. "
    "All exports are labelled 'Synthetic educational example'.",
)

household_id = household_selector(conn, include_archived=True)
if household_id is None:
    st.stop()

household = models.get_household(conn, household_id)
st.header(household["name"])

safe_name = "".join(c if c.isalnum() else "_" for c in household["name"])
timestamp = datetime.date.today().isoformat()

col1, col2 = st.columns(2)

with col1:
    st.subheader("Advisor workbook (Excel)")
    st.caption(
        "Includes household summary, financial snapshot, goals, scenario projections, "
        "checklists, meetings, tasks, and audit history."
    )
    workbook_bytes = exports.generate_workbook(conn, household_id)
    st.download_button(
        "Download Excel workbook",
        data=workbook_bytes,
        file_name=f"{safe_name}_advisor_workbook_{timestamp}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

with col2:
    st.subheader("Client plan summary (HTML)")
    st.caption(
        "A clean, printable summary suitable for saving to PDF (use your browser's "
        "Print > Save as PDF after opening the downloaded file)."
    )
    html_str = exports.generate_plan_summary_html(conn, household_id)
    st.download_button(
        "Download plan summary (HTML)",
        data=html_str,
        file_name=f"{safe_name}_plan_summary_{timestamp}.html",
        mime="text/html",
    )
    with st.expander("Preview plan summary"):
        st.components.v1.html(html_str, height=600, scrolling=True)

st.divider()
st.caption(
    "Both exports are generated on demand from the data currently stored for this "
    "household and are labelled as synthetic educational examples throughout."
)
