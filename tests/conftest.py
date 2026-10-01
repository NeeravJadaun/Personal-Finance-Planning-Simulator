"""Shared pytest fixtures: isolated in-memory-ish SQLite DB per test."""

import sqlite3

import pytest

from src import db


@pytest.fixture
def conn(tmp_path):
    """A fresh, schema-initialized SQLite connection backed by a temp file."""
    db_path = tmp_path / "test.db"
    connection = sqlite3.connect(str(db_path))
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    db.init_db(connection)
    yield connection
    connection.close()


@pytest.fixture
def household_id(conn):
    """A single bare household with no seed data, for isolated unit tests."""
    from src import models

    return models.create_household(conn, name="Test Household", advisor="Test Advisor")
