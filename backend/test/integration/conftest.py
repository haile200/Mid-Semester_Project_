"""Hermetic integration harness: the real Flask endpoints run against a
throwaway SQLite database injected in place of MySQL, so the suite needs no
running database server."""
import os
import sqlite3
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import services
from app import app

SCHEMA = """
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    bio TEXT DEFAULT '',
    profile_picture TEXT DEFAULT '',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE sessions (
    token TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""


class CursorAdapter:
    """Translates the MySQL placeholder style used by the app (%s) to SQLite (?)."""

    def __init__(self, cursor):
        self._cursor = cursor

    def execute(self, query, params=None):
        return self._cursor.execute(query.replace('%s', '?'), params or ())

    def __getattr__(self, name):
        return getattr(self._cursor, name)


class ConnectionAdapter:
    """Hands out adapted cursors; close() is a no-op so the shared in-memory
    connection survives the app's per-request open/close pattern."""

    def __init__(self, conn):
        self._conn = conn

    def cursor(self):
        return CursorAdapter(self._conn.cursor())

    def commit(self):
        self._conn.commit()

    def close(self):
        pass


@pytest.fixture
def db(monkeypatch):
    conn = sqlite3.connect(':memory:')
    conn.executescript(SCHEMA)
    monkeypatch.setattr(services, 'get_db', lambda: ConnectionAdapter(conn))
    yield conn
    conn.close()


@pytest.fixture
def client(db):
    app.testing = True
    with app.test_client() as client:
        yield client
