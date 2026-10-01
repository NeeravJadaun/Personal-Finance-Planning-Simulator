"""Audit-event logging. Every data-changing action should call `log_event`."""

from __future__ import annotations

import sqlite3


def log_event(
    conn: sqlite3.Connection,
    *,
    household_id: int | None,
    event_type: str,
    entity_type: str,
    entity_id: int | None,
    description: str,
    actor: str = "Advisor",
) -> int:
    """Insert an audit_events row and return its id. Caller commits."""
    cur = conn.execute(
        """
        INSERT INTO audit_events (household_id, event_type, entity_type, entity_id, description, actor)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (household_id, event_type, entity_type, entity_id, description, actor),
    )
    return cur.lastrowid


def get_events(
    conn: sqlite3.Connection, household_id: int | None = None, limit: int = 200
) -> list[sqlite3.Row]:
    if household_id is not None:
        rows = conn.execute(
            "SELECT * FROM audit_events WHERE household_id = ? ORDER BY timestamp DESC LIMIT ?",
            (household_id, limit),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM audit_events ORDER BY timestamp DESC LIMIT ?", (limit,)
        ).fetchall()
    return rows
