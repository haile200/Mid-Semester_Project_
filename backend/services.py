import hashlib
import random
import secrets
from contextlib import closing
from datetime import datetime, timedelta

import mysql.connector

from brain import PostNotes, get_brain
from db import get_db
from utils import (
    clean_comment_body,
    clean_correction_text,
    clean_post_notes,
    clean_report,
    fetchall_dict,
    fetchone_dict,
    hash_password,
    html_to_text,
    sanitize_post_html,
    unusable_password_hash,
    verify_password,
)


class ContentRejected(ValueError):
    """The brain refused to let the text be published."""


class ModerationUnavailable(Exception):
    """The moderation check itself failed. Only strict mode, used by the bot worker, raises this."""


class AccountBanned(Exception):
    """Correct credentials, but the account is banned."""


class AlreadyReported(Exception):
    """This user has already reported this post."""


def _ensure_publishable(text, strict=False):
    # Runs before any database connection opens, so a slow check never holds one.
    # Strict mode gets no fallback: a failed check stops the publish instead of using the word list.
    try:
        result = get_brain(fallback=not strict).check_toxicity(text)
    except Exception as error:
        raise ModerationUnavailable(str(error)) from error
    if not result.allowed:
        reason = result.reason or 'Rejected by moderation'
        raise ContentRejected(f'Not published: {reason[0].lower()}{reason[1:]}')

