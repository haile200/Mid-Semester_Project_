import secrets

from db import get_db
from utils import fetchone_dict, hash_password, verify_password


def create_user(name, email, password):
    """Register a new user. Returns the new user id, or None if the email is taken."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
    if fetchone_dict(cursor):
        cursor.close()
        conn.close()
        return None

    cursor.execute(
        "INSERT INTO users (name, email, password) VALUES (%s, %s, %s)",
        (name, email, hash_password(password))
    )
    conn.commit()
    user_id = cursor.lastrowid
    cursor.close()
    conn.close()
    return user_id


def authenticate(email, password):
    """Check credentials. Returns the user dict on success, None otherwise."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, name, email, password, profile_picture FROM users WHERE email = %s",
        (email,)
    )
    user = fetchone_dict(cursor)
    cursor.close()
    conn.close()

    if not user or not verify_password(password, user['password']):
        return None

    return {
        'id': user['id'],
        'name': user['name'],
        'email': user['email'],
        'profile_picture': user['profile_picture']
    }


def create_session(user_id):
    """Create a server-side session and return its opaque token."""
    token = secrets.token_urlsafe(32)
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO sessions (token, user_id) VALUES (%s, %s)",
        (token, user_id)
    )
    conn.commit()
    cursor.close()
    conn.close()
    return token


def get_user_by_session(token):
    """Resolve a session token to its user dict, or None if invalid."""
    if not token:
        return None

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT users.id, users.name, users.email, users.profile_picture
        FROM sessions
        JOIN users ON sessions.user_id = users.id
        WHERE sessions.token = %s
        """,
        (token,)
    )
    user = fetchone_dict(cursor)
    cursor.close()
    conn.close()
    return user


def delete_session(token):
    """Destroy a server-side session. Safe to call with a missing/unknown token."""
    if not token:
        return

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM sessions WHERE token = %s", (token,))
    conn.commit()
    cursor.close()
    conn.close()
