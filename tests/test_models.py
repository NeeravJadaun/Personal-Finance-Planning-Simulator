"""Tests for src/models.py: CRUD, CRM history, tasks, audit events, discovery."""

import pytest

from src import models
from src.audit import get_events


# ---------------------------------------------------------------------------
# Households
# ---------------------------------------------------------------------------


def test_create_household_seeds_checklist_and_audit_event(conn):
    hid = models.create_household(conn, name="Lopez Household", advisor="Priya Malhotra")
    household = models.get_household(conn, hid)
    assert household["name"] == "Lopez Household"
    assert household["crm_stage"] == "Prospect"

    checklist = models.list_checklist_items(conn, hid)
    assert len(checklist) > 0
    assert all(item["status"] == "Not reviewed" for item in checklist)

    events = get_events(conn, household_id=hid)
    assert any(e["event_type"] == "create" and e["entity_type"] == "household" for e in events)

    crm_history = models.get_crm_history(conn, hid)
    assert len(crm_history) == 1
    assert crm_history[0]["stage"] == "Prospect"


def test_create_household_rejects_blank_name(conn):
    with pytest.raises(ValueError):
        models.create_household(conn, name="   ", advisor="Advisor")


def test_create_household_rejects_invalid_crm_stage(conn):
    with pytest.raises(ValueError):
        models.create_household(conn, name="X", advisor="Advisor", crm_stage="Nonexistent")


def test_update_household_logs_audit_event(conn, household_id):
    models.update_household(conn, household_id, notes="Updated notes", actor="Advisor")
    household = models.get_household(conn, household_id)
    assert household["notes"] == "Updated notes"
    events = get_events(conn, household_id=household_id)
    assert any("Updated household fields" in e["description"] for e in events)


def test_update_household_rejects_unknown_field(conn, household_id):
    with pytest.raises(ValueError):
        models.update_household(conn, household_id, crm_stage="Discovery")


def test_archive_and_unarchive_household(conn, household_id):
    models.set_archived(conn, household_id, True)
    assert len(models.list_households(conn)) == 0
    assert len(models.list_households(conn, include_archived=True)) == 1

    models.set_archived(conn, household_id, False)
    assert len(models.list_households(conn)) == 1


# ---------------------------------------------------------------------------
# People
# ---------------------------------------------------------------------------


def test_add_and_list_people(conn, household_id):
    models.add_person(conn, household_id, name="Alex Doe", relationship="Self")
    models.add_person(conn, household_id, name="Jamie Doe", relationship="Child", is_dependant=True)
    people = models.list_people(conn, household_id)
    assert len(people) == 2
    assert any(p["is_dependant"] == 1 for p in people)


def test_add_person_rejects_blank_name(conn, household_id):
    with pytest.raises(ValueError):
        models.add_person(conn, household_id, name="", relationship="Self")


def test_delete_person_logs_audit_event(conn, household_id):
    pid = models.add_person(conn, household_id, name="Alex Doe", relationship="Self")
    models.delete_person(conn, pid)
    assert models.list_people(conn, household_id) == []
    events = get_events(conn, household_id=household_id)
    assert any(e["event_type"] == "delete" and e["entity_type"] == "person" for e in events)


# ---------------------------------------------------------------------------
# Financial items
# ---------------------------------------------------------------------------


def test_add_financial_item_rejects_invalid_category(conn, household_id):
    with pytest.raises(ValueError):
        models.add_financial_item(
            conn, household_id, category="not_a_category", subcategory="x", amount=100
        )


def test_add_financial_item_rejects_negative_amount(conn, household_id):
    with pytest.raises(ValueError):
        models.add_financial_item(
            conn, household_id, category="asset", subcategory="Cash", amount=-50
        )


def test_financial_summary_zero_income_savings_rate_is_none(conn, household_id):
    models.add_financial_item(
        conn, household_id, category="expense", subcategory="Rent", amount=1000, frequency="monthly"
    )
    summary = models.get_financial_summary(conn, household_id)
    assert summary["monthly_income"] == 0
    assert summary["savings_rate"] is None
    assert summary["monthly_surplus"] == -1000


def test_financial_summary_includes_debt_payments_in_outflow(conn, household_id):
    models.add_financial_item(
        conn, household_id, category="income", subcategory="Salary", amount=5000, frequency="monthly"
    )
    models.add_financial_item(
        conn, household_id, category="expense", subcategory="Food", amount=1000, frequency="monthly"
    )
    models.add_financial_item(
        conn,
        household_id,
        category="debt_payment",
        subcategory="Auto Loan Payment",
        amount=400,
        frequency="monthly",
    )
    summary = models.get_financial_summary(conn, household_id)
    assert summary["monthly_total_outflow"] == 1400
    assert summary["monthly_surplus"] == 3600
    assert summary["debt_to_income"] == pytest.approx(400 / 5000)


