import os
import sys
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from app import app


class DummyCursor:
    def __init__(self, description=(), rows=None, one=None):
        self.description = description
        self.rows = rows or []
        self.one = one
        self.queries = []
        self.lastrowid = 42

    def execute(self, query, params=None):
        self.queries.append((query, params or ()))

    def fetchall(self):
        return self.rows

    def fetchone(self):
        if self.one is not None:
            result = self.one
            self.one = None
            return result
        return self.rows[0] if self.rows else None

    def close(self):
        pass


class DummyConnection:
    def __init__(self, cursor):
        self._cursor = cursor
        self.committed = False

    def cursor(self):
        return self._cursor

    def commit(self):
        self.committed = True

    def close(self):
        pass


@patch('routes.posts.get_db')
def test_get_posts_returns_posts(mock_get_db):
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
        ),
        rows=[
            (1, 'Post 1', 'Body 1', None, '2026-06-20', 5, 'Alice', None),
            (2, 'Post 2', 'Body 2', 'http://img', '2026-06-20', 6, 'Bob', 'http://pic'),
        ]
    )
    mock_get_db.return_value = DummyConnection(cursor)

    client = app.test_client()
    response = client.get('/api/posts')

    assert response.status_code == 200
    assert response.get_json() == [
        {
            'id': 1,
            'title': 'Post 1',
            'body': 'Body 1',
            'image_url': None,
            'created_at': '2026-06-20',
            'userId': 5,
            'author_name': 'Alice',
            'author_profile_picture': None,
        },
        {
            'id': 2,
            'title': 'Post 2',
            'body': 'Body 2',
            'image_url': 'http://img',
            'created_at': '2026-06-20',
            'userId': 6,
            'author_name': 'Bob',
            'author_profile_picture': 'http://pic',
        },
    ]


def test_create_post_requires_login():
    client = app.test_client()
    response = client.post('/api/posts', json={
        'title': 'New Post',
        'body': 'Hello world',
        'imageUrl': None,
    })

    assert response.status_code == 401
    assert response.get_json() == {'message': 'Unauthorized. Please log in.'}


@patch('routes.posts.get_db')
def test_create_post_succeeds_when_logged_in(mock_get_db):
    cursor = DummyCursor()
    mock_get_db.return_value = DummyConnection(cursor)

    client = app.test_client()
    with client.session_transaction() as sess:
        sess['user_id'] = 3

    response = client.post('/api/posts', json={
        'title': 'New Post',
        'body': 'Hello world',
        'imageUrl': 'http://example.com/pic.jpg',
    })

    assert response.status_code == 201
    assert response.get_json() == {'message': 'Post created successfully', 'postId': 42}
    assert mock_get_db.return_value.committed is True
    assert any('INSERT INTO posts' in q for q, _ in cursor.queries)


@patch('routes.users.get_db')
def test_get_users_returns_list(mock_get_db):
    cursor = DummyCursor(
        description=(
            ('id',),
            ('name',),
            ('email',),
            ('profile_picture',),
            ('postCount',),
        ),
        rows=[
            (1, 'Alice', 'alice@example.com', None, 3),
            (2, 'Bob', 'bob@example.com', 'http://pic', 1),
        ]
    )
    mock_get_db.return_value = DummyConnection(cursor)

    client = app.test_client()
    response = client.get('/api/users')

    assert response.status_code == 200
    assert response.get_json() == [
        {'id': 1, 'name': 'Alice', 'email': 'alice@example.com', 'profile_picture': None, 'postCount': 3},
        {'id': 2, 'name': 'Bob', 'email': 'bob@example.com', 'profile_picture': 'http://pic', 'postCount': 1},
    ]


@patch('routes.users.get_db')
def test_get_user_by_id_not_found(mock_get_db):
    cursor = DummyCursor(one=None)
    mock_get_db.return_value = DummyConnection(cursor)

    client = app.test_client()
    response = client.get('/api/users/999')

    assert response.status_code == 404
    assert response.get_json() == {'message': 'User not found'}


@patch('routes.users.get_db')
def test_get_user_by_id_returns_user_and_following_flag(mock_get_db):
    cursor = DummyCursor(
        description=(
            ('id',),
            ('name',),
            ('email',),
            ('bio',),
            ('profile_picture',),
            ('created_at',),
            ('postCount',),
            ('followersCount',),
            ('followingCount',),
        ),
        rows=[(7, 'Carol', 'carol@example.com', 'Bio', None, '2026-06-20', 4, 2, 5)],
        one=(1,)
    )
    mock_get_db.return_value = DummyConnection(cursor)

    client = app.test_client()
    with client.session_transaction() as sess:
        sess['user_id'] = 3

    response = client.get('/api/users/7')

    assert response.status_code == 200
    assert response.get_json()['id'] == 7
    assert response.get_json()['name'] == 'Carol'
    assert response.get_json()['is_following'] is True