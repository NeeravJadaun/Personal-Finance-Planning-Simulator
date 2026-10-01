"""Data-access layer for the practice simulator.

Every function that changes data also writes an audit_events row so the
full history of a household can be reconstructed. All data manipulated here
is synthetic demo data (see README.md).
"""

from __future__ import annotations

import sqlite3
from datetime import date, datetime, timedelta

from src import calculations
from src.audit import log_event
from src.db import CHECKLIST_CATEGORIES, CRM_STAGES

#: Asset subcategories treated as "liquid" for emergency-fund coverage.
LIQUID_ASSET_SUBCATEGORIES = {
    "Cash & Checking",
    "Savings",
    "Emergency Fund",
    "Money Market",
}

#: Default educational checklist items seeded for every new household.
DEFAULT_CHECKLIST_ITEMS: dict[str, list[str]] = {
    "Insurance": [
        "Life insurance coverage reviewed",
        "Disability insurance coverage reviewed",
        "Health insurance coverage reviewed",
        "Property & liability (home/auto) coverage reviewed",
        "Umbrella liability policy considered",
    ],
    "Tax": [
        "Prior-year tax return reviewed",
        "Withholding / estimated payments reviewed",
        "Tax-advantaged account contributions reviewed",
        "Tax-loss harvesting opportunities discussed",
    ],
    "Estate": [
        "Will in place and current",
        "Powers of attorney (financial & healthcare) in place",
        "Beneficiary designations reviewed",
        "Trust strategy discussed (if applicable)",
    ],
    "Retirement": [
        "Employer retirement plan contribution reviewed",
        "IRA / Roth IRA contribution reviewed",
        "Social Security claiming strategy discussed",
        "Retirement account asset allocation reviewed",
    ],
    "Emergency": [
        "Emergency fund target defined",
        "Emergency fund funding progress reviewed",
        "Income-protection plan (job loss) discussed",
    ],
}


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ---------------------------------------------------------------------------
# Households
# ---------------------------------------------------------------------------


