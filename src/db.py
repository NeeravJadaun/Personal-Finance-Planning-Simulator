"""SQLite connection and schema management for the practice simulator.

All data in this database is synthetic and generated for educational
demonstration purposes. See README.md for details.
"""

from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "practice.db"

CRM_STAGES = [
    "Prospect",
    "Discovery",
    "Analysis",
    "Recommendations",
    "Implementation",
    "Ongoing Service",
]

CHECKLIST_CATEGORIES = ["Insurance", "Tax", "Estate", "Retirement", "Emergency"]
CHECKLIST_STATUSES = ["Not reviewed", "Needs follow-up", "Complete"]

SCHEMA = """
CREATE TABLE IF NOT EXISTS households (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    advisor TEXT NOT NULL,
    crm_stage TEXT NOT NULL DEFAULT 'Prospect',
    risk_tolerance TEXT NOT NULL DEFAULT 'Moderate',
    contact_preference TEXT NOT NULL DEFAULT 'Email',
    notes TEXT DEFAULT '',
    next_meeting_date TEXT,
    archived INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS people (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    household_id INTEGER NOT NULL REFERENCES households(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    relationship TEXT NOT NULL,
    date_of_birth TEXT,
    is_dependant INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS financial_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    household_id INTEGER NOT NULL REFERENCES households(id) ON DELETE CASCADE,
    category TEXT NOT NULL,       -- asset | liability | income | expense
    subcategory TEXT NOT NULL,
    description TEXT DEFAULT '',
    amount REAL NOT NULL,
    frequency TEXT NOT NULL DEFAULT 'monthly',  -- monthly | annual | one_time
    as_of_date TEXT NOT NULL DEFAULT (date('now'))
);

CREATE TABLE IF NOT EXISTS goals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    household_id INTEGER NOT NULL REFERENCES households(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    goal_type TEXT NOT NULL,      -- retirement | major_purchase | other
    target_amount REAL NOT NULL,
    target_date TEXT,
    current_savings REAL NOT NULL DEFAULT 0,
    monthly_contribution REAL NOT NULL DEFAULT 0,
    priority TEXT NOT NULL DEFAULT 'Medium'
);

CREATE TABLE IF NOT EXISTS scenario_assumptions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    goal_id INTEGER NOT NULL REFERENCES goals(id) ON DELETE CASCADE,
    scenario TEXT NOT NULL,       -- baseline | optimistic | conservative
    annual_return REAL NOT NULL,
    withdrawal_rate REAL,
    notes TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS checklist_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    household_id INTEGER NOT NULL REFERENCES households(id) ON DELETE CASCADE,
    category TEXT NOT NULL,
    item_name TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'Not reviewed',
    note TEXT DEFAULT '',
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS meetings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    household_id INTEGER NOT NULL REFERENCES households(id) ON DELETE CASCADE,
    meeting_date TEXT NOT NULL,
    agenda TEXT DEFAULT '',
    notes TEXT DEFAULT '',
    recommendations TEXT DEFAULT '',
    status TEXT NOT NULL DEFAULT 'Scheduled',  -- Scheduled | Completed | Cancelled
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    household_id INTEGER NOT NULL REFERENCES households(id) ON DELETE CASCADE,
    meeting_id INTEGER REFERENCES meetings(id) ON DELETE SET NULL,
    description TEXT NOT NULL,
    assigned_to TEXT NOT NULL DEFAULT 'Advisor',
    due_date TEXT,
    status TEXT NOT NULL DEFAULT 'Open',  -- Open | Complete
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    completed_at TEXT
);

CREATE TABLE IF NOT EXISTS crm_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    household_id INTEGER NOT NULL REFERENCES households(id) ON DELETE CASCADE,
    stage TEXT NOT NULL,
    changed_at TEXT NOT NULL DEFAULT (datetime('now')),
    actor TEXT NOT NULL DEFAULT 'Advisor',
    note TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS audit_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    household_id INTEGER REFERENCES households(id) ON DELETE CASCADE,
    event_type TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    entity_id INTEGER,
    description TEXT NOT NULL,
    actor TEXT NOT NULL DEFAULT 'Advisor',
    timestamp TEXT NOT NULL DEFAULT (datetime('now'))
);
"""


def _resolve_db_path(db_path: Path | str | None) -> Path:
    """PRACTICE_DB_PATH lets tests point the app at an isolated temp database
    without touching the real demo database on disk."""
    if db_path is not None:
        return Path(db_path)
    override = os.environ.get("PRACTICE_DB_PATH")
    return Path(override) if override else DEFAULT_DB_PATH


def get_connection(db_path: Path | str | None = None) -> sqlite3.Connection:
    """Open a SQLite connection with sane defaults for app use."""
    db_path = _resolve_db_path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    """Create all tables if they do not already exist."""
    conn.executescript(SCHEMA)
    conn.commit()


@contextmanager
def connect(db_path: Path | str | None = None):
    """Context manager yielding an initialized connection."""
    conn = get_connection(db_path)
    try:
        init_db(conn)
        yield conn
    finally:
        conn.close()


def reset_db(db_path: Path | str | None = None) -> None:
    """Delete and recreate the database file. Used for reseeding demo data."""
    db_path = _resolve_db_path(db_path)
    if db_path.exists():
        db_path.unlink()
    conn = get_connection(db_path)
    init_db(conn)
    conn.close()