# The single %s is the viewer's id (or NULL for a visitor), so every query using this passes it first.
POST_COLUMNS = """
    posts.id, posts.title, posts.body, posts.image_url, posts.created_at,
    users.id AS userId,
    users.name AS author_name,
    users.profile_picture AS author_profile_picture,
    (SELECT COUNT(*) FROM likes WHERE likes.post_id = posts.id) AS likeCount,
    EXISTS (SELECT 1 FROM likes WHERE likes.post_id = posts.id AND likes.user_id = %s) AS likedByMe
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


def upsert_bot(name, email, bio, personality):
    """Create or update a bot account keyed by email. Returns (user_id, created).

    Raises ValueError if the email belongs to a human account.
    """
    with closing(get_db()) as conn, closing(conn.cursor()) as cursor:
        cursor.execute("SELECT id, is_bot FROM users WHERE email = %s", (email,))
        existing = cursor.fetchone()

        if existing and not existing[1]:
            raise ValueError(f'{email} belongs to a human account')

        if existing:
            cursor.execute(
                "UPDATE users SET name = %s, bio = %s, personality = %s WHERE id = %s",
                (name, bio, personality, existing[0])
            )
            conn.commit()
            return existing[0], False

        cursor.execute(
            "INSERT INTO users (name, email, password, bio, is_bot, personality) VALUES (%s, %s, %s, %s, 1, %s)",
            (name, email, unusable_password_hash(), bio, personality)
        )
        conn.commit()
        return cursor.lastrowid, True


def authenticate(email, password):
    """Check credentials. Returns the user dict on success, None otherwise.

    Raises AccountBanned only after the password matched, so a ban is never revealed to a guesser.
    """
    with closing(get_db()) as conn, closing(conn.cursor()) as cursor:
        cursor.execute(
            "SELECT id, name, email, password, profile_picture, is_admin, banned_at FROM users WHERE email = %s",
            (email,)
        )
        user = fetchone_dict(cursor)

    if not user or not verify_password(password, user['password']):
        return None
    if user['banned_at'] is not None:
        raise AccountBanned()

    return {
        'id': user['id'],
        'name': user['name'],
        'email': user['email'],
        'profile_picture': user['profile_picture'],
        'is_admin': bool(user['is_admin']),
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
    """Resolve a session token to its user dict, or None if invalid or the account is banned."""
    if not token:
        return None

    with closing(get_db()) as conn, closing(conn.cursor()) as cursor:
        cursor.execute(
            """
            SELECT users.id, users.name, users.email, users.profile_picture, users.is_admin
            FROM sessions
            JOIN users ON sessions.user_id = users.id
            WHERE sessions.token = %s AND users.banned_at IS NULL
            """,
            (token,)
        )
        user = fetchone_dict(cursor)

    if user:
        user['is_admin'] = bool(user['is_admin'])
    return user


def delete_session(token):
    """Destroy a server-side session. Safe to call with a missing/unknown token."""
    if not token:
        return

    with closing(get_db()) as conn, closing(conn.cursor()) as cursor:
        cursor.execute("DELETE FROM sessions WHERE token = %s", (token,))
        conn.commit()


# ---- Password reset ----

RESET_LINK_MINUTES = 30


class InvalidResetToken(Exception):
    pass


def _reset_token_hash(token):
    # A fast hash is enough here: the token is 256 random bits, so it cannot be guessed the way a password can.
    return hashlib.sha256(token.encode('utf-8')).hexdigest()


def create_password_reset(email):
    """Returns (name, token) for a new reset link, or None if the email cannot reset a password.

    Bots and banned accounts cannot. A new link replaces any earlier one for the same account.
    """
    with closing(get_db()) as conn, closing(conn.cursor()) as cursor:
        cursor.execute(
            "SELECT id, name FROM users WHERE email = %s AND is_bot = 0 AND banned_at IS NULL",
            (email,)
        )
        user = cursor.fetchone()
        if user is None:
            return None

        token = secrets.token_urlsafe(32)
        cursor.execute("DELETE FROM password_resets WHERE user_id = %s", (user[0],))
        cursor.execute(
            "INSERT INTO password_resets (token_hash, user_id) VALUES (%s, %s)",
            (_reset_token_hash(token), user[0])
        )
        conn.commit()
    return user[1], token


def reset_password(token, new_password):
    """Sets the new password, uses up the link and logs the account out everywhere.

    Raises InvalidResetToken for an unknown, used or expired token, or a banned account.
    """
    if not isinstance(token, str) or not token:
        raise InvalidResetToken()
    token_hash = _reset_token_hash(token)
    oldest_allowed = database_now() - timedelta(minutes=RESET_LINK_MINUTES)

    with closing(get_db()) as conn, closing(conn.cursor()) as cursor:
        cursor.execute(
            """
            SELECT password_resets.user_id
            FROM password_resets
            JOIN users ON users.id = password_resets.user_id
            WHERE password_resets.token_hash = %s
              AND password_resets.created_at >= %s
              AND users.banned_at IS NULL
            """,
            (token_hash, oldest_allowed)
        )
        row = cursor.fetchone()
        if row is None:
            raise InvalidResetToken()

        # Claiming the link by deleting it means two simultaneous requests cannot both use it.
        cursor.execute("DELETE FROM password_resets WHERE token_hash = %s", (token_hash,))
        if cursor.rowcount != 1:
            raise InvalidResetToken()

        cursor.execute("UPDATE users SET password = %s WHERE id = %s", (hash_password(new_password), row[0]))
        cursor.execute("DELETE FROM sessions WHERE user_id = %s", (row[0],))
        conn.commit()


# ---- Posts and feeds ----

def _post_rows(query, params):
    # EXISTS comes back as 0/1 from the database; the API promises a real boolean.
    rows = _fetch_all(query, params)
    for row in rows:
        row['likedByMe'] = bool(row['likedByMe'])
    return rows


def list_feed(start, limit, viewer_id=None):
    return _post_rows(
        f"""
        SELECT {POST_COLUMNS}
        FROM posts
        JOIN users ON posts.author_id = users.id
        ORDER BY posts.id DESC LIMIT %s OFFSET %s
        """,
        (viewer_id, limit, start)
    )


def list_following_feed(viewer_id, start, limit):
    return _post_rows(
        f"""
        SELECT {POST_COLUMNS}
        FROM posts
        JOIN users ON posts.author_id = users.id
        JOIN followers ON posts.author_id = followers.following_id
        WHERE followers.follower_id = %s
        ORDER BY posts.id DESC LIMIT %s OFFSET %s
        """,
        (viewer_id, viewer_id, limit, start)
    )


def list_posts(start, limit, author_id=None, viewer_id=None):
    query = f"SELECT {POST_COLUMNS} FROM posts JOIN users ON posts.author_id = users.id"
    params = [viewer_id]

    if author_id is not None:
        query += " WHERE posts.author_id = %s"
        params.append(author_id)

    query += " ORDER BY posts.id DESC LIMIT %s OFFSET %s"
    params.extend([limit, start])
    return _post_rows(query, tuple(params))


def create_post(author_id, title, body, image_url=None, strict=False):
    """Sanitize and store a post.

    Raises ValueError if title or body is empty after cleaning, ContentRejected if the brain blocks it,
    and in strict mode ModerationUnavailable if the check cannot run.
    """
    title = (title or '').strip()
    body = sanitize_post_html(body or '').strip()
    if not title or not body:
        raise ValueError('Title and body are required')
    _ensure_publishable(f'{title}\n{html_to_text(body)}', strict)

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


def create_comment(post_id, author_id, body, parent_id=None, strict=False):
    """Store a comment or reply and return it.

    Raises ValueError for invalid text or a parent outside this post, ContentRejected if the brain
    blocks it, LookupError if the post is missing, and in strict mode ModerationUnavailable if the
    check cannot run.
    """
    body = clean_comment_body(body)
    _ensure_publishable(body, strict)

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


# ---- Writing help ----

def correct_text(text):
    """Returns the text with spelling and capitalization fixed. Raises ValueError for invalid input."""
    return get_brain().suggest_correction(clean_correction_text(text))


def suggest_post(style, grade, title, body):
    """A draft title and body built from what the author has so far. Raises ValueError for invalid input."""
    notes = PostNotes(*clean_post_notes(style, grade, title, body))
    # A fresh seed per request, so asking again gives a different draft.
    return get_brain().suggest_post(notes, random.randrange(1_000_000))


def comment_ideas(post_id):
    """Three comment ideas for the post, or None if it does not exist."""
    with closing(get_db()) as conn, closing(conn.cursor()) as cursor:
        cursor.execute("SELECT title, body FROM posts WHERE id = %s", (post_id,))
        post = cursor.fetchone()
    # The model is called after the connection is closed, so a slow answer never holds one.
    if post is None:
        return None
    return get_brain().propose_comments(post[0], post[1])


# ---- Moderation ----

def create_report(post_id, reporter_id, reason, note):
    """Store a report and return its id.

    Raises ValueError for bad input or reporting your own post, LookupError if the post is missing,
    and AlreadyReported for a second report by the same user.
    """
    reason, note = clean_report(reason, note)

    with closing(get_db()) as conn, closing(conn.cursor()) as cursor:
        cursor.execute("SELECT author_id FROM posts WHERE id = %s", (post_id,))
        post = cursor.fetchone()
        if post is None:
            raise LookupError('Post not found')
        if post[0] == reporter_id:
            raise ValueError('You cannot report your own post')

        cursor.execute("SELECT 1 FROM reports WHERE post_id = %s AND reporter_id = %s", (post_id, reporter_id))
        if cursor.fetchone():
            raise AlreadyReported('You already reported this post')

        cursor.execute(
            "INSERT INTO reports (post_id, reporter_id, reason, note) VALUES (%s, %s, %s, %s)",
            (post_id, reporter_id, reason, note)
        )
        conn.commit()
        return cursor.lastrowid


def list_open_reports():
    """Open reports grouped by post, most-reported first."""
    rows = _fetch_all(
        """
        SELECT
            reports.id, reports.post_id, reports.reason, reports.note, reports.created_at,
            reporters.name AS reporter_name,
            posts.title, posts.body, posts.created_at AS post_created_at,
            authors.id AS author_id, authors.name AS author_name,
            authors.is_bot AS author_is_bot, authors.is_admin AS author_is_admin,
            authors.banned_at AS author_banned_at
        FROM reports
        JOIN posts ON reports.post_id = posts.id
        JOIN users AS authors ON posts.author_id = authors.id
        JOIN users AS reporters ON reports.reporter_id = reporters.id
        WHERE reports.status = 'open'
        ORDER BY reports.created_at, reports.id
        """,
        ()
    )

    groups = {}
    for row in rows:
        group = groups.setdefault(row['post_id'], {
            'post': {
                'id': row['post_id'],
                'title': row['title'],
                'body': row['body'],
                'created_at': row['post_created_at'],
                'author': {
                    'id': row['author_id'],
                    'name': row['author_name'],
                    'is_bot': bool(row['author_is_bot']),
                    'is_admin': bool(row['author_is_admin']),
                    'is_banned': row['author_banned_at'] is not None,
                },
            },
            'reports': [],
        })
        group['reports'].append({
            'id': row['id'],
            'reason': row['reason'],
            'note': row['note'],
            'reporter_name': row['reporter_name'],
            'created_at': row['created_at'],
        })

    return sorted(groups.values(), key=lambda group: -len(group['reports']))


def dismiss_reports(post_id, moderator_id):
    """Mark a post's open reports dismissed. Returns how many, or None if the post does not exist."""
    with closing(get_db()) as conn, closing(conn.cursor()) as cursor:
        cursor.execute("SELECT 1 FROM posts WHERE id = %s", (post_id,))
        if cursor.fetchone() is None:
            return None
        cursor.execute(
            """
            UPDATE reports SET status = 'dismissed', reviewed_by = %s, reviewed_at = CURRENT_TIMESTAMP
            WHERE post_id = %s AND status = 'open'
            """,
            (moderator_id, post_id)
        )
        conn.commit()
        return cursor.rowcount


