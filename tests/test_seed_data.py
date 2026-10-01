"""Tests for seed data: reproducibility and coverage of required household types."""

import sqlite3

from src import db, models, seed_data


def _fresh_conn(path) -> sqlite3.Connection:
    connection = sqlite3.connect(str(path))
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    db.init_db(connection)
    return connection


def test_seed_all_creates_at_least_twelve_households(conn):
    ids = seed_data.seed_all(conn)
    assert len(ids) >= 12
    households = models.list_households(conn, include_archived=True)
    assert len(households) >= 12


def test_seed_all_rejects_non_empty_database(conn):
    seed_data.seed_all(conn)
    import pytest

    with pytest.raises(RuntimeError):
        seed_data.seed_all(conn)


def test_seed_all_covers_required_household_archetypes(conn):
    seed_data.seed_all(conn)
    households = models.list_households(conn, include_archived=True)
    names = {h["name"] for h in households}

    # At least one business owner household (holds a "Business Ownership
    # Interest" asset line).
    business_owner_found = any(
        any(
            item["subcategory"] == "Business Ownership Interest"
            for item in models.list_financial_items(conn, h["id"])
        )
        for h in households
    )
    assert business_owner_found

    # At least one household with children (a dependant person).
    family_with_children_found = any(
        any(p["is_dependant"] for p in models.list_people(conn, h["id"])) for h in households
    )
    assert family_with_children_found

    # At least one household approaching retirement (a retirement goal with
    # a short time horizon).
    import datetime

    near_retirement_found = False
    for h in households:
        for g in models.list_goals(conn, h["id"], goal_type="retirement"):
            if g["target_date"]:
                target = datetime.date.fromisoformat(g["target_date"])
                if (target - datetime.date.today()).days < 365 * 10:
                    near_retirement_found = True
    assert near_retirement_found

    assert len(names) == len(households)  # all household names unique


def test_seed_reproducibility_same_business_data_each_run(tmp_path):
    """Seeding twice (on two fresh databases) should produce identical
    business-meaningful data -- household names, financial amounts, goal
    targets, and row counts per table. Wall-clock timestamp columns
    (created_at, audit timestamps) are intentionally excluded since they
    are allowed to differ by a second between runs."""

    conn_a = _fresh_conn(tmp_path / "a.db")
    conn_b = _fresh_conn(tmp_path / "b.db")
    seed_data.seed_all(conn_a)
    seed_data.seed_all(conn_b)

    households_a = models.list_households(conn_a, include_archived=True)
    households_b = models.list_households(conn_b, include_archived=True)
    assert len(households_a) == len(households_b)

    for ha, hb in zip(households_a, households_b):
        assert ha["name"] == hb["name"]
        assert ha["advisor"] == hb["advisor"]
        assert ha["crm_stage"] == hb["crm_stage"]
        assert ha["risk_tolerance"] == hb["risk_tolerance"]

        items_a = models.list_financial_items(conn_a, ha["id"])
        items_b = models.list_financial_items(conn_b, hb["id"])
        assert len(items_a) == len(items_b)
        assert [i["amount"] for i in items_a] == [i["amount"] for i in items_b]
        assert [i["subcategory"] for i in items_a] == [i["subcategory"] for i in items_b]

        goals_a = models.list_goals(conn_a, ha["id"])
        goals_b = models.list_goals(conn_b, hb["id"])
        assert [g["target_amount"] for g in goals_a] == [g["target_amount"] for g in goals_b]

        summary_a = models.get_financial_summary(conn_a, ha["id"])
        summary_b = models.get_financial_summary(conn_b, hb["id"])
        assert summary_a["net_worth"] == summary_b["net_worth"]
        assert summary_a["savings_rate"] == summary_b["savings_rate"]

    conn_a.close()
    conn_b.close()


def test_seed_financial_summaries_do_not_error_for_any_household(conn):
    seed_data.seed_all(conn)
    households = models.list_households(conn, include_archived=True)
    for h in households:
        summary = models.get_financial_summary(conn, h["id"])
        assert summary["net_worth"] >= 0 or summary["net_worth"] < 0  # just must not raise
        assert summary["total_assets"] >= 0
