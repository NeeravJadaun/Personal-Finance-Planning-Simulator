"""End-to-end integration test: discovery through export for one household,
covering every workflow described in the project brief in a single pass."""

from __future__ import annotations

from datetime import date, timedelta

from openpyxl import load_workbook

from src import calculations, exports, models
from src.audit import get_events


def test_full_workflow_discovery_through_export(conn, tmp_path):
    # 1. Create a household (discovery starts here).
    household_id = models.create_household(
        conn,
        name="Test Household",
        advisor="Avery Simmons",
        risk_tolerance="Moderate",
        contact_preference="Email",
        notes="Integration test household.",
    )

    # Discovery profile starts incomplete.
    missing = models.discovery_completeness(conn, household_id)
    assert missing  # no people, financials, or goals yet

    # 2. Complete the discovery profile: household members, financial facts,
    # goals, risk tolerance (already set at creation).
    models.add_person(conn, household_id, name="Jamie Doe", relationship="Self")
    models.add_person(conn, household_id, name="Riley Doe", relationship="Spouse")

    models.add_financial_item(conn, household_id, category="asset", subcategory="Cash & Checking", amount=10000)
    models.add_financial_item(conn, household_id, category="asset", subcategory="Emergency Fund", amount=15000)
    models.add_financial_item(conn, household_id, category="liability", subcategory="Mortgage", amount=200000)
    models.add_financial_item(
        conn, household_id, category="income", subcategory="Salary", amount=9000, frequency="monthly"
    )
    models.add_financial_item(
        conn, household_id, category="expense", subcategory="Housing", amount=2500, frequency="monthly"
    )
    models.add_financial_item(
        conn, household_id, category="debt_payment", subcategory="Mortgage Payment", amount=1200, frequency="monthly"
    )

    retirement_goal_id = models.add_goal(
        conn,
        household_id,
        name="Retirement",
        goal_type="retirement",
        target_amount=1_500_000,
        target_date=(date.today() + timedelta(days=365 * 25)).isoformat(),
        current_savings=25000,
        monthly_contribution=800,
    )
    purchase_goal_id = models.add_goal(
        conn,
        household_id,
        name="New car",
        goal_type="major_purchase",
        target_amount=35000,
        target_date=(date.today() + timedelta(days=365 * 3)).isoformat(),
        current_savings=5000,
        monthly_contribution=400,
    )

    missing = models.discovery_completeness(conn, household_id)
    assert missing == []  # discovery profile now complete

    # 3. Financial snapshot calculations run cleanly and match direct formulas.
    summary = models.get_financial_summary(conn, household_id)
    assert summary["net_worth"] == calculations.net_worth(25000, 200000)
    assert summary["savings_rate"] is not None
    assert summary["debt_to_income"] == 1200 / 9000

    # 4. Scenario planner: run baseline/optimistic/conservative projections
    # for both goals, and persist a custom assumption.
    retirement_results = calculations.run_retirement_scenarios(25000, 800, 25)
    assert set(retirement_results) == {"baseline", "optimistic", "conservative"}

    models.set_scenario_assumption(conn, retirement_goal_id, "baseline", annual_return=0.065, withdrawal_rate=0.04)
    assumptions = models.get_scenario_assumptions(conn, retirement_goal_id)
    assert assumptions["baseline"]["annual_return"] == 0.065

    purchase_results = calculations.run_major_purchase_scenarios(35000, 5000, 3, 400)
    assert set(purchase_results) == {"baseline", "optimistic", "conservative"}

    # 5. Planning checklists: mark some items reviewed.
    checklist_items = models.list_checklist_items(conn, household_id)
    assert len(checklist_items) > 0
    first_item = checklist_items[0]
    models.update_checklist_item(conn, first_item["id"], status="Needs follow-up", note="Discuss at next meeting")

    # 6. Meeting prep: generate an agenda (should now reflect the
    # needs-follow-up checklist item, not the earlier missing-discovery
    # prompts since discovery is complete) and schedule a meeting.
    agenda = models.generate_agenda(conn, household_id)
    assert "No household members recorded" not in agenda
    assert first_item["item_name"] in agenda

    meeting_id = models.create_meeting(
        conn, household_id, meeting_date=(date.today() + timedelta(days=7)).isoformat(), agenda=agenda
    )
    models.update_meeting(
        conn,
        meeting_id,
        status="Completed",
        notes="Reviewed full financial picture.",
        recommendations="Recommend household consult a licensed tax professional about mortgage interest deduction.",
    )

    # 7. Follow-up task tied to the meeting; mark it complete.
    task_id = models.create_task(
        conn,
        household_id,
        description="Send updated beneficiary form",
        assigned_to="Jamie Doe",
        due_date=(date.today() + timedelta(days=14)).isoformat(),
        meeting_id=meeting_id,
    )
    models.complete_task(conn, task_id)
    tasks = models.list_tasks(conn, household_id)
    assert all(t["status"] == "Complete" for t in tasks if t["id"] == task_id)

    # 8. CRM pipeline: progress the household through several stages.
    for stage in ["Discovery", "Analysis", "Recommendations"]:
        models.change_crm_stage(conn, household_id, stage, note=f"Advanced to {stage}")
    household = models.get_household(conn, household_id)
    assert household["crm_stage"] == "Recommendations"
    history = models.get_crm_history(conn, household_id)  # most recent first
    assert [h["stage"] for h in history][:4] == ["Recommendations", "Analysis", "Discovery", "Prospect"]

    # 9. Every data-changing action above must have produced an audit event.
    events = get_events(conn, household_id=household_id, limit=200)
    event_entity_types = {e["entity_type"] for e in events}
    assert {
        "household",
        "person",
        "financial_item",
        "goal",
        "checklist_item",
        "meeting",
        "task",
    }.issubset(event_entity_types)
    assert any(e["event_type"] == "stage_change" for e in events)

    # 10. Exports: the Excel workbook and HTML plan summary both generate
    # and contain this household's data.
    workbook_bytes = exports.generate_workbook(conn, household_id)
    workbook_path = tmp_path / "workbook.xlsx"
    workbook_path.write_bytes(workbook_bytes)
    wb = load_workbook(workbook_path)
    assert wb.sheetnames == [
        "Household Summary",
        "Financial Snapshot",
        "Goals & Scenarios",
        "Checklists",
        "Meetings",
        "Tasks",
        "Audit History",
    ]
    household_sheet_text = " ".join(
        str(cell.value) for row in wb["Household Summary"].iter_rows() for cell in row if cell.value
    )
    assert "Test Household" in household_sheet_text
    assert exports.LABEL in household_sheet_text

    html_summary = exports.generate_plan_summary_html(conn, household_id)
    assert "Test Household" in html_summary
    assert "New car" in html_summary
    assert exports.LABEL.upper() in html_summary.upper()
    assert "licensed" in html_summary.lower()
