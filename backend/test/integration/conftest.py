"""Hermetic integration harness: the real Flask endpoints run against a
throwaway SQLite database injected in place of MySQL, so the suite needs no
running database server."""
import os
import sqlite3
import sys
from datetime import datetime

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import services
from app import app

# Python 3.12 deprecated sqlite3's built-in datetime conversion. This stores the same text that
# SQLite's CURRENT_TIMESTAMP produces, so time comparisons in SQL stay correct.
sqlite3.register_adapter(datetime, lambda value: value.isoformat(' '))

SCHEMA = """
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    bio TEXT DEFAULT '',
    profile_picture TEXT DEFAULT '',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_bot INTEGER NOT NULL DEFAULT 0,
    personality TEXT,
    is_admin INTEGER NOT NULL DEFAULT 0,
    banned_at TIMESTAMP
);

CREATE TABLE sessions (
    token TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    image_url TEXT DEFAULT '',
    author_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE followers (
    follower_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    following_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (follower_id, following_id)
);

CREATE TABLE comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    post_id INTEGER NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
    author_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    parent_id INTEGER REFERENCES comments(id) ON DELETE CASCADE,
    body TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE likes (
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    post_id INTEGER NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, post_id)
);

CREATE TABLE reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    post_id INTEGER NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
    reporter_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    reason TEXT NOT NULL,
    note TEXT,
    status TEXT NOT NULL DEFAULT 'open',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reviewed_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    reviewed_at TIMESTAMP,
    UNIQUE (post_id, reporter_id)
);

CREATE TABLE password_resets (
    token_hash TEXT PRIMARY KEY,
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