def delete_post(post_id):
    """Delete a post; its comments and reports go with it. Returns False if it did not exist."""
    with closing(get_db()) as conn, closing(conn.cursor()) as cursor:
        cursor.execute("DELETE FROM posts WHERE id = %s", (post_id,))
        conn.commit()
        return cursor.rowcount > 0


def _moderation_target(cursor, user_id):
    cursor.execute("SELECT id, name, is_admin, banned_at FROM users WHERE id = %s", (user_id,))
    user = fetchone_dict(cursor)
    if user is None:
        raise LookupError('User not found')
    return user


def ban_user(user_id, admin_id):
    """Ban a user and end all their sessions. Safe to repeat.

    Raises LookupError if the user is missing, ValueError for yourself or another admin.
    """
    if user_id == admin_id:
        raise ValueError('You cannot ban yourself')

    with closing(get_db()) as conn, closing(conn.cursor()) as cursor:
        user = _moderation_target(cursor, user_id)
        if user['is_admin']:
            raise ValueError('Admins cannot be banned. Revoke their admin rights first.')
        if user['banned_at'] is None:
            cursor.execute("UPDATE users SET banned_at = CURRENT_TIMESTAMP WHERE id = %s", (user_id,))
        cursor.execute("DELETE FROM sessions WHERE user_id = %s", (user_id,))
        conn.commit()
    return {'id': user['id'], 'name': user['name'], 'banned': True}