def test_annual_frequency_normalized_to_monthly(conn, household_id):
    models.add_financial_item(
        conn, household_id, category="income", subcategory="Bonus", amount=12000, frequency="annual"
    )
    summary = models.get_financial_summary(conn, household_id)
    assert summary["monthly_income"] == pytest.approx(1000)


def test_delete_financial_item(conn, household_id):
    item_id = models.add_financial_item(
        conn, household_id, category="asset", subcategory="Savings", amount=1000
    )
    models.delete_financial_item(conn, item_id)
    assert models.list_financial_items(conn, household_id) == []


# ---------------------------------------------------------------------------
# Goals
# ---------------------------------------------------------------------------


def test_add_goal_rejects_invalid_type(conn, household_id):
    with pytest.raises(ValueError):
        models.add_goal(
            conn, household_id, name="X", goal_type="invalid", target_amount=1000
        )


def test_add_goal_rejects_negative_amounts(conn, household_id):
    with pytest.raises(ValueError):
        models.add_goal(
            conn, household_id, name="X", goal_type="other", target_amount=-1
        )


def test_get_scenario_assumptions_defaults_without_override(conn, household_id):
    goal_id = models.add_goal(
        conn, household_id, name="Retirement", goal_type="retirement", target_amount=1_000_000
    )
    assumptions = models.get_scenario_assumptions(conn, goal_id)
    assert set(assumptions) == {"baseline", "optimistic", "conservative"}
    assert assumptions["baseline"]["annual_return"] == 0.06


def test_set_scenario_assumption_overrides_default(conn, household_id):
    goal_id = models.add_goal(
        conn, household_id, name="Retirement", goal_type="retirement", target_amount=1_000_000
    )
    models.set_scenario_assumption(conn, goal_id, "baseline", annual_return=0.07, withdrawal_rate=0.045)
    assumptions = models.get_scenario_assumptions(conn, goal_id)
    assert assumptions["baseline"]["annual_return"] == 0.07
    assert assumptions["optimistic"]["annual_return"] == 0.08  # untouched default


def test_delete_goal(conn, household_id):
    goal_id = models.add_goal(
        conn, household_id, name="Goal", goal_type="other", target_amount=1000
    )
    models.delete_goal(conn, goal_id)
    assert models.get_goal(conn, goal_id) is None


# ---------------------------------------------------------------------------
# Checklists
# ---------------------------------------------------------------------------


def test_checklist_seeded_on_create(conn, household_id):
    items = models.list_checklist_items(conn, household_id)
    categories = {item["category"] for item in items}
    assert categories == {"Insurance", "Tax", "Estate", "Retirement", "Emergency"}


def test_update_checklist_item_rejects_invalid_status(conn, household_id):
    items = models.list_checklist_items(conn, household_id)
    with pytest.raises(ValueError):
        models.update_checklist_item(conn, items[0]["id"], status="Bogus Status")


def test_update_checklist_item_logs_audit_event(conn, household_id):
    items = models.list_checklist_items(conn, household_id)
    models.update_checklist_item(conn, items[0]["id"], status="Complete", note="Reviewed with client")
    updated = [i for i in models.list_checklist_items(conn, household_id) if i["id"] == items[0]["id"]][0]
    assert updated["status"] == "Complete"
    assert updated["note"] == "Reviewed with client"
    events = get_events(conn, household_id=household_id)
    assert any(e["entity_type"] == "checklist_item" for e in events)


# ---------------------------------------------------------------------------
# Meetings and agenda generation
# ---------------------------------------------------------------------------


def test_create_meeting_updates_next_meeting_date(conn, household_id):
    models.create_meeting(conn, household_id, meeting_date="2030-01-15")
    household = models.get_household(conn, household_id)
    assert household["next_meeting_date"] == "2030-01-15"


def test_generate_agenda_flags_missing_discovery_fields(conn, household_id):
    agenda = models.generate_agenda(conn, household_id)
    assert "No household members recorded" in agenda
    assert "No asset information recorded" in agenda
    assert "No financial goals recorded" in agenda


def test_generate_agenda_lists_open_goals_with_gap(conn, household_id):
    models.add_goal(
        conn,
        household_id,
        name="House down payment",
        goal_type="major_purchase",
        target_amount=50000,
        current_savings=20000,
    )
    agenda = models.generate_agenda(conn, household_id)
    assert "House down payment" in agenda
    assert "30,000.00" in agenda  # 50000 - 20000 funding gap


