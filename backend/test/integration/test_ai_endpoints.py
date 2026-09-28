"""Integration tests for the AI endpoints: real routes and SQL against SQLite, with the offline brain."""
import pytest

import routes.ai
import services
from brain import FallbackBrain, OfflineBrain
from rate_limit import SlidingWindowLimiter

USER = {'name': 'Writer', 'email': 'writer@example.com', 'password': 'Password123!'}
OTHER = {'name': 'Other', 'email': 'other@example.com', 'password': 'Password123!'}
TOO_MANY = {'message': 'Too many AI requests. Please wait a minute and try again.'}


@pytest.fixture(autouse=True)
def fresh_limiter(monkeypatch):
    # The limiter is process-wide state; without a fresh one, earlier tests would use up later tests' budget.
    limiter = SlidingWindowLimiter(100, 60)
    monkeypatch.setattr(routes.ai, 'ai_limiter', limiter)
    return limiter


def log_in(client, user=USER):
    client.post('/api/signup', json=user)
    client.post('/api/login', json={'email': user['email'], 'password': user['password']})


def correct(client, payload):
    return client.post('/api/corrections', json=payload)


class UnreachableModel(OfflineBrain):
    name = 'unreachable'

    def propose_comments(self, post_title, post_body):
        raise TimeoutError('read timed out')

    def suggest_post(self, notes, seed):
        raise TimeoutError('read timed out')


# ---- /api/corrections ----

def test_correction_requires_login(client):
    # Arrange: nobody is logged in

    # Act
    response = correct(client, {'text': 'i love bouldring'})

    # Assert
    assert response.status_code == 401


def test_correction_returns_the_corrected_text(client):
    # Arrange
    log_in(client)

    # Act
    response = correct(client, {'text': 'i love bouldring'})

    # Assert
    assert response.status_code == 200
    assert response.get_json() == {'text': 'I love bouldering'}


def test_correction_keeps_paragraph_breaks(client):
    # Arrange: the composer sends one paragraph per line and splits the answer the same way.
    log_in(client)

    # Act
    response = correct(client, {'text': 'first paragraf\nsecond one'})

    # Assert
    assert response.get_json()['text'].count('\n') == 1


@pytest.mark.parametrize('payload, message', [
    ({}, 'Invalid JSON payload'),
    ({'text': '   '}, 'Text is required'),
    ({'text': 42}, 'Invalid input types'),
    ({'text': 'a' * 5001}, 'Text must be 5000 characters or fewer'),
])
def test_correction_rejects_bad_input(client, payload, message):
    # Arrange
    log_in(client)

    # Act
    response = correct(client, payload)

    # Assert
    assert response.status_code == 400
    assert response.get_json() == {'message': message}


# ---- /api/posts/<id>/comment-ideas ----

def test_comment_ideas_require_login(client):
    # Arrange: nobody is logged in

    # Act
    response = client.get('/api/posts/1/comment-ideas')

    # Assert
    assert response.status_code == 401


def test_comment_ideas_returns_three_ideas_for_the_post(client):
    # Arrange
    log_in(client)
    post_id = client.post('/api/posts', json={'title': 'Finally sent it', 'body': '<p>Six sessions.</p>'}).get_json()['postId']

    # Act
    response = client.get(f'/api/posts/{post_id}/comment-ideas')

    # Assert
    ideas = response.get_json()['comments']
    assert response.status_code == 200
    assert len(ideas) == 3 and all(idea.strip() for idea in ideas)


def test_comment_ideas_for_a_missing_post_returns_404(client):
    # Arrange
    log_in(client)

    # Act
    response = client.get('/api/posts/9999/comment-ideas')

    # Assert
    assert response.status_code == 404
    assert response.get_json() == {'message': 'Post not found'}


def test_comment_ideas_fall_back_to_offline_when_the_model_is_down(client, monkeypatch):
    # Arrange
    log_in(client)
    post_id = client.post('/api/posts', json={'title': 'Sent it', 'body': '<p>Yes.</p>'}).get_json()['postId']
    brain = FallbackBrain(UnreachableModel(), OfflineBrain(), lambda op, error: None)
    monkeypatch.setattr(services, 'get_brain', lambda fallback=True: brain)

    # Act
    response = client.get(f'/api/posts/{post_id}/comment-ideas')

    # Assert
    assert response.status_code == 200
    assert len(response.get_json()['comments']) == 3


