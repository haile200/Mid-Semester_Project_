import secrets
from contextlib import closing

import mysql.connector

from db import get_db
from utils import (
    clean_comment_body,
    fetchall_dict,
    fetchone_dict,
    hash_password,
    sanitize_post_html,
    verify_password,
)

POST_COLUMNS = """
    posts.id, posts.title, posts.body, posts.image_url, posts.created_at,
    users.id AS userId,
    users.name AS author_name,
    users.profile_picture AS author_profile_picture
"""

COMMENT_COLUMNS = """
    comments.id, comments.post_id, comments.parent_id, comments.body, comments.created_at,
    users.id AS userId,
    users.name AS author_name,
    users.profile_picture AS author_profile_picture,
    users.is_bot AS author_is_bot
"""


def _fetch_all(query, params):
    with closing(get_db()) as conn, closing(conn.cursor()) as cursor:
        cursor.execute(query, params)
        return fetchall_dict(cursor)


# ---- Users and sessions ----

def create_user(name, email, password):
    """Register a new user. Returns the new user id, or None if the email is taken."""
    with closing(get_db()) as conn, closing(conn.cursor()) as cursor:
        cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
        if fetchone_dict(cursor):
            return None

        cursor.execute(
            "INSERT INTO users (name, email, password) VALUES (%s, %s, %s)",
            (name, email, hash_password(password))
        )
        conn.commit()
        return cursor.lastrowid


def authenticate(email, password):
    """Check credentials. Returns the user dict on success, None otherwise."""
    with closing(get_db()) as conn, closing(conn.cursor()) as cursor:
        cursor.execute(
            "SELECT id, name, email, password, profile_picture FROM users WHERE email = %s",
            (email,)
        )
        user = fetchone_dict(cursor)

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
    with closing(get_db()) as conn, closing(conn.cursor()) as cursor:
        cursor.execute(
            "INSERT INTO sessions (token, user_id) VALUES (%s, %s)",
            (token, user_id)
        )
        conn.commit()
    return token


def get_user_by_session(token):
    """Resolve a session token to its user dict, or None if invalid."""
    if not token:
        return None

    with closing(get_db()) as conn, closing(conn.cursor()) as cursor:
        cursor.execute(
            """
            SELECT users.id, users.name, users.email, users.profile_picture
            FROM sessions
            JOIN users ON sessions.user_id = users.id
            WHERE sessions.token = %s
            """,
            (token,)
        )
        return fetchone_dict(cursor)


def delete_session(token):
    """Destroy a server-side session. Safe to call with a missing/unknown token."""
    if not token:
        return

    with closing(get_db()) as conn, closing(conn.cursor()) as cursor:
        cursor.execute("DELETE FROM sessions WHERE token = %s", (token,))
        conn.commit()


# ---- Posts and feeds ----

def list_feed(start, limit):
    return _fetch_all(
        f"""
        SELECT {POST_COLUMNS}
        FROM posts
        JOIN users ON posts.author_id = users.id
        ORDER BY posts.id DESC LIMIT %s OFFSET %s
        """,
        (limit, start)
    )


def list_following_feed(viewer_id, start, limit):
    return _fetch_all(
        f"""
        SELECT {POST_COLUMNS}
        FROM posts
        JOIN users ON posts.author_id = users.id
        JOIN followers ON posts.author_id = followers.following_id
        WHERE followers.follower_id = %s
        ORDER BY posts.id DESC LIMIT %s OFFSET %s
        """,
        (viewer_id, limit, start)
    )


def list_posts(start, limit, author_id=None):
    query = f"SELECT {POST_COLUMNS} FROM posts JOIN users ON posts.author_id = users.id"
    params = []

    if author_id is not None:
        query += " WHERE posts.author_id = %s"
        params.append(author_id)

    query += " ORDER BY posts.id DESC LIMIT %s OFFSET %s"
    params.extend([limit, start])
    return _fetch_all(query, tuple(params))


def create_post(author_id, title, body, image_url=None):
    """Sanitize and store a post. Raises ValueError if title or body is empty after cleaning."""
    title = (title or '').strip()
    body = sanitize_post_html(body or '').strip()
    if not title or not body:
        raise ValueError('Title and body are required')

    with closing(get_db()) as conn, closing(conn.cursor()) as cursor:
        cursor.execute(
            "INSERT INTO posts (title, body, image_url, author_id) VALUES (%s, %s, %s, %s)",
            (title, body, image_url, author_id)
        )
        conn.commit()
        return cursor.lastrowid


# ---- Comments ----

