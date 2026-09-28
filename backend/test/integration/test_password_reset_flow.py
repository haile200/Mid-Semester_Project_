"""Password reset end to end: real routes and SQL against SQLite, with outgoing email captured."""
import hashlib
import re

import pytest

import mailer
import routes.auth
import services
from rate_limit import SlidingWindowLimiter

USER = {'name': 'Alex', 'email': 'alex@example.com', 'password': 'OldPassword1!'}
NEW_PASSWORD = 'NewPassword2!'
REQUESTED = {'message': 'If that email has an account, a reset link is on its way.'}
INVALID_LINK = {'message': 'This reset link is invalid or has expired. Please ask for a new one.'}


@pytest.fixture
def outbox(monkeypatch):
    sent = []
    monkeypatch.setattr(mailer, 'send_in_background', lambda to, subject, body: sent.append((to, subject, body)))
    return sent


@pytest.fixture(autouse=True)
def fresh_limiter(monkeypatch):
    # Process-wide state: without a fresh limiter, earlier tests would use up later tests' budget.
    monkeypatch.setattr(routes.auth, 'reset_limiter', SlidingWindowLimiter(100, 900))


def sign_up(client, user=USER):
    client.post('/api/signup', json=user)


def log_in(client, email=USER['email'], password=USER['password']):
    return client.post('/api/login', json={'email': email, 'password': password})


def request_reset(client, email=USER['email']):
    return client.post('/api/password-resets', json={'email': email})


def token_from(email):
    return re.search(r'#token=([\w-]+)', email[2]).group(1)


def confirm(client, token, password=NEW_PASSWORD):
    return client.post('/api/password-resets/confirm', json={'token': token, 'password': password})


# ---- Asking for a link ----

def test_a_registered_user_gets_one_email_with_a_fragment_link(client, outbox):
    # Arrange
    sign_up(client)

    # Act
    response = request_reset(client)

    # Assert
    assert response.status_code == 200
    assert response.get_json() == REQUESTED
    assert len(outbox) == 1
    to, subject, body = outbox[0]
    assert to == USER['email']
    assert subject == 'Reset your My Beta password'
    assert '/reset-password#token=' in body


def test_an_unknown_email_gets_the_same_answer_and_no_email(client, outbox):
    # Arrange: nobody is registered

    # Act
    response = request_reset(client, 'nobody@example.com')

    # Assert
    assert response.status_code == 200
    assert response.get_json() == REQUESTED
    assert outbox == []


def test_bots_and_banned_users_get_no_email(client, db, outbox):
    # Arrange
    services.upsert_bot('Bot', 'bot@example.test', 'bio', 'personality')
    sign_up(client)
    db.execute("UPDATE users SET banned_at = CURRENT_TIMESTAMP WHERE email = ?", (USER['email'],))

    # Act
    responses = [request_reset(client, 'bot@example.test'), request_reset(client)]

    # Assert
    assert [r.get_json() for r in responses] == [REQUESTED, REQUESTED]
    assert outbox == []


@pytest.mark.parametrize('payload, message', [
    (None, 'Invalid JSON payload'),
    ({'email': 42}, 'Invalid input types'),
    ({'email': 'not-an-email'}, 'Invalid email address'),
    ({}, 'Invalid email address'),
])
def test_a_bad_request_is_rejected(client, outbox, payload, message):
    # Arrange: nothing

    # Act
    response = client.post('/api/password-resets', json=payload)

    # Assert
    assert response.status_code == 400
    assert response.get_json() == {'message': message}


def test_only_a_hash_of_the_token_is_stored(client, db, outbox):
    # Arrange
    sign_up(client)
    request_reset(client)
    token = token_from(outbox[0])

    # Act
    stored = [row[0] for row in db.execute("SELECT token_hash FROM password_resets")]

    # Assert
    assert stored == [hashlib.sha256(token.encode()).hexdigest()]


