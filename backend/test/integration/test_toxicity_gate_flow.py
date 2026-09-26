"""Integration tests for the toxicity gate: real endpoints and SQL, with the
real offline brain deciding what may be published."""

USER = {'name': 'Gate Tester', 'email': 'gate@example.com', 'password': 'Password123!'}
REJECTED = {'message': 'Not published: contains blocked language'}


def log_in(client):
    client.post('/api/signup', json=USER)
    client.post('/api/login', json={'email': USER['email'], 'password': USER['password']})


def count(db, table):
    return db.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0]


def test_toxic_comment_is_rejected_and_not_stored(client, db):
    # Arrange
    log_in(client)
    post_id = client.post('/api/posts', json={'title': 'Sent it', 'body': '<p>Yes.</p>'}).get_json()['postId']

    # Act
    response = client.post(f'/api/posts/{post_id}/comments', json={'body': 'you are an idiot'})

    # Assert
    assert response.status_code == 400
    assert response.get_json() == REJECTED
    assert count(db, 'comments') == 0


def test_toxic_post_title_is_rejected_and_not_stored(client, db):
    # Arrange
    log_in(client)

    # Act
    response = client.post('/api/posts', json={'title': 'What an idiot', 'body': '<p>Fine body</p>'})

    # Assert
    assert response.status_code == 400
    assert response.get_json() == REJECTED
    assert count(db, 'posts') == 0


def test_toxic_word_split_by_markup_is_still_rejected(client, db):
    # Arrange: <strong> is an allowed tag, so it survives sanitizing and splits the word.
    log_in(client)

    # Act
    response = client.post('/api/posts', json={'title': 'Hello', 'body': '<p>id<strong>iot</strong></p>'})

    # Assert
    assert response.status_code == 400
    assert count(db, 'posts') == 0


def test_innocent_text_containing_a_blocked_word_is_published(client, db):
    # Arrange
    log_in(client)

    # Act
    response = client.post('/api/posts', json={'title': 'Warm-up?', 'body': '<p>Calling it easy is an oxymoron.</p>'})

    # Assert
    assert response.status_code == 201
    assert count(db, 'posts') == 1
