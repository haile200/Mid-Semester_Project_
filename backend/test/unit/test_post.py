import os
import sys
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from app import app
from mock_db import DummyCursor, DummyConnection


@patch('services.get_db')
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
            ('likeCount',),
            ('likedByMe',),
        ),
        rows=[
            (1, 'Post 1', 'Body 1', None, '2026-06-20', 5, 'Alice', None, 1, 0),
            (2, 'Post 2', 'Body 2', 'http://img', '2026-06-20', 6, 'Bob', 'http://pic', 0, 1),
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
            'likeCount': 1,
            'likedByMe': False,
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
            'likeCount': 0,
            'likedByMe': True,
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


@patch('services.get_user_by_session', return_value={'id': 3, 'name': 'Test User', 'email': 'test@example.com', 'profile_picture': None})
@patch('services.get_db')
def test_create_post_succeeds_when_logged_in(mock_get_db, mock_get_user):
    cursor = DummyCursor()
    mock_get_db.return_value = DummyConnection(cursor)

    client = app.test_client()
    client.set_cookie('session_token', 'test-token')

    response = client.post('/api/posts', json={
        'title': 'New Post',
        'body': 'Hello world',
        'imageUrl': 'http://example.com/pic.jpg',
    })

    assert response.status_code == 201
    assert response.get_json() == {'message': 'Post created successfully', 'postId': 42}
    assert mock_get_db.return_value.committed is True
    assert any('INSERT INTO posts' in q for q, _ in cursor.queries)


@patch('services.get_user_by_session', return_value={'id': 3, 'name': 'Test User', 'email': 'test@example.com', 'profile_picture': None})
@patch('services.get_db')
def test_create_post_sanitizes_body_before_insert(mock_get_db, mock_get_user):
    # Arrange
    cursor = DummyCursor()
    mock_get_db.return_value = DummyConnection(cursor)
    client = app.test_client()
    client.set_cookie('session_token', 'test-token')

    # Act
    response = client.post('/api/posts', json={
        'title': 'Crux beta',
        'body': '<p>heel hook</p><img src=x onerror="alert(1)"><script>alert(2)</script>',
    })

    # Assert
    assert response.status_code == 201
    insert_params = next(params for q, params in cursor.queries if 'INSERT INTO posts' in q)
    assert insert_params[1] == '<p>heel hook</p>'


@patch('services.get_user_by_session', return_value={'id': 3, 'name': 'Test User', 'email': 'test@example.com', 'profile_picture': None})
@patch('services.get_db')
def test_create_post_rejects_body_that_is_only_malicious_markup(mock_get_db, mock_get_user):
    # Arrange
    client = app.test_client()
    client.set_cookie('session_token', 'test-token')

    # Act
    response = client.post('/api/posts', json={
        'title': 'Crux beta',
        'body': '<script>alert(1)</script>',
    })

    # Assert
    assert response.status_code == 400
    assert response.get_json() == {'message': 'Title and body are required'}
    mock_get_db.assert_not_called()


@patch('services.get_db')
def test_get_users_returns_list(mock_get_db):
    cursor = DummyCursor(
        description=(
            ('id',),
            ('name',),
            ('profile_picture',),
            ('postCount',),
        ),
        rows=[
            (1, 'Alice', None, 3),
            (2, 'Bob', 'http://pic', 1),
        ]
    )
    mock_get_db.return_value = DummyConnection(cursor)

    client = app.test_client()
    response = client.get('/api/users')

    assert response.status_code == 200
    assert response.get_json() == [
        {'id': 1, 'name': 'Alice', 'profile_picture': None, 'postCount': 3},
        {'id': 2, 'name': 'Bob', 'profile_picture': 'http://pic', 'postCount': 1},
    ]


@patch('services.get_db')
def test_get_user_by_id_not_found(mock_get_db):
    cursor = DummyCursor(one=None)
    mock_get_db.return_value = DummyConnection(cursor)

    client = app.test_client()
    response = client.get('/api/users/999')

    assert response.status_code == 404
    assert response.get_json() == {'message': 'User not found'}


@patch('services.get_user_by_session', return_value={'id': 3, 'name': 'Test User', 'email': 'test@example.com', 'profile_picture': None})
@patch('services.get_db')
def test_get_user_by_id_returns_user_and_following_flag(mock_get_db, mock_get_user):
    cursor = DummyCursor(
        description=(
            ('id',),
            ('name',),
            ('bio',),
            ('profile_picture',),
            ('created_at',),
            ('postCount',),
            ('followersCount',),
            ('followingCount',),
        ),
        rows=[(7, 'Carol', 'Bio', None, '2026-06-20', 4, 2, 5)],
        one=(1,)
    )
    mock_get_db.return_value = DummyConnection(cursor)

    client = app.test_client()
    client.set_cookie('session_token', 'test-token')

    response = client.get('/api/users/7')

    assert response.status_code == 200
    assert response.get_json()['id'] == 7
    assert response.get_json()['name'] == 'Carol'
    assert response.get_json()['is_following'] is True
