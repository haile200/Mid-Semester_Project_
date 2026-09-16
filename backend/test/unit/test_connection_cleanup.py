import os
import sys
from unittest.mock import patch

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
import db
import services
from app import app
from mock_db import DummyCursor, DummyConnection


class ExplodingCursor(DummyCursor):
    def __init__(self):
        super().__init__()
        self.closed = False

    def execute(self, query, params=None):
        raise RuntimeError('query failed')

    def close(self):
        self.closed = True


class TrackingConnection(DummyConnection):
    def __init__(self, cursor):
        super().__init__(cursor)
        self.closed = False

    def close(self):
        self.closed = True


@patch('db.mysql.connector.connect')
def test_get_db_sets_a_connection_timeout(mock_connect):
    # Arrange
    mock_connect.return_value = object()

    # Act
    db.get_db()

    # Assert
    assert mock_connect.call_args.kwargs['connection_timeout'] == 5


@patch('services.get_db')
def test_route_closes_connection_when_query_fails(mock_get_db, monkeypatch):
    # Arrange
    cursor = ExplodingCursor()
    conn = TrackingConnection(cursor)
    mock_get_db.return_value = conn
    monkeypatch.setitem(app.config, 'PROPAGATE_EXCEPTIONS', True)
    client = app.test_client()

    # Act
    with pytest.raises(RuntimeError):
        client.get('/api/feed')

    # Assert
    assert cursor.closed is True
    assert conn.closed is True


@patch('services.get_db')
def test_service_closes_connection_when_query_fails(mock_get_db):
    # Arrange
    cursor = ExplodingCursor()
    conn = TrackingConnection(cursor)
    mock_get_db.return_value = conn

    # Act
    with pytest.raises(RuntimeError):
        services.get_user_by_session('some-token')

    # Assert
    assert cursor.closed is True
    assert conn.closed is True