def create_household(
    conn: sqlite3.Connection,
    *,
    name: str,
    advisor: str,
    risk_tolerance: str = "Moderate",
    contact_preference: str = "Email",
    notes: str = "",
    crm_stage: str = "Prospect",
    actor: str = "Advisor",
) -> int:
    if not name or not name.strip():
        raise ValueError("Household name is required")
    if crm_stage not in CRM_STAGES:
        raise ValueError(f"Invalid CRM stage: {crm_stage}")

    cur = conn.execute(
        """
        INSERT INTO households (name, advisor, crm_stage, risk_tolerance, contact_preference, notes)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (name.strip(), advisor, crm_stage, risk_tolerance, contact_preference, notes),
    )
    household_id = cur.lastrowid

    conn.execute(
        "INSERT INTO crm_history (household_id, stage, actor, note) VALUES (?, ?, ?, ?)",
        (household_id, crm_stage, actor, "Household created"),
    )
    log_event(
        conn,
        household_id=household_id,
        event_type="create",
        entity_type="household",
        entity_id=household_id,
        description=f"Created household '{name.strip()}'",
        actor=actor,
    )
    seed_checklist_for_household(conn, household_id)
    conn.commit()
    return household_id


def get_household(conn: sqlite3.Connection, household_id: int) -> sqlite3.Row | None:
    return conn.execute("SELECT * FROM households WHERE id = ?", (household_id,)).fetchone()


def list_households(
    conn: sqlite3.Connection,
    *,
    include_archived: bool = False,
    advisor: str | None = None,
    stage: str | None = None,
) -> list[sqlite3.Row]:
    query = "SELECT * FROM households WHERE 1=1"
    params: list = []
    if not include_archived:
        query += " AND archived = 0"
    if advisor:
        query += " AND advisor = ?"
        params.append(advisor)
    if stage:
        query += " AND crm_stage = ?"
        params.append(stage)
    query += " ORDER BY name"
    return conn.execute(query, params).fetchall()


def update_household(
    conn: sqlite3.Connection,
    household_id: int,
    *,
    actor: str = "Advisor",
    **fields,
) -> None:
    """Update arbitrary household columns and log a single audit event."""
    if not fields:
        return
    allowed = {
        "name",
        "advisor",
        "risk_tolerance",
        "contact_preference",
        "notes",
        "next_meeting_date",
    }
    unknown = set(fields) - allowed
    if unknown:
        raise ValueError(f"Cannot update unknown fields: {unknown}")

    set_clause = ", ".join(f"{col} = ?" for col in fields)
    conn.execute(
        f"UPDATE households SET {set_clause} WHERE id = ?",
        (*fields.values(), household_id),
    )
    changed = ", ".join(fields.keys())
    log_event(
        conn,
        household_id=household_id,
        event_type="update",
        entity_type="household",
        entity_id=household_id,
        description=f"Updated household fields: {changed}",
        actor=actor,
    )
    conn.commit()


def set_archived(
    conn: sqlite3.Connection, household_id: int, archived: bool, actor: str = "Advisor"
) -> None:
    conn.execute(
        "UPDATE households SET archived = ? WHERE id = ?", (int(archived), household_id)
    )
    log_event(
        conn,
        household_id=household_id,
        event_type="archive" if archived else "unarchive",
        entity_type="household",
        entity_id=household_id,
        description="Household archived" if archived else "Household unarchived",
        actor=actor,
    )
    conn.commit()


# ---------------------------------------------------------------------------
# People
# ---------------------------------------------------------------------------


def add_person(
    conn: sqlite3.Connection,
    household_id: int,
    *,
    name: str,
    relationship: str,
    date_of_birth: str | None = None,
    is_dependant: bool = False,
    actor: str = "Advisor",
) -> int:
    if not name or not name.strip():
        raise ValueError("Person name is required")
    cur = conn.execute(
        """
        INSERT INTO people (household_id, name, relationship, date_of_birth, is_dependant)
        VALUES (?, ?, ?, ?, ?)
        """,
        (household_id, name.strip(), relationship, date_of_birth, int(is_dependant)),
    )
    person_id = cur.lastrowid
    log_event(
        conn,
        household_id=household_id,
        event_type="create",
        entity_type="person",
        entity_id=person_id,
        description=f"Added household member '{name.strip()}' ({relationship})",
        actor=actor,
    )
    conn.commit()
    return person_id


def list_people(conn: sqlite3.Connection, household_id: int) -> list[sqlite3.Row]:
    return conn.execute(
        "SELECT * FROM people WHERE household_id = ? ORDER BY id", (household_id,)
    ).fetchall()


def delete_person(conn: sqlite3.Connection, person_id: int, actor: str = "Advisor") -> None:
    row = conn.execute("SELECT * FROM people WHERE id = ?", (person_id,)).fetchone()
    if row is None:
        return
    conn.execute("DELETE FROM people WHERE id = ?", (person_id,))
    log_event(
        conn,
        household_id=row["household_id"],
        event_type="delete",
        entity_type="person",
        entity_id=person_id,
        description=f"Removed household member '{row['name']}'",
        actor=actor,
    )
    conn.commit()


# ---------------------------------------------------------------------------
# Financial items
# ---------------------------------------------------------------------------

FINANCIAL_CATEGORIES = ["asset", "liability", "income", "expense", "debt_payment"]


def add_financial_item(
    conn: sqlite3.Connection,
    household_id: int,
    *,
    category: str,
    subcategory: str,
    amount: float,
    description: str = "",
    frequency: str = "monthly",
    as_of_date: str | None = None,
    actor: str = "Advisor",
) -> int:
    if category not in FINANCIAL_CATEGORIES:
        raise ValueError(f"Invalid category: {category}")
    if amount < 0:
        raise ValueError("amount must be non-negative")
    as_of_date = as_of_date or date.today().isoformat()
    cur = conn.execute(
        """
        INSERT INTO financial_items (household_id, category, subcategory, description, amount, frequency, as_of_date)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (household_id, category, subcategory, description, amount, frequency, as_of_date),
    )
    item_id = cur.lastrowid
    log_event(
        conn,
        household_id=household_id,
        event_type="create",
        entity_type="financial_item",
        entity_id=item_id,
        description=f"Added {category} '{subcategory}': {amount:,.2f} ({frequency})",
        actor=actor,
    )
    conn.commit()
    return item_id


def list_financial_items(
    conn: sqlite3.Connection, household_id: int, category: str | None = None
) -> list[sqlite3.Row]:
    if category:
        return conn.execute(
            "SELECT * FROM financial_items WHERE household_id = ? AND category = ? ORDER BY id",
            (household_id, category),
        ).fetchall()
    return conn.execute(
        "SELECT * FROM financial_items WHERE household_id = ? ORDER BY category, id",
        (household_id,),
    ).fetchall()


