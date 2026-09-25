"""Integration tests for comments: real Flask endpoints and real SQL, against
the SQLite database injected by conftest.py."""
import pytest

USER = {'name': 'Crag Tester', 'email': 'crag@example.com', 'password': 'Password123!'}


def log_in(client, **overrides):
    user = {**USER, **overrides}
    client.post('/api/signup', json=user)
    client.post('/api/login', json={'email': user['email'], 'password': user['password']})


def create_post(client, title='Sent my project'):
    response = client.post('/api/posts', json={'title': title, 'body': '<p>Finally.</p>'})
    return response.get_json()['postId']


def add_comment(client, post_id, body='Nice send', parent_id=None):
    payload = {'body': body}
    if parent_id is not None:
        payload['parent_id'] = parent_id
    return client.post(f'/api/posts/{post_id}/comments', json=payload)


def test_comment_requires_login(client, db):
    # Arrange: a post exists, then the author logs out.
    log_in(client)
    post_id = create_post(client)
    client.post('/api/logout')

    # Act
    response = add_comment(client, post_id)

    # Assert
    assert response.status_code == 401
    assert response.get_json() == {'message': 'Unauthorized. Please log in.'}
    assert db.execute('SELECT COUNT(*) FROM comments').fetchone()[0] == 0


def test_created_comment_is_listed_with_its_author(client):
    # Arrange
    log_in(client)
    post_id = create_post(client)

    # Act
    created = add_comment(client, post_id, body='Nice send')
    listed = client.get(f'/api/posts/{post_id}/comments')

    # Assert: the response describes exactly what a later read returns.
    assert created.status_code == 201
    payload = created.get_json()
    assert payload['message'] == 'Comment created successfully'
    comment = payload['comment']
    assert comment['body'] == 'Nice send'
    assert comment['post_id'] == post_id
    assert comment['parent_id'] is None
    assert comment['author_name'] == 'Crag Tester'
    assert comment['author_is_bot'] is False
    assert listed.status_code == 200
    assert listed.get_json() == [comment]


def test_comments_are_listed_oldest_first(client):
    # Arrange
    log_in(client)
    post_id = create_post(client)
    for body in ['first', 'second', 'third']:
        add_comment(client, post_id, body=body)

    # Act
    listed = client.get(f'/api/posts/{post_id}/comments')

    # Assert
    assert [c['body'] for c in listed.get_json()] == ['first', 'second', 'third']


def test_reply_is_linked_to_its_parent(client):
    # Arrange
    log_in(client)
    post_id = create_post(client)
    parent = add_comment(client, post_id, body='Where is the rest?').get_json()['comment']

    # Act
    reply = add_comment(client, post_id, body='Kneebar after the roof', parent_id=parent['id'])

    # Assert
    assert reply.status_code == 201
    assert reply.get_json()['comment']['parent_id'] == parent['id']


def test_reply_to_a_comment_on_another_post_is_rejected(client):
    # Arrange: a comment exists on post A; the reply targets post B.
    log_in(client)
    post_a = create_post(client, title='Post A')
    post_b = create_post(client, title='Post B')
    comment_on_a = add_comment(client, post_a).get_json()['comment']

    # Act
    response = add_comment(client, post_b, parent_id=comment_on_a['id'])

    # Assert
    assert response.status_code == 400
    assert response.get_json() == {'message': 'Parent comment not found on this post'}


def test_reply_to_a_missing_comment_is_rejected(client):
    # Arrange
    log_in(client)
    post_id = create_post(client)

    # Act
    response = add_comment(client, post_id, parent_id=9999)

    # Assert
    assert response.status_code == 400
    assert response.get_json() == {'message': 'Parent comment not found on this post'}


def test_comment_on_a_missing_post_returns_404(client):
    # Arrange
    log_in(client)

    # Act
    response = add_comment(client, 9999)

    # Assert
    assert response.status_code == 404
    assert response.get_json() == {'message': 'Post not found'}


def test_listing_comments_of_a_missing_post_returns_404(client):
    # Arrange: an empty database

    # Act
    response = client.get('/api/posts/9999/comments')

    # Assert
    assert response.status_code == 404
    assert response.get_json() == {'message': 'Post not found'}


def test_blank_comment_is_rejected(client, db):
    # Arrange
    log_in(client)
    post_id = create_post(client)

    # Act
    response = add_comment(client, post_id, body='   ')

    # Assert
    assert response.status_code == 400
    assert response.get_json() == {'message': 'Comment cannot be empty'}
    assert db.execute('SELECT COUNT(*) FROM comments').fetchone()[0] == 0


def test_comment_over_the_length_limit_is_rejected(client):
    # Arrange
    log_in(client)
    post_id = create_post(client)

    # Act
    response = add_comment(client, post_id, body='a' * 1001)

    # Assert
    assert response.status_code == 400
    assert response.get_json() == {'message': 'Comment must be 1000 characters or fewer'}


@pytest.mark.parametrize('parent_id', ['5', True, 1.5])
def test_non_integer_parent_id_is_rejected(client, parent_id):
    # Arrange: True matters because Python treats booleans as integers.
    log_in(client)
    post_id = create_post(client)

    # Act
    response = client.post(f'/api/posts/{post_id}/comments', json={'body': 'x', 'parent_id': parent_id})

    # Assert
    assert response.status_code == 400
    assert response.get_json() == {'message': 'Invalid input types'}


def test_comment_markup_is_stored_as_plain_text(client):
    # Arrange: comments are rendered as text, so markup is kept verbatim, never interpreted.
    log_in(client)
    post_id = create_post(client)
    body = '<b>bold</b> <script>alert(1)</script>'

    # Act
    created = add_comment(client, post_id, body=body)

    # Assert
    assert created.get_json()['comment']['body'] == body


def test_create_comment_rejects_invalid_json(client):
    # Arrange
    log_in(client)
    post_id = create_post(client)

    # Act
    response = client.post(f'/api/posts/{post_id}/comments', data='not json', content_type='application/json')

    # Assert
    assert response.status_code == 400
    assert response.get_json() == {'message': 'Invalid JSON payload'}


def test_list_comments_rejects_invalid_pagination(client):
    # Arrange
    log_in(client)
    post_id = create_post(client)

    # Act
    response = client.get(f'/api/posts/{post_id}/comments?limit=abc')

    # Assert
    assert response.status_code == 400
    assert response.get_json() == {'message': 'Invalid query parameters'}
