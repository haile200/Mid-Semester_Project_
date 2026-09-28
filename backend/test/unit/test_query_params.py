import os
import sys
from unittest.mock import patch

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
import services
from app import app
from mock_db import DummyCursor, DummyConnection
from utils import MAX_PAGE_SIZE, parse_pagination


def test_parse_pagination_uses_defaults_when_absent():
    # Arrange
    args = {}

    # Act
    start, limit = parse_pagination(args)

    # Assert
    assert (start, limit) == (0, 10)


def test_parse_pagination_caps_oversized_limit():
    # Arrange
    args = {'start': '20', 'limit': '100000'}

    # Act
    start, limit = parse_pagination(args)

    # Assert
    assert (start, limit) == (20, MAX_PAGE_SIZE)


@pytest.mark.parametrize('args', [
    {'start': 'abc'},
    {'limit': 'ten'},
    {'limit': '2.5'},
    {'start': '-1'},
    {'limit': '0'},
    {'limit': '-5'},
])
def test_parse_pagination_rejects_invalid_values(args):
    # Arrange: args supplied by parametrize

    # Act / Assert
    with pytest.raises(ValueError):
        parse_pagination(args)


@pytest.mark.parametrize('url', [
    '/api/feed?start=abc',
    '/api/feed?limit=-1',
    '/api/posts?limit=0',
    '/api/posts?userId=abc',
    '/api/users?start=-3',
])
@patch('services.get_db')
def test_list_routes_reject_invalid_query_parameters(mock_get_db, url):
    # Arrange
    client = app.test_client()

    # Act
    response = client.get(url)

    # Assert
    assert response.status_code == 400
    assert response.get_json() == {'message': 'Invalid query parameters'}
    mock_get_db.assert_not_called()


@patch('services.get_db')
def test_feed_caps_oversized_limit_before_querying(mock_get_db):
    # Arrange
    cursor = DummyCursor(description=(('id',),), rows=[])
    mock_get_db.return_value = DummyConnection(cursor)
    client = app.test_client()

    # Act
    response = client.get('/api/feed?limit=100000')

    # Assert
    assert response.status_code == 200
    assert cursor.queries[0][1] == (None, MAX_PAGE_SIZE, 0)


@patch('services.get_db')
def test_public_user_queries_never_select_email(mock_get_db):
    # Arrange
    cursor = DummyCursor(description=(('id',),), rows=[])
    mock_get_db.return_value = DummyConnection(cursor)

    # Act
    services.list_users(0, 10)
    services.get_user_profile(7)

    # Assert
    assert len(cursor.queries) == 2
    assert all('users.email' not in query for query, _ in cursor.queries)