def unban_user(user_id):
    """Lift a ban. Safe to repeat. Raises LookupError if the user is missing."""
    with closing(get_db()) as conn, closing(conn.cursor()) as cursor:
        user = _moderation_target(cursor, user_id)
        cursor.execute("UPDATE users SET banned_at = NULL WHERE id = %s", (user_id,))
        conn.commit()
    return {'id': user['id'], 'name': user['name'], 'banned': False}


def set_admin(email, is_admin):
    """Grant or revoke admin rights by email and return the user's name.

    Raises LookupError for an unknown email, ValueError when granting to a bot or a banned user.
    """
    with closing(get_db()) as conn, closing(conn.cursor()) as cursor:
        cursor.execute("SELECT id, name, is_bot, banned_at FROM users WHERE email = %s", (email,))
        user = fetchone_dict(cursor)
        if user is None:
            raise LookupError(f'No user with email {email}')
        if is_admin and user['is_bot']:
            raise ValueError('Bots cannot be admins')
        if is_admin and user['banned_at'] is not None:
            raise ValueError('Banned users cannot be admins')
        cursor.execute("UPDATE users SET is_admin = %s WHERE id = %s", (1 if is_admin else 0, user['id']))
        conn.commit()
    return user['name']


def list_admins():
    return _fetch_all("SELECT id, name, email FROM users WHERE is_admin = 1 ORDER BY id", ())