def test_requests_per_email_are_limited(client, outbox, monkeypatch):
    # Arrange: two emails allowed per address in the window
    monkeypatch.setattr(routes.auth, 'reset_limiter', SlidingWindowLimiter(2, 900))
    sign_up(client)
    request_reset(client)
    request_reset(client)

    # Act
    blocked = request_reset(client, USER['email'].upper())
    other = request_reset(client, 'someone-else@example.com')

    # Assert: the limit ignores letter case, and other addresses are unaffected.
    assert blocked.status_code == 429
    assert 'Retry-After' in blocked.headers
    assert other.status_code == 200
    assert len(outbox) == 2


# ---- Using the link ----

def test_the_link_sets_a_new_password(client, outbox):
    # Arrange
    sign_up(client)
    request_reset(client)

    # Act
    response = confirm(client, token_from(outbox[0]))

    # Assert
    assert response.status_code == 200
    assert response.get_json() == {'message': 'Password updated. You can log in with your new password.'}
    assert log_in(client).status_code == 401
    assert log_in(client, password=NEW_PASSWORD).status_code == 200


def test_resetting_logs_the_account_out_everywhere(client, db, outbox):
    # Arrange: the account is logged in, perhaps by someone else.
    sign_up(client)
    log_in(client)
    request_reset(client)

    # Act
    confirm(client, token_from(outbox[0]))

    # Assert
    assert db.execute("SELECT COUNT(*) FROM sessions").fetchone()[0] == 0
    assert client.get('/api/auth/me').status_code == 401


def test_a_link_works_only_once(client, outbox):
    # Arrange
    sign_up(client)
    request_reset(client)
    token = token_from(outbox[0])
    confirm(client, token)

    # Act
    response = confirm(client, token, 'AnotherPassword3!')

    # Assert
    assert response.status_code == 400
    assert response.get_json() == INVALID_LINK
    assert log_in(client, password=NEW_PASSWORD).status_code == 200


def test_an_expired_link_is_rejected(client, db, outbox):
    # Arrange: the link was sent 31 minutes ago.
    sign_up(client)
    request_reset(client)
    db.execute("UPDATE password_resets SET created_at = datetime('now', '-31 minutes')")

    # Act
    response = confirm(client, token_from(outbox[0]))

    # Assert
    assert response.get_json() == INVALID_LINK
    assert log_in(client).status_code == 200


def test_a_link_just_inside_the_lifetime_still_works(client, db, outbox):
    # Arrange
    sign_up(client)
    request_reset(client)
    db.execute("UPDATE password_resets SET created_at = datetime('now', '-29 minutes')")

    # Act
    response = confirm(client, token_from(outbox[0]))

    # Assert
    assert response.status_code == 200


def test_a_newer_link_replaces_the_older_one(client, outbox):
    # Arrange
    sign_up(client)
    request_reset(client)
    request_reset(client)
    older, newer = token_from(outbox[0]), token_from(outbox[1])

    # Act
    old_response = confirm(client, older)
    new_response = confirm(client, newer)

    # Assert
    assert old_response.get_json() == INVALID_LINK
    assert new_response.status_code == 200


def test_a_user_banned_after_asking_cannot_use_the_link(client, db, outbox):
    # Arrange
    sign_up(client)
    request_reset(client)
    db.execute("UPDATE users SET banned_at = CURRENT_TIMESTAMP")

    # Act
    response = confirm(client, token_from(outbox[0]))

    # Assert
    assert response.get_json() == INVALID_LINK


@pytest.mark.parametrize('token', ['made-up-token', '', None, 42])
def test_an_unknown_token_is_rejected(client, token):
    # Arrange: nothing

    # Act
    response = confirm(client, token)

    # Assert
    assert response.status_code == 400
    assert response.get_json() == INVALID_LINK


@pytest.mark.parametrize('password', ['short', 'x' * 73, None, 12345678])
def test_an_invalid_new_password_keeps_the_link_usable(client, outbox, password):
    # Arrange
    sign_up(client)
    request_reset(client)
    token = token_from(outbox[0])

    # Act
    rejected = confirm(client, token, password)
    accepted = confirm(client, token)

    # Assert
    assert rejected.status_code == 400
    assert rejected.get_json() == {'message': 'Password must be between 8 and 72 characters'}
    assert accepted.status_code == 200
