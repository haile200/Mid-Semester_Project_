import os
import sys
from unittest.mock import patch

import mysql.connector

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
import services
from app import app
from mock_db import DummyCursor, DummyConnection

LOGGED_IN_USER = {'id': 3, 'name': 'Test User', 'email': 'test@example.com', 'profile_picture': None}


class DuplicateInsertCursor(DummyCursor):
    def execute(self, query, params=None):
        super().execute(query, params)
        raise mysql.connector.IntegrityError('Duplicate entry')


@patch('services.get_db')
def test_list_posts_filters_by_author_when_given(mock_get_db):
    # Arrange
    cursor = DummyCursor(description=(('id',),), rows=[])
    mock_get_db.return_value = DummyConnection(cursor)

    # Act
    services.list_posts(start=20, limit=10, author_id=7)

    # Assert
    query, params = cursor.queries[0]
    assert 'WHERE posts.author_id = %s' in query
    # The viewer comes first: it feeds likedByMe in the column list.
    assert params == (None, 7, 10, 20)


@patch('services.get_db')
def test_list_users_applies_name_search(mock_get_db):
    # Arrange
    cursor = DummyCursor(description=(('id',),), rows=[])
    mock_get_db.return_value = DummyConnection(cursor)

    # Act
    services.list_users(start=0, limit=5, search='ali')

    # Assert
    query, params = cursor.queries[0]
    assert 'WHERE users.name LIKE %s' in query
    assert params == ('%ali%', 5, 0)


@patch('services.get_db')
def test_get_user_profile_for_anonymous_viewer_skips_follow_lookup(mock_get_db):
    # Arrange
    cursor = DummyCursor(
        description=(('id',), ('name',)),
        rows=[(7, 'Carol')],
    )
    mock_get_db.return_value = DummyConnection(cursor)

    # Act
    profile = services.get_user_profile(7, viewer_id=None)

    # Assert
    assert profile == {'id': 7, 'name': 'Carol', 'is_following': False}
    assert len(cursor.queries) == 1


@patch('services.get_db')
def test_update_profile_commits_new_values(mock_get_db):
    # Arrange
    cursor = DummyCursor()
    conn = DummyConnection(cursor)
    mock_get_db.return_value = conn

    # Act
    services.update_profile(3, 'Crimper', 'http://pic')

    # Assert
    query, params = cursor.queries[0]
    assert query.startswith('UPDATE users')
    assert params == ('Crimper', 'http://pic', 3)
    assert conn.committed is True


@patch('services.get_db')
def test_follow_user_returns_true_and_commits_new_follow(mock_get_db):
    # Arrange
    cursor = DummyCursor()
    conn = DummyConnection(cursor)
    mock_get_db.return_value = conn

    # Act
    created = services.follow_user(3, 7)

    # Assert
    assert created is True
    assert conn.committed is True
    assert cursor.queries[0][1] == (3, 7)


@patch('services.get_db')
def test_follow_user_returns_false_when_already_following(mock_get_db):
    # Arrange
    cursor = DuplicateInsertCursor()
    conn = DummyConnection(cursor)
    mock_get_db.return_value = conn

    # Act
    created = services.follow_user(3, 7)

    # Assert
    assert created is False
    assert conn.committed is False


@patch('services.get_db')
def test_unfollow_user_deletes_and_commits(mock_get_db):
    # Arrange
    cursor = DummyCursor()
    conn = DummyConnection(cursor)
    mock_get_db.return_value = conn

    # Act
    services.unfollow_user(3, 7)

    # Assert
    query, params = cursor.queries[0]
    assert query.startswith('DELETE FROM followers')
    assert params == (3, 7)
    assert conn.committed is True


def test_follow_route_requires_login():
    # Arrange
    client = app.test_client()

    # Act
    response = client.post('/api/follow/7')

    # Assert
    assert response.status_code == 401
    assert response.get_json() == {'message': 'Unauthorized. Please log in.'}


@patch('services.get_user_by_session', return_value=LOGGED_IN_USER)
@patch('services.get_db')
def test_follow_route_rejects_following_yourself(mock_get_db, mock_get_user):
    # Arrange
    client = app.test_client()
    client.set_cookie('session_token', 'test-token')

    # Act
    response = client.post('/api/follow/3')

    # Assert
    assert response.status_code == 400
    assert response.get_json() == {'message': 'You cannot follow yourself.'}
    mock_get_db.assert_not_called()


@patch('services.get_user_by_session', return_value=LOGGED_IN_USER)
@patch('services.get_db')
def test_follow_route_reports_existing_follow(mock_get_db, mock_get_user):
    # Arrange
    mock_get_db.return_value = DummyConnection(DuplicateInsertCursor())
    client = app.test_client()
    client.set_cookie('session_token', 'test-token')

    # Act
    response = client.post('/api/follow/7')

    # Assert
    assert response.status_code == 200
    assert response.get_json() == {'message': 'Already following this user'}


@patch('services.get_user_by_session', return_value=LOGGED_IN_USER)
@patch('services.get_db')
def test_unfollow_route_reports_success(mock_get_db, mock_get_user):
    # Arrange
    mock_get_db.return_value = DummyConnection(DummyCursor())
    client = app.test_client()
    client.set_cookie('session_token', 'test-token')

    # Act
    response = client.delete('/api/follow/7')

    # Assert
    assert response.status_code == 200
    assert response.get_json() == {'message': 'Successfully unfollowed user'}


@patch('services.get_user_by_session', return_value=LOGGED_IN_USER)
@patch('services.get_db')
def test_update_profile_route_uses_logged_in_user(mock_get_db, mock_get_user):
    # Arrange
    cursor = DummyCursor()
    mock_get_db.return_value = DummyConnection(cursor)
    client = app.test_client()
    client.set_cookie('session_token', 'test-token')

    # Act
    response = client.put('/api/users/profile', json={'bio': 'Crimper', 'profilePicture': 'http://pic'})

    # Assert
    assert response.status_code == 200
    assert response.get_json() == {'message': 'Profile updated successfully'}
    assert cursor.queries[0][1] == ('Crimper', 'http://pic', 3)