# ---- Bot worker ----

def _as_datetime(value):
    # MySQL returns datetime objects; SQLite, used by the integration tests, returns text.
    if value is None or isinstance(value, datetime):
        return value
    return datetime.fromisoformat(str(value))


def database_now():
    """The database's own clock, so comparisons with created_at never mix two clocks."""
    with closing(get_db()) as conn, closing(conn.cursor()) as cursor:
        cursor.execute("SELECT CURRENT_TIMESTAMP")
        return _as_datetime(cursor.fetchone()[0])


def list_bot_activity(since):
    """Every bot with its last action time and the number of posts, comments and likes since `since`."""
    rows = _fetch_all(
        """
        SELECT
            users.id,
            users.name,
            users.personality,
            (SELECT MAX(created_at) FROM posts WHERE author_id = users.id) AS last_post_at,
            (SELECT MAX(created_at) FROM comments WHERE author_id = users.id) AS last_comment_at,
            (SELECT MAX(created_at) FROM likes WHERE user_id = users.id) AS last_like_at,
            (SELECT COUNT(*) FROM posts WHERE author_id = users.id AND created_at >= %s)
                + (SELECT COUNT(*) FROM comments WHERE author_id = users.id AND created_at >= %s)
                + (SELECT COUNT(*) FROM likes WHERE user_id = users.id AND created_at >= %s) AS recent_actions
        FROM users
        WHERE users.is_bot = 1 AND users.banned_at IS NULL
        ORDER BY users.id
        """,
        (since, since, since)
    )
    for row in rows:
        times = [_as_datetime(row.pop(key)) for key in ('last_post_at', 'last_comment_at', 'last_like_at')]
        times = [t for t in times if t]
        row['last_action_at'] = max(times) if times else None
    return rows


def list_like_targets(bot_id, limit):
    """Recent posts by others that the bot has not liked yet."""
    return _fetch_all(
        """
        SELECT posts.id, posts.title
        FROM posts
        WHERE posts.author_id <> %s
          AND NOT EXISTS (SELECT 1 FROM likes WHERE likes.post_id = posts.id AND likes.user_id = %s)
        ORDER BY posts.id DESC
        LIMIT %s
        """,
        (bot_id, bot_id, limit)
    )


def list_comment_targets(bot_id, limit):
    """Recent posts by others that the bot has not commented on yet."""
    return _fetch_all(
        """
        SELECT posts.id, posts.title, posts.body
        FROM posts
        WHERE posts.author_id <> %s
          AND NOT EXISTS (
              SELECT 1 FROM comments
              WHERE comments.post_id = posts.id AND comments.author_id = %s AND comments.parent_id IS NULL
          )
        ORDER BY posts.id DESC
        LIMIT %s
        """,
        (bot_id, bot_id, limit)
    )


def list_reply_targets(bot_id, limit):
    """Recent comments by others that the bot has not replied to yet."""
    return _fetch_all(
        """
        SELECT comments.id, comments.post_id, comments.body
        FROM comments
        WHERE comments.author_id <> %s
          AND NOT EXISTS (
              SELECT 1 FROM comments AS replies
              WHERE replies.parent_id = comments.id AND replies.author_id = %s
          )
        ORDER BY comments.id DESC
        LIMIT %s
        """,
        (bot_id, bot_id, limit)
    )


def comment_depth(comment_id):
    """0 for a top-level comment, 1 for a reply to it, and so on."""
    depth = 0
    with closing(get_db()) as conn, closing(conn.cursor()) as cursor:
        while True:
            cursor.execute("SELECT parent_id FROM comments WHERE id = %s", (comment_id,))
            parent_id = cursor.fetchone()[0]
            if parent_id is None:
                return depth
            depth += 1
            comment_id = parent_id


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


def _like_count(cursor, post_id):
    cursor.execute("SELECT COUNT(*) FROM likes WHERE post_id = %s", (post_id,))
    return cursor.fetchone()[0]