def _as_comment(row):
    row['author_is_bot'] = bool(row['author_is_bot'])
    return row


def post_exists(post_id):
    with closing(get_db()) as conn, closing(conn.cursor()) as cursor:
        cursor.execute("SELECT 1 FROM posts WHERE id = %s", (post_id,))
        return cursor.fetchone() is not None


def list_comments(post_id, start, limit):
    rows = _fetch_all(
        f"""
        SELECT {COMMENT_COLUMNS}
        FROM comments
        JOIN users ON comments.author_id = users.id
        WHERE comments.post_id = %s
        ORDER BY comments.created_at, comments.id
        LIMIT %s OFFSET %s
        """,
        (post_id, limit, start)
    )
    return [_as_comment(row) for row in rows]


def create_comment(post_id, author_id, body, parent_id=None):
    """Store a comment or reply and return it.

    Raises ValueError for invalid text or a parent outside this post, LookupError if the post is missing.
    """
    body = clean_comment_body(body)

    with closing(get_db()) as conn, closing(conn.cursor()) as cursor:
        cursor.execute("SELECT 1 FROM posts WHERE id = %s", (post_id,))
        if cursor.fetchone() is None:
            raise LookupError('Post not found')

        if parent_id is not None:
            cursor.execute("SELECT post_id FROM comments WHERE id = %s", (parent_id,))
            parent = cursor.fetchone()
            if parent is None or parent[0] != post_id:
                raise ValueError('Parent comment not found on this post')

        cursor.execute(
            "INSERT INTO comments (post_id, author_id, parent_id, body) VALUES (%s, %s, %s, %s)",
            (post_id, author_id, parent_id, body)
        )
        comment_id = cursor.lastrowid
        conn.commit()

        cursor.execute(
            f"SELECT {COMMENT_COLUMNS} FROM comments JOIN users ON comments.author_id = users.id WHERE comments.id = %s",
            (comment_id,)
        )
        return _as_comment(fetchone_dict(cursor))


# ---- Profiles and the social graph ----
# Public profile queries deliberately never select users.email.

def list_users(start, limit, search=''):
    query = """
        SELECT
            users.id,
            users.name,
            users.profile_picture,
            (SELECT COUNT(*) FROM posts WHERE author_id = users.id) AS postCount
        FROM users
    """
    params = []

    if search:
        query += " WHERE users.name LIKE %s "
        params.append(f"%{search}%")

    query += " ORDER BY users.name LIMIT %s OFFSET %s"
    params.extend([limit, start])
    return _fetch_all(query, tuple(params))


def get_user_profile(user_id, viewer_id=None):
    """Profile with post/follower counts and whether the viewer follows them. None if not found."""
    with closing(get_db()) as conn, closing(conn.cursor()) as cursor:
        cursor.execute("""
            SELECT
                users.id,
                users.name,
                users.bio,
                users.profile_picture,
                users.created_at,
                (SELECT COUNT(*) FROM posts WHERE author_id = users.id) AS postCount,
                (SELECT COUNT(*) FROM followers WHERE following_id = users.id) AS followersCount,
                (SELECT COUNT(*) FROM followers WHERE follower_id = users.id) AS followingCount
            FROM users
            WHERE users.id = %s
        """, (user_id,))

        user = fetchone_dict(cursor)
        if not user:
            return None

        user['is_following'] = False
        if viewer_id:
            cursor.execute(
                "SELECT 1 FROM followers WHERE follower_id = %s AND following_id = %s",
                (viewer_id, user_id)
            )
            user['is_following'] = bool(cursor.fetchone())

    return user


def update_profile(user_id, bio, profile_picture):
    with closing(get_db()) as conn, closing(conn.cursor()) as cursor:
        cursor.execute(
            "UPDATE users SET bio = %s, profile_picture = %s WHERE id = %s",
            (bio, profile_picture, user_id)
        )
        conn.commit()


def follow_user(follower_id, following_id):
    """Returns True if a new follow was created, False if it already existed."""
    with closing(get_db()) as conn, closing(conn.cursor()) as cursor:
        try:
            cursor.execute(
                "INSERT INTO followers (follower_id, following_id) VALUES (%s, %s)",
                (follower_id, following_id)
            )
        except mysql.connector.IntegrityError:
            return False
        conn.commit()
        return True


def unfollow_user(follower_id, following_id):
    with closing(get_db()) as conn, closing(conn.cursor()) as cursor:
        cursor.execute(
            "DELETE FROM followers WHERE follower_id = %s AND following_id = %s",
            (follower_id, following_id)
        )
        conn.commit()
