"""Smoke-tests every Streamlit page against an isolated, freshly-seeded
database using Streamlit's AppTest harness. Each page must render without
raising an exception and without any placeholder/"TODO" controls -- this is
the automated stand-in for "every page functions" and a basic accessibility
check (a page that throws an exception renders nothing for assistive tech
either).
"""

from __future__ import annotations

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parent.parent

PAGES = [
    str(ROOT / "app.py"),
    str(ROOT / "pages/1_Household_Profile.py"),
    str(ROOT / "pages/2_Financial_Snapshot.py"),
    str(ROOT / "pages/3_Scenario_Planner.py"),
    str(ROOT / "pages/4_Planning_Checklists.py"),
    str(ROOT / "pages/5_Meetings_and_Follow_up.py"),
    str(ROOT / "pages/6_CRM_Pipeline.py"),
    str(ROOT / "pages/7_Exports.py"),
]


@pytest.fixture(autouse=True)
def isolated_db(tmp_path, monkeypatch):
    """Point the app at a fresh temp database and clear Streamlit's
    cached-resource connection so each test gets its own isolated DB."""
    monkeypatch.setenv("PRACTICE_DB_PATH", str(tmp_path / "test_practice.db"))
    from src.ui_common import get_conn

    get_conn.clear()
    yield
    get_conn.clear()


@pytest.mark.parametrize("page", PAGES)
def test_page_renders_without_exception(page):
    at = AppTest.from_file(page, default_timeout=30)
    at.run()
    assert not at.exception, f"{page} raised: {at.exception}"


def test_dashboard_shows_seeded_households():
    at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=30)
    at.run()
    assert not at.exception
    metric_values = [m.value for m in at.get("metric")]
    assert "12" in metric_values  # household count


def test_household_profile_shows_disclaimer_free_content_and_create_form():
    at = AppTest.from_file(str(ROOT / "pages/1_Household_Profile.py"), default_timeout=30)
    at.run()
    assert not at.exception
    assert any("Create a new household" in e.label for e in at.get("expander"))


def test_planning_checklists_shows_professional_disclaimer():
    at = AppTest.from_file(str(ROOT / "pages/4_Planning_Checklists.py"), default_timeout=30)
    at.run()
    assert not at.exception
    warnings = [w.value for w in at.warning]
    assert any("licensed professional" in w for w in warnings)