def test_update_meeting_rejects_unknown_field(conn, household_id):
    meeting_id = models.create_meeting(conn, household_id, meeting_date="2030-01-01")
    with pytest.raises(ValueError):
        models.update_meeting(conn, meeting_id, household_id=999)


# ---------------------------------------------------------------------------
# Tasks
# ---------------------------------------------------------------------------


def test_create_task_rejects_blank_description(conn, household_id):
    with pytest.raises(ValueError):
        models.create_task(conn, household_id, description="   ")


def test_complete_and_reopen_task(conn, household_id):
    task_id = models.create_task(conn, household_id, description="Send documents")
    models.complete_task(conn, task_id)
    task = models.list_tasks(conn, household_id)[0]
    assert task["status"] == "Complete"
    assert task["completed_at"] is not None

    models.reopen_task(conn, task_id)
    task = models.list_tasks(conn, household_id)[0]
    assert task["status"] == "Open"
    assert task["completed_at"] is None

    events = get_events(conn, household_id=household_id)
    assert sum(1 for e in events if e["entity_type"] == "task") >= 3  # create, complete, reopen


def test_complete_task_raises_for_unknown_id(conn):
    with pytest.raises(ValueError):
        models.complete_task(conn, 99999)


def test_get_overdue_tasks(conn, household_id):
    models.create_task(conn, household_id, description="Overdue", due_date="2000-01-01")
    models.create_task(conn, household_id, description="Future", due_date="2999-01-01")
    overdue = models.get_overdue_tasks(conn)
    assert len(overdue) == 1
    assert overdue[0]["description"] == "Overdue"


# ---------------------------------------------------------------------------
# CRM pipeline
# ---------------------------------------------------------------------------


def test_change_crm_stage_records_history_and_audit(conn, household_id):
    models.change_crm_stage(conn, household_id, "Discovery", note="Kickoff call complete")
    household = models.get_household(conn, household_id)
    assert household["crm_stage"] == "Discovery"

    history = models.get_crm_history(conn, household_id)
    assert len(history) == 2  # initial Prospect + new Discovery
    assert history[0]["stage"] == "Discovery"  # most recent first

    events = get_events(conn, household_id=household_id)
    assert any(e["event_type"] == "stage_change" for e in events)


def test_change_crm_stage_rejects_invalid_stage(conn, household_id):
    with pytest.raises(ValueError):
        models.change_crm_stage(conn, household_id, "Not A Stage")


def test_change_crm_stage_rejects_unknown_household(conn):
    with pytest.raises(ValueError):
        models.change_crm_stage(conn, 99999, "Discovery")


def test_get_stalled_households_detects_inactive_pipeline(conn, household_id):
    import datetime

    models.change_crm_stage(conn, household_id, "Analysis")
    old_date = (datetime.datetime.now() - datetime.timedelta(days=60)).strftime("%Y-%m-%d %H:%M:%S")
    conn.execute(
        "UPDATE crm_history SET changed_at = ? WHERE household_id = ? AND stage = 'Analysis'",
        (old_date, household_id),
    )
    conn.commit()

    stalled = models.get_stalled_households(conn, days_threshold=30)
    assert len(stalled) == 1
    assert stalled[0]["household_id"] == household_id


def test_get_stalled_households_excludes_ongoing_service(conn, household_id):
    for stage in ["Discovery", "Analysis", "Recommendations", "Implementation", "Ongoing Service"]:
        models.change_crm_stage(conn, household_id, stage)
    import datetime

    old_date = (datetime.datetime.now() - datetime.timedelta(days=90)).strftime("%Y-%m-%d %H:%M:%S")
    conn.execute("UPDATE crm_history SET changed_at = ?", (old_date,))
    conn.commit()
    stalled = models.get_stalled_households(conn, days_threshold=30)
    assert stalled == []


# ---------------------------------------------------------------------------
# Dashboard metrics
# ---------------------------------------------------------------------------


def test_dashboard_metrics_counts_incomplete_profiles(conn, household_id):
    metrics = models.get_dashboard_metrics(conn)
    assert metrics["household_count"] == 1
    assert len(metrics["incomplete_profiles"]) == 1  # bare household has no people/financials/goals


def test_dashboard_metrics_upcoming_meetings_and_overdue_tasks(conn, household_id):
    import datetime

    soon = (datetime.date.today() + datetime.timedelta(days=5)).isoformat()
    models.create_meeting(conn, household_id, meeting_date=soon)
    models.create_task(conn, household_id, description="Late task", due_date="2000-01-01")

    metrics = models.get_dashboard_metrics(conn)
    assert len(metrics["upcoming_meetings"]) == 1
    assert len(metrics["overdue_tasks"]) == 1
