import os
import sys
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from app import app

@patch('routes.feed.get_db')
def test_get_feed_returns_posts(mock_get_db):
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
            )
            self._data = [
                (1, 'Title 1', 'Body 1', None, '2026-01-01', 10, 'Alice', None),
                (2, 'Title 2', 'Body 2', 'http://img', '2026-01-02', 11, 'Bob', None),
            ]

        def execute(self, query, params=None):
            self.last_query = query
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
        },
    ]

def test_get_following_feed_requires_login():
    client = app.test_client()
    response = client.get('/api/feed/following')
    assert response.status_code == 401
    assert response.get_json() == {'message': 'Unauthorized. Please log in.'}

@patch('routes.feed.get_db')
def test_get_following_feed_returns_posts(mock_get_db):
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
            )
            self._data = [
                (3, 'Followed Post', 'Body', None, '2026-01-03', 12, 'Carol', None),
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
    with client.session_transaction() as sess:
        sess['user_id'] = 1

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
        }
    ]