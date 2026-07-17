"""Integration tests: real Flask endpoints + real SQL, against the injected
SQLite database from conftest.py. No mocks on the auth path itself."""

SIGNUP_PAYLOAD = {'name': 'Test User', 'email': 'test@example.com', 'password': 'Password123!'}


def signup(client, **overrides):
    return client.post('/api/signup', json={**SIGNUP_PAYLOAD, **overrides})


def login(client, email=SIGNUP_PAYLOAD['email'], password=SIGNUP_PAYLOAD['password']):
    return client.post('/api/login', json={'email': email, 'password': password})


def test_signup_persists_hashed_password(client, db):
    # Arrange - nothing beyond the empty database

    # Act
    response = signup(client)

    # Assert - user row exists and the stored password is a bcrypt hash, not plaintext
    assert response.status_code == 201
    assert response.get_json() == {'message': 'Registered successfully'}

    row = db.execute('SELECT password FROM users WHERE email = ?', (SIGNUP_PAYLOAD['email'],)).fetchone()
    assert row is not None
    assert row[0] != SIGNUP_PAYLOAD['password']
    assert row[0].startswith('$2b$')


def test_signup_rejects_duplicate_email(client):
    # Arrange
    signup(client)

    # Act
    duplicate = signup(client, name='Someone Else')

    # Assert
    assert duplicate.status_code == 400
    assert duplicate.get_json() == {'message': 'Email already registered'}


def test_signup_rejects_invalid_json(client):
    # Arrange
    not_json = 'not a json'

    # Act
    response = client.post('/api/signup', data=not_json, content_type='application/json')

    # Assert
    assert response.status_code == 400
    assert response.get_json() == {'message': 'Invalid JSON payload'}


def test_login_rejects_invalid_json(client):
    # Arrange
    not_json = 'not a json'

    # Act
    response = client.post('/api/login', data=not_json, content_type='application/json')

    # Assert
    assert response.status_code == 400
    assert response.get_json() == {'message': 'Invalid JSON payload'}


def test_signup_rejects_missing_fields(client):
    # Arrange
    incomplete = {'name': 'Test User'}

    # Act
    response = client.post('/api/signup', json=incomplete)

    # Assert
    assert response.status_code == 400
    assert response.get_json() == {'message': 'Name, email, and password are required'}


def test_signup_rejects_overlong_name(client):
    # Arrange - a 256-character name, above the 255-character column limit

    # Act
    response = signup(client, name='x' * 256)

    # Assert
    assert response.status_code == 400
    assert response.get_json() == {'message': 'Name is too long'}


def test_signup_rejects_invalid_email_format(client):
    # Arrange - a payload whose email has no domain part

    # Act
    response = signup(client, email='not-an-email')

    # Assert
    assert response.status_code == 400
    assert response.get_json() == {'message': 'Invalid email address'}


def test_signup_rejects_short_password(client):
    # Arrange - a 7-character password, below the 8-character minimum

    # Act
    response = signup(client, password='Short1!')

    # Assert
    assert response.status_code == 400
    assert response.get_json() == {'message': 'Password must be between 8 and 72 characters'}


def test_signup_rejects_non_string_input(client):
    # Arrange - a malicious payload where password is a list, not a string

    # Act
    response = signup(client, password=['not', 'a', 'string'])

    # Assert
    assert response.status_code == 400
    assert response.get_json() == {'message': 'Invalid input types'}


def test_login_rejects_non_string_input(client):
    # Arrange - a malicious payload where password is an object, not a string

    # Act
    response = client.post('/api/login', json={'email': 'test@example.com', 'password': {'evil': True}})

    # Assert
    assert response.status_code == 400
    assert response.get_json() == {'message': 'Invalid input types'}


def test_login_succeeds_and_sets_session_cookie(client, db):
    # Arrange
    signup(client)

    # Act
    response = login(client)

    # Assert - 200 with user payload and an httpOnly session cookie backed by a DB row
    assert response.status_code == 200
    body = response.get_json()
    assert body['message'] == 'Login successful'
    assert body['user']['email'] == SIGNUP_PAYLOAD['email']

    set_cookie = response.headers.get('Set-Cookie', '')
    assert 'session_token=' in set_cookie
    assert 'HttpOnly' in set_cookie

    token = set_cookie.split('session_token=')[1].split(';')[0]
    session_row = db.execute('SELECT user_id FROM sessions WHERE token = ?', (token,)).fetchone()
    assert session_row is not None


def test_login_rejects_wrong_password(client):
    # Arrange
    signup(client)

    # Act
    response = login(client, password='WrongPassword!')

    # Assert
    assert response.status_code == 401
    assert response.get_json() == {'message': 'Invalid credentials'}


def test_login_rejects_unknown_email(client):
    # Arrange - empty database

    # Act
    response = login(client, email='nobody@example.com')

    # Assert
    assert response.status_code == 401
    assert response.get_json() == {'message': 'Invalid credentials'}


def test_login_rejects_missing_fields(client):
    # Arrange
    incomplete = {'email': SIGNUP_PAYLOAD['email']}

    # Act
    response = client.post('/api/login', json=incomplete)

    # Assert
    assert response.status_code == 400
    assert response.get_json() == {'message': 'Email and password are required'}


def test_logout_destroys_session(client, db):
    # Arrange - a logged-in user whose session works
    signup(client)
    login(client)
    assert client.get('/api/auth/me').status_code == 200

    # Act
    response = client.post('/api/logout')

    # Assert - session gone server-side, cookie no longer accepted, logout idempotent
    assert response.status_code == 200
    assert db.execute('SELECT COUNT(*) FROM sessions').fetchone()[0] == 0
    assert client.get('/api/auth/me').status_code == 401
    assert client.post('/api/logout').status_code == 200


def test_me_requires_valid_session(client):
    # Arrange - no cookie at all, then a forged token

    # Act
    without_cookie = client.get('/api/auth/me')
    client.set_cookie('session_token', 'forged-token')
    with_forged_token = client.get('/api/auth/me')

    # Assert
    assert without_cookie.status_code == 401
    assert without_cookie.get_json() == {'message': 'Unauthorized. Please log in.'}
    assert with_forged_token.status_code == 401


def test_me_returns_current_user(client):
    # Arrange
    signup(client)
    login(client)

    # Act
    response = client.get('/api/auth/me')

    # Assert
    assert response.status_code == 200
    user = response.get_json()['user']
    assert user['name'] == SIGNUP_PAYLOAD['name']
    assert user['email'] == SIGNUP_PAYLOAD['email']