def delete_financial_item(conn: sqlite3.Connection, item_id: int, actor: str = "Advisor") -> None:
    row = conn.execute("SELECT * FROM financial_items WHERE id = ?", (item_id,)).fetchone()
    if row is None:
        return
    conn.execute("DELETE FROM financial_items WHERE id = ?", (item_id,))
    log_event(
        conn,
        household_id=row["household_id"],
        event_type="delete",
        entity_type="financial_item",
        entity_id=item_id,
        description=f"Removed {row['category']} '{row['subcategory']}'",
        actor=actor,
    )
    conn.commit()


def _normalize_monthly(amount: float, frequency: str) -> float:
    if frequency == "monthly":
        return amount
    if frequency == "annual":
        return amount / 12
    return 0.0  # one_time items do not contribute to recurring monthly totals


def get_financial_summary(conn: sqlite3.Connection, household_id: int) -> dict:
    """Aggregate financial_items into the figures shown on the Financial Snapshot page."""
    items = list_financial_items(conn, household_id)

    total_assets = sum(i["amount"] for i in items if i["category"] == "asset")
    total_liabilities = sum(i["amount"] for i in items if i["category"] == "liability")
    liquid_assets = sum(
        i["amount"]
        for i in items
        if i["category"] == "asset" and i["subcategory"] in LIQUID_ASSET_SUBCATEGORIES
    )
    monthly_income = sum(
        _normalize_monthly(i["amount"], i["frequency"]) for i in items if i["category"] == "income"
    )
    monthly_expenses = sum(
        _normalize_monthly(i["amount"], i["frequency"])
        for i in items
        if i["category"] == "expense"
    )
    monthly_debt_payments = sum(
        _normalize_monthly(i["amount"], i["frequency"])
        for i in items
        if i["category"] == "debt_payment"
    )

    # Total monthly cash outflow includes both living expenses and debt
    # service (loan/mortgage payments) -- a dollar going to a loan payment
    # is just as unavailable for saving as a dollar spent on groceries.
    # debt_to_income is a separate ratio computed from the same debt
    # payment figure.
    monthly_total_outflow = monthly_expenses + monthly_debt_payments
    surplus = calculations.monthly_cash_flow(monthly_income, monthly_total_outflow)

    return {
        "total_assets": total_assets,
        "total_liabilities": total_liabilities,
        "net_worth": calculations.net_worth(total_assets, total_liabilities),
        "liquid_assets": liquid_assets,
        "monthly_income": monthly_income,
        "monthly_expenses": monthly_expenses,
        "monthly_debt_payments": monthly_debt_payments,
        "monthly_total_outflow": monthly_total_outflow,
        "monthly_surplus": surplus,
        "savings_rate": calculations.savings_rate(surplus, monthly_income),
        "debt_to_income": calculations.debt_to_income(monthly_debt_payments, monthly_income),
        "emergency_fund_months": calculations.emergency_fund_months(
            liquid_assets, monthly_expenses
        ),
    }


# ---------------------------------------------------------------------------
# Goals
# ---------------------------------------------------------------------------

GOAL_TYPES = ["retirement", "major_purchase", "other"]