# ---- /api/post-suggestions ----

def suggest(client, payload):
    return client.post('/api/post-suggestions', json=payload)


def test_post_suggestion_requires_login(client):
    # Arrange: nobody is logged in

    # Act
    response = suggest(client, {'style': 'Bouldering', 'grade': 'V4'})

    # Assert
    assert response.status_code == 401


def test_post_suggestion_returns_a_draft_for_the_style_and_grade(client):
    # Arrange
    log_in(client)

    # Act
    response = suggest(client, {'style': 'Bouldering', 'grade': 'V4', 'title': '', 'body': ''})

    # Assert
    draft = response.get_json()
    assert response.status_code == 200
    assert set(draft) == {'title', 'body'}
    assert 'V4' in f"{draft['title']} {draft['body']}"


def test_post_suggestion_keeps_what_the_author_wrote(client):
    # Arrange
    log_in(client)

    # Act
    response = suggest(client, {'style': 'Lead', 'grade': '6c+', 'title': 'First lead', 'body': 'Clipped every bolt.'})

    # Assert
    assert response.get_json() == {'title': 'First lead', 'body': 'Clipped every bolt.'}


@pytest.mark.parametrize('payload, message', [
    ({}, 'Invalid JSON payload'),
    ({'grade': 'V4'}, 'Style and grade are required'),
    ({'style': 1, 'grade': 'V4'}, 'Invalid input types'),
    ({'style': 'Lead', 'grade': 'V4', 'body': 'x' * 501}, 'Post suggestions work from up to 500 characters of text'),
])
def test_post_suggestion_rejects_bad_input(client, payload, message):
    # Arrange
    log_in(client)

    # Act
    response = suggest(client, payload)

    # Assert
    assert response.status_code == 400
    assert response.get_json() == {'message': message}


def test_post_suggestion_falls_back_to_offline_when_the_model_is_down(client, monkeypatch):
    # Arrange
    log_in(client)
    brain = FallbackBrain(UnreachableModel(), OfflineBrain(), lambda op, error: None)
    monkeypatch.setattr(services, 'get_brain', lambda fallback=True: brain)

    # Act
    response = suggest(client, {'style': 'Top rope', 'grade': '6b', 'title': '', 'body': ''})

    # Assert
    assert response.status_code == 200
    assert '6b' in f"{response.get_json()['title']} {response.get_json()['body']}"


def test_post_suggestion_shares_the_ai_request_budget(client, monkeypatch):
    # Arrange: one request allowed per minute, already used by a correction.
    monkeypatch.setattr(routes.ai, 'ai_limiter', SlidingWindowLimiter(1, 60))
    log_in(client)
    correct(client, {'text': 'one'})

    # Act
    response = suggest(client, {'style': 'Bouldering', 'grade': 'V4'})

    # Assert
    assert response.status_code == 429


# ---- Rate limiting ----

def test_requests_over_the_limit_get_429_with_retry_after(client, monkeypatch):
    # Arrange
    monkeypatch.setattr(routes.ai, 'ai_limiter', SlidingWindowLimiter(2, 60))
    log_in(client)
    correct(client, {'text': 'one'})
    correct(client, {'text': 'two'})

    # Act
    response = correct(client, {'text': 'three'})

    # Assert
    assert response.status_code == 429
    assert response.get_json() == TOO_MANY
    assert 1 <= int(response.headers['Retry-After']) <= 60


def test_the_limit_is_per_user(client, monkeypatch):
    # Arrange: one user uses up the budget.
    monkeypatch.setattr(routes.ai, 'ai_limiter', SlidingWindowLimiter(1, 60))
    log_in(client, USER)
    correct(client, {'text': 'one'})
    client.post('/api/logout')
    log_in(client, OTHER)

    # Act
    response = correct(client, {'text': 'two'})

    # Assert
    assert response.status_code == 200


def test_logged_out_requests_do_not_use_up_anyones_budget(client, monkeypatch):
    # Arrange: login is checked before the limit, so anonymous calls are refused without counting.
    monkeypatch.setattr(routes.ai, 'ai_limiter', SlidingWindowLimiter(1, 60))
    for _ in range(5):
        correct(client, {'text': 'spam'})
    log_in(client)

    # Act
    response = correct(client, {'text': 'real request'})

    # Assert
    assert response.status_code == 200
