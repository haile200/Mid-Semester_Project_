import os
import sys
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from app import app
from mock_db import DummyCursor, DummyConnection

@patch('services.get_db')
def test_get_feed_returns_posts(mock_get_db):
    cursor = DummyCursor(
        description=(
            ('id',),
            ('title',),
            ('body',),
            ('image_url',),
            ('created_at',),
            ('userId',),
            ('author_name',),
            ('author_profile_picture',),
            ('likeCount',),
            ('likedByMe',),
        ),
        rows=[
            (1, 'Title 1', 'Body 1', None, '2026-01-01', 10, 'Alice', None, 4, 1),
            (2, 'Title 2', 'Body 2', 'http://img', '2026-01-02', 11, 'Bob', None, 0, 0),
        ]
    )
    mock_get_db.return_value = DummyConnection(cursor)

    client = app.test_client()
    response = client.get('/api/feed')

    assert response.status_code == 200
    assert response.get_json() == [
        {
            'id': 1,
            'title': 'Title 1',
            'body': 'Body 1',
            'image_url': None,
            'created_at': '2026-01-01',
            'userId': 10,
            'author_name': 'Alice',
            'author_profile_picture': None,
            'likeCount': 4,
            'likedByMe': True,
        },
        {
            'id': 2,
            'title': 'Title 2',
            'body': 'Body 2',
            'image_url': 'http://img',
            'created_at': '2026-01-02',
            'userId': 11,
            'author_name': 'Bob',
            'author_profile_picture': None,
            'likeCount': 0,
            'likedByMe': False,
        },
    ]

def test_get_following_feed_requires_login():
    client = app.test_client()
    response = client.get('/api/feed/following')
    assert response.status_code == 401
    assert response.get_json() == {'message': 'Unauthorized. Please log in.'}

@patch('services.get_user_by_session', return_value={'id': 1, 'name': 'Test User', 'email': 'test@example.com', 'profile_picture': None})
@patch('services.get_db')
def test_get_following_feed_returns_posts(mock_get_db, mock_get_user):
    class DummyCursor:
        def __init__(self):
            self.description = (
                ('id',),
                ('title',),
                ('body',),
                ('image_url',),
                ('created_at',),
                ('userId',),
                ('author_name',),
                ('author_profile_picture',),
                ('likeCount',),
                ('likedByMe',),
            )
            self._data = [
                (3, 'Followed Post', 'Body', None, '2026-01-03', 12, 'Carol', None, 2, 0),
            ]

        def execute(self, query, params=None):
            self.last_params = params

        def fetchall(self):
            return self._data

        def close(self):
            pass

    dummy_cursor = DummyCursor()
    class DummyConn:
        def cursor(self):
            return dummy_cursor
        def close(self):
            pass

    mock_get_db.return_value = DummyConn()

    client = app.test_client()
    client.set_cookie('session_token', 'test-token')

    response = client.get('/api/feed/following')

    assert response.status_code == 200
    assert response.get_json() == [
        {
            'id': 3,
            'title': 'Followed Post',
            'body': 'Body',
            'image_url': None,
            'created_at': '2026-01-03',
            'userId': 12,
            'author_name': 'Carol',
            'author_profile_picture': None,
            'likeCount': 2,
            'likedByMe': False,
        }
    ]