def add_goal(
    conn: sqlite3.Connection,
    household_id: int,
    *,
    name: str,
    goal_type: str,
    target_amount: float,
    target_date: str | None = None,
    current_savings: float = 0.0,
    monthly_contribution: float = 0.0,
    priority: str = "Medium",
    actor: str = "Advisor",
) -> int:
    if goal_type not in GOAL_TYPES:
        raise ValueError(f"Invalid goal_type: {goal_type}")
    if target_amount < 0 or current_savings < 0 or monthly_contribution < 0:
        raise ValueError("Goal amounts must be non-negative")
    cur = conn.execute(
        """
        INSERT INTO goals (household_id, name, goal_type, target_amount, target_date, current_savings, monthly_contribution, priority)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            household_id,
            name,
            goal_type,
            target_amount,
            target_date,
            current_savings,
            monthly_contribution,
            priority,
        ),
    )
    goal_id = cur.lastrowid
    log_event(
        conn,
        household_id=household_id,
        event_type="create",
        entity_type="goal",
        entity_id=goal_id,
        description=f"Added goal '{name}' (target {target_amount:,.2f})",
        actor=actor,
    )
    conn.commit()
    return goal_id


def list_goals(
    conn: sqlite3.Connection, household_id: int, goal_type: str | None = None
) -> list[sqlite3.Row]:
    if goal_type:
        return conn.execute(
            "SELECT * FROM goals WHERE household_id = ? AND goal_type = ? ORDER BY id",
            (household_id, goal_type),
        ).fetchall()
    return conn.execute(
        "SELECT * FROM goals WHERE household_id = ? ORDER BY id", (household_id,)
    ).fetchall()


def get_goal(conn: sqlite3.Connection, goal_id: int) -> sqlite3.Row | None:
    return conn.execute("SELECT * FROM goals WHERE id = ?", (goal_id,)).fetchone()


def delete_goal(conn: sqlite3.Connection, goal_id: int, actor: str = "Advisor") -> None:
    row = get_goal(conn, goal_id)
    if row is None:
        return
    conn.execute("DELETE FROM goals WHERE id = ?", (goal_id,))
    log_event(
        conn,
        household_id=row["household_id"],
        event_type="delete",
        entity_type="goal",
        entity_id=goal_id,
        description=f"Removed goal '{row['name']}'",
        actor=actor,
    )
    conn.commit()


# ---------------------------------------------------------------------------
# Scenario assumptions
# ---------------------------------------------------------------------------


def set_scenario_assumption(
    conn: sqlite3.Connection,
    goal_id: int,
    scenario: str,
    *,
    annual_return: float,
    withdrawal_rate: float | None = None,
    notes: str = "",
    actor: str = "Advisor",
) -> None:
    existing = conn.execute(
        "SELECT id FROM scenario_assumptions WHERE goal_id = ? AND scenario = ?",
        (goal_id, scenario),
    ).fetchone()
    if existing:
        conn.execute(
            "UPDATE scenario_assumptions SET annual_return = ?, withdrawal_rate = ?, notes = ? WHERE id = ?",
            (annual_return, withdrawal_rate, notes, existing["id"]),
        )
    else:
        conn.execute(
            """
            INSERT INTO scenario_assumptions (goal_id, scenario, annual_return, withdrawal_rate, notes)
            VALUES (?, ?, ?, ?, ?)
            """,
            (goal_id, scenario, annual_return, withdrawal_rate, notes),
        )
    goal = get_goal(conn, goal_id)
    log_event(
        conn,
        household_id=goal["household_id"] if goal else None,
        event_type="update",
        entity_type="scenario_assumption",
        entity_id=goal_id,
        description=f"Set {scenario} assumption for goal {goal_id}: return={annual_return}",
        actor=actor,
    )
    conn.commit()


def get_scenario_assumptions(conn: sqlite3.Connection, goal_id: int) -> dict[str, dict]:
    """Return custom assumptions merged over the calculations.DEFAULT_SCENARIOS."""
    result = {
        name: {"annual_return": a.annual_return, "withdrawal_rate": a.withdrawal_rate, "notes": ""}
        for name, a in calculations.DEFAULT_SCENARIOS.items()
    }
    rows = conn.execute(
        "SELECT * FROM scenario_assumptions WHERE goal_id = ?", (goal_id,)
    ).fetchall()
    for row in rows:
        result[row["scenario"]] = {
            "annual_return": row["annual_return"],
            "withdrawal_rate": row["withdrawal_rate"],
            "notes": row["notes"],
        }
    return result


# ---------------------------------------------------------------------------
# Checklists
# ---------------------------------------------------------------------------


def seed_checklist_for_household(conn: sqlite3.Connection, household_id: int) -> None:
    """Insert default checklist items for a new household (idempotent)."""
    existing = conn.execute(
        "SELECT COUNT(*) AS n FROM checklist_items WHERE household_id = ?", (household_id,)
    ).fetchone()["n"]
    if existing > 0:
        return
    for category in CHECKLIST_CATEGORIES:
        for item_name in DEFAULT_CHECKLIST_ITEMS.get(category, []):
            conn.execute(
                """
                INSERT INTO checklist_items (household_id, category, item_name, status)
                VALUES (?, ?, ?, 'Not reviewed')
                """,
                (household_id, category, item_name),
            )


def list_checklist_items(
    conn: sqlite3.Connection, household_id: int, category: str | None = None
) -> list[sqlite3.Row]:
    if category:
        return conn.execute(
            "SELECT * FROM checklist_items WHERE household_id = ? AND category = ? ORDER BY id",
            (household_id, category),
        ).fetchall()
    return conn.execute(
        "SELECT * FROM checklist_items WHERE household_id = ? ORDER BY category, id",
        (household_id,),
    ).fetchall()


def update_checklist_item(
    conn: sqlite3.Connection,
    item_id: int,
    *,
    status: str,
    note: str = "",
    actor: str = "Advisor",
) -> None:
    from src.db import CHECKLIST_STATUSES

    if status not in CHECKLIST_STATUSES:
        raise ValueError(f"Invalid checklist status: {status}")
    row = conn.execute("SELECT * FROM checklist_items WHERE id = ?", (item_id,)).fetchone()
    if row is None:
        raise ValueError(f"No checklist item with id {item_id}")
    conn.execute(
        "UPDATE checklist_items SET status = ?, note = ?, updated_at = ? WHERE id = ?",
        (status, note, _now(), item_id),
    )
    log_event(
        conn,
        household_id=row["household_id"],
        event_type="update",
        entity_type="checklist_item",
        entity_id=item_id,
        description=f"Checklist '{row['item_name']}' set to {status}",
        actor=actor,
    )
    conn.commit()


# ---------------------------------------------------------------------------
# Meetings
# ---------------------------------------------------------------------------


def create_meeting(
    conn: sqlite3.Connection,
    household_id: int,
    *,
    meeting_date: str,
    agenda: str = "",
    actor: str = "Advisor",
) -> int:
    cur = conn.execute(
        "INSERT INTO meetings (household_id, meeting_date, agenda) VALUES (?, ?, ?)",
        (household_id, meeting_date, agenda),
    )
    meeting_id = cur.lastrowid
    conn.execute(
        "UPDATE households SET next_meeting_date = ? WHERE id = ? AND (next_meeting_date IS NULL OR next_meeting_date > ?)",
        (meeting_date, household_id, meeting_date),
    )
    log_event(
        conn,
        household_id=household_id,
        event_type="create",
        entity_type="meeting",
        entity_id=meeting_id,
        description=f"Scheduled meeting for {meeting_date}",
        actor=actor,
    )
    conn.commit()
    return meeting_id


def list_meetings(
    conn: sqlite3.Connection, household_id: int | None = None
) -> list[sqlite3.Row]:
    if household_id is not None:
        return conn.execute(
            "SELECT * FROM meetings WHERE household_id = ? ORDER BY meeting_date DESC",
            (household_id,),
        ).fetchall()
    return conn.execute("SELECT * FROM meetings ORDER BY meeting_date DESC").fetchall()


def get_meeting(conn: sqlite3.Connection, meeting_id: int) -> sqlite3.Row | None:
    return conn.execute("SELECT * FROM meetings WHERE id = ?", (meeting_id,)).fetchone()


def update_meeting(
    conn: sqlite3.Connection,
    meeting_id: int,
    *,
    actor: str = "Advisor",
    **fields,
) -> None:
    if not fields:
        return
    allowed = {"agenda", "notes", "recommendations", "status", "meeting_date"}
    unknown = set(fields) - allowed
    if unknown:
        raise ValueError(f"Cannot update unknown meeting fields: {unknown}")
    row = get_meeting(conn, meeting_id)
    if row is None:
        raise ValueError(f"No meeting with id {meeting_id}")
    set_clause = ", ".join(f"{col} = ?" for col in fields)
    conn.execute(
        f"UPDATE meetings SET {set_clause} WHERE id = ?", (*fields.values(), meeting_id)
    )
    log_event(
        conn,
        household_id=row["household_id"],
        event_type="update",
        entity_type="meeting",
        entity_id=meeting_id,
        description=f"Updated meeting fields: {', '.join(fields.keys())}",
        actor=actor,
    )
    conn.commit()


def discovery_completeness(conn: sqlite3.Connection, household_id: int) -> list[str]:
    """Return a list of missing-information prompts for a household's discovery profile."""
    missing = []
    people = list_people(conn, household_id)
    if not people:
        missing.append("No household members recorded")

    items = list_financial_items(conn, household_id)
    categories_present = {i["category"] for i in items}
    for required in ["asset", "liability", "income", "expense"]:
        if required not in categories_present:
            missing.append(f"No {required} information recorded")

    household = get_household(conn, household_id)
    if household and not household["risk_tolerance"]:
        missing.append("Risk tolerance not set")

    goals = list_goals(conn, household_id)
    if not goals:
        missing.append("No financial goals recorded")

    return missing


def generate_agenda(conn: sqlite3.Connection, household_id: int) -> str:
    """Build a meeting agenda from missing discovery fields and open goals."""
    lines = ["Synthetic educational example", "", "Meeting Agenda", "=" * 14, ""]

    missing = discovery_completeness(conn, household_id)
    if missing:
        lines.append("Discovery follow-ups needed:")
        lines.extend(f"  - {m}" for m in missing)
        lines.append("")

    goals = list_goals(conn, household_id)
    if goals:
        lines.append("Open goals to discuss:")
        for g in goals:
            gap = calculations.goal_funding_gap(g["target_amount"], g["current_savings"])
            lines.append(
                f"  - {g['name']} ({g['goal_type']}): target {g['target_amount']:,.2f}, "
                f"gap {gap:,.2f}"
            )
        lines.append("")

    checklist = list_checklist_items(conn, household_id)
    needs_followup = [c for c in checklist if c["status"] == "Needs follow-up"]
    if needs_followup:
        lines.append("Checklist items needing follow-up:")
        lines.extend(f"  - [{c['category']}] {c['item_name']}" for c in needs_followup)
        lines.append("")

    open_tasks = [t for t in list_tasks(conn, household_id=household_id) if t["status"] == "Open"]
    if open_tasks:
        lines.append("Open tasks from prior meetings:")
        lines.extend(f"  - {t['description']} (due {t['due_date'] or 'unscheduled'})" for t in open_tasks)
        lines.append("")

    if not missing and not goals and not needs_followup and not open_tasks:
        lines.append("Discovery profile complete -- no outstanding items.")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Tasks
# ---------------------------------------------------------------------------


def create_task(
    conn: sqlite3.Connection,
    household_id: int,
    *,
    description: str,
    assigned_to: str = "Advisor",
    due_date: str | None = None,
    meeting_id: int | None = None,
    actor: str = "Advisor",
) -> int:
    if not description or not description.strip():
        raise ValueError("Task description is required")
    cur = conn.execute(
        """
        INSERT INTO tasks (household_id, meeting_id, description, assigned_to, due_date)
        VALUES (?, ?, ?, ?, ?)
        """,
        (household_id, meeting_id, description.strip(), assigned_to, due_date),
    )
    task_id = cur.lastrowid
    log_event(
        conn,
        household_id=household_id,
        event_type="create",
        entity_type="task",
        entity_id=task_id,
        description=f"Created task '{description.strip()}' assigned to {assigned_to}",
        actor=actor,
    )
    conn.commit()
    return task_id


def list_tasks(
    conn: sqlite3.Connection,
    household_id: int | None = None,
    status: str | None = None,
) -> list[sqlite3.Row]:
    query = "SELECT * FROM tasks WHERE 1=1"
    params: list = []
    if household_id is not None:
        query += " AND household_id = ?"
        params.append(household_id)
    if status is not None:
        query += " AND status = ?"
        params.append(status)
    query += " ORDER BY due_date IS NULL, due_date"
    return conn.execute(query, params).fetchall()


def get_overdue_tasks(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    today = date.today().isoformat()
    return conn.execute(
        "SELECT * FROM tasks WHERE status = 'Open' AND due_date IS NOT NULL AND due_date < ? ORDER BY due_date",
        (today,),
    ).fetchall()


def complete_task(conn: sqlite3.Connection, task_id: int, actor: str = "Advisor") -> None:
    row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    if row is None:
        raise ValueError(f"No task with id {task_id}")
    conn.execute(
        "UPDATE tasks SET status = 'Complete', completed_at = ? WHERE id = ?",
        (_now(), task_id),
    )
    log_event(
        conn,
        household_id=row["household_id"],
        event_type="update",
        entity_type="task",
        entity_id=task_id,
        description=f"Completed task '{row['description']}'",
        actor=actor,
    )
    conn.commit()


def reopen_task(conn: sqlite3.Connection, task_id: int, actor: str = "Advisor") -> None:
    row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    if row is None:
        raise ValueError(f"No task with id {task_id}")
    conn.execute(
        "UPDATE tasks SET status = 'Open', completed_at = NULL WHERE id = ?", (task_id,)
    )
    log_event(
        conn,
        household_id=row["household_id"],
        event_type="update",
        entity_type="task",
        entity_id=task_id,
        description=f"Reopened task '{row['description']}'",
        actor=actor,
    )
    conn.commit()


# ---------------------------------------------------------------------------
# CRM pipeline
# ---------------------------------------------------------------------------


def change_crm_stage(
    conn: sqlite3.Connection,
    household_id: int,
    new_stage: str,
    *,
    actor: str = "Advisor",
    note: str = "",
) -> None:
    if new_stage not in CRM_STAGES:
        raise ValueError(f"Invalid CRM stage: {new_stage}")
    household = get_household(conn, household_id)
    if household is None:
        raise ValueError(f"No household with id {household_id}")

    conn.execute("UPDATE households SET crm_stage = ? WHERE id = ?", (new_stage, household_id))
    conn.execute(
        "INSERT INTO crm_history (household_id, stage, actor, note) VALUES (?, ?, ?, ?)",
        (household_id, new_stage, actor, note),
    )
    log_event(
        conn,
        household_id=household_id,
        event_type="stage_change",
        entity_type="household",
        entity_id=household_id,
        description=f"CRM stage changed from {household['crm_stage']} to {new_stage}"
        + (f" ({note})" if note else ""),
        actor=actor,
    )
    conn.commit()


def get_crm_history(conn: sqlite3.Connection, household_id: int) -> list[sqlite3.Row]:
    # Ordered by id (true insertion order), not changed_at: timestamps only
    # have second precision and may be backdated for demo/stalled-pipeline
    # data, so they cannot be trusted to break ties or sort reliably.
    return conn.execute(
        "SELECT * FROM crm_history WHERE household_id = ? ORDER BY id DESC",
        (household_id,),
    ).fetchall()


def get_stalled_households(
    conn: sqlite3.Connection, days_threshold: int = 30
) -> list[dict]:
    """Households (not archived, not Ongoing Service) whose current CRM stage
    has not changed in more than `days_threshold` days."""
    cutoff = (datetime.now() - timedelta(days=days_threshold)).strftime("%Y-%m-%d %H:%M:%S")
    households = list_households(conn, include_archived=False)
    stalled = []
    for h in households:
        if h["crm_stage"] == "Ongoing Service":
            continue
        # The most recent transition by insertion order reflects when the
        # household entered its current stage, even if changed_at was
        # backdated for demo data.
        last_change = conn.execute(
            "SELECT changed_at FROM crm_history WHERE household_id = ? ORDER BY id DESC LIMIT 1",
            (h["id"],),
        ).fetchone()
        last_change = last_change["changed_at"] if last_change else None
        if last_change is None or last_change < cutoff:
            stalled.append(
                {
                    "household_id": h["id"],
                    "name": h["name"],
                    "crm_stage": h["crm_stage"],
                    "stage_since": last_change,
                }
            )
    return stalled


# ---------------------------------------------------------------------------
# Dashboard aggregates
# ---------------------------------------------------------------------------


def get_dashboard_metrics(conn: sqlite3.Connection) -> dict:
    households = list_households(conn, include_archived=False)
    today = date.today().isoformat()
    horizon = (date.today() + timedelta(days=14)).isoformat()

    upcoming_meetings = conn.execute(
        "SELECT m.*, h.name AS household_name FROM meetings m "
        "JOIN households h ON h.id = m.household_id "
        "WHERE m.status = 'Scheduled' AND m.meeting_date BETWEEN ? AND ? "
        "ORDER BY m.meeting_date",
        (today, horizon),
    ).fetchall()

    overdue_tasks = get_overdue_tasks(conn)

    incomplete_profiles = [h for h in households if discovery_completeness(conn, h["id"])]

    stage_counts: dict[str, int] = {stage: 0 for stage in CRM_STAGES}
    for h in households:
        stage_counts[h["crm_stage"]] = stage_counts.get(h["crm_stage"], 0) + 1

    return {
        "household_count": len(households),
        "upcoming_meetings": upcoming_meetings,
        "overdue_tasks": overdue_tasks,
        "incomplete_profiles": incomplete_profiles,
        "stage_counts": stage_counts,
    }