def like_post(user_id, post_id):
    """Like a post; safe to repeat. Returns the post's like count. Raises LookupError if it is missing."""
    with closing(get_db()) as conn, closing(conn.cursor()) as cursor:
        cursor.execute("SELECT 1 FROM posts WHERE id = %s", (post_id,))
        if cursor.fetchone() is None:
            raise LookupError('Post not found')
        cursor.execute("SELECT 1 FROM likes WHERE user_id = %s AND post_id = %s", (user_id, post_id))
        if cursor.fetchone() is None:
            cursor.execute("INSERT INTO likes (user_id, post_id) VALUES (%s, %s)", (user_id, post_id))
            conn.commit()
        return _like_count(cursor, post_id)


def unlike_post(user_id, post_id):
    """Remove a like; safe to repeat. Returns the post's like count. Raises LookupError if it is missing."""
    with closing(get_db()) as conn, closing(conn.cursor()) as cursor:
        cursor.execute("SELECT 1 FROM posts WHERE id = %s", (post_id,))
        if cursor.fetchone() is None:
            raise LookupError('Post not found')
        cursor.execute("DELETE FROM likes WHERE user_id = %s AND post_id = %s", (user_id, post_id))
        conn.commit()
        return _like_count(cursor, post_id)


def user_exists(user_id):
    with closing(get_db()) as conn, closing(conn.cursor()) as cursor:
        cursor.execute("SELECT 1 FROM users WHERE id = %s", (user_id,))
        return cursor.fetchone() is not None


def _people(query, params):
    rows = _fetch_all(query, params)
    for row in rows:
        row['is_bot'] = bool(row['is_bot'])
    return rows


def list_followers(user_id, start, limit):
    """People who follow the user, newest first."""
    return _people(
        """
        SELECT users.id, users.name, users.profile_picture, users.is_bot
        FROM followers JOIN users ON users.id = followers.follower_id
        WHERE followers.following_id = %s
        ORDER BY followers.created_at DESC, users.id
        LIMIT %s OFFSET %s
        """,
        (user_id, limit, start)
    )


def list_following(user_id, start, limit):
    """People the user follows, newest first."""
    return _people(
        """
        SELECT users.id, users.name, users.profile_picture, users.is_bot
        FROM followers JOIN users ON users.id = followers.following_id
        WHERE followers.follower_id = %s
        ORDER BY followers.created_at DESC, users.id
        LIMIT %s OFFSET %s
        """,
        (user_id, limit, start)
    )


def suggest_users(viewer_id, limit):
    """People the viewer may know: ranked by how many of the viewer's follows also follow them,
    then by popularity. Never the viewer, people they already follow, or banned accounts."""
    return _people(
        """
        SELECT
            candidate.id, candidate.name, candidate.profile_picture, candidate.is_bot,
            COUNT(DISTINCT mine.following_id) AS mutualCount,
            (SELECT COUNT(*) FROM followers AS fans WHERE fans.following_id = candidate.id) AS followersCount
        FROM users AS candidate
        LEFT JOIN followers AS theirs ON theirs.following_id = candidate.id
        LEFT JOIN followers AS mine ON mine.follower_id = %s AND mine.following_id = theirs.follower_id
        WHERE candidate.id <> %s
          AND candidate.banned_at IS NULL
          AND NOT EXISTS (
              SELECT 1 FROM followers AS already
              WHERE already.follower_id = %s AND already.following_id = candidate.id
          )
        GROUP BY candidate.id, candidate.name, candidate.profile_picture, candidate.is_bot
        ORDER BY mutualCount DESC, followersCount DESC, candidate.id
        LIMIT %s
        """,
        (viewer_id, viewer_id, viewer_id, limit)
    )


def unfollow_user(follower_id, following_id):
    with closing(get_db()) as conn, closing(conn.cursor()) as cursor:
        cursor.execute(
            "DELETE FROM followers WHERE follower_id = %s AND following_id = %s",
            (follower_id, following_id)
        )
        conn.commit()
