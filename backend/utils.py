import html
import re
import secrets

import bcrypt
import nh3

SESSION_COOKIE_NAME = 'session_token'

# Must cover every format the Quill toolbar in NewPost.jsx can emit.
POST_ALLOWED_TAGS = {'p', 'br', 'strong', 'em', 'u', 'a'}
POST_ALLOWED_ATTRIBUTES = {'a': {'href', 'target'}}
POST_URL_SCHEMES = {'http', 'https', 'mailto'}

EMAIL_RE = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')


def is_valid_email(email):
    return bool(email) and len(email) <= 255 and bool(EMAIL_RE.match(email))


MAX_PAGE_SIZE = 50


def parse_pagination(args):
    """Returns (start, limit) with limit capped at MAX_PAGE_SIZE. Raises ValueError on bad input."""
    start = int(args.get('start', 0))
    limit = int(args.get('limit', 10))
    if start < 0 or limit < 1:
        raise ValueError('start must be >= 0 and limit must be >= 1')
    return start, min(limit, MAX_PAGE_SIZE)


MAX_COMMENT_LENGTH = 1000


def clean_comment_body(body):
    """Returns the trimmed comment text. Raises ValueError if it is not text, empty, or too long."""
    if body is None:
        body = ''
    if not isinstance(body, str):
        raise ValueError('Invalid input types')
    body = body.strip()
    if not body:
        raise ValueError('Comment cannot be empty')
    if len(body) > MAX_COMMENT_LENGTH:
        raise ValueError(f'Comment must be {MAX_COMMENT_LENGTH} characters or fewer')
    return body


def hash_password(plain_password):
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(plain_password.encode('utf-8'), salt).decode('utf-8')


def unusable_password_hash():
    # bcrypt's slowness protects guessable passwords; this secret is 256 random bits that are
    # never stored, so the minimum cost is enough and keeps seeding fast.
    secret = secrets.token_urlsafe(32).encode('utf-8')
    return bcrypt.hashpw(secret, bcrypt.gensalt(rounds=4)).decode('utf-8')


def verify_password(plain_password, hashed_password):
    if not hashed_password:
        return False
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except ValueError:
        return False


def sanitize_post_html(html):
    return nh3.clean(
        html,
        tags=POST_ALLOWED_TAGS,
        attributes=POST_ALLOWED_ATTRIBUTES,
        url_schemes=POST_URL_SCHEMES,
        link_rel='noopener noreferrer',
    )


BLOCK_TAG_RE = re.compile(r'</?(?:p|br|div|li|ul|ol|h[1-6])\b[^>]*>', re.IGNORECASE)
TAG_RE = re.compile(r'<[^>]+>')


def html_to_text(markup):
    # Block tags become spaces; inline tags vanish so a word split by <strong> reads as one word.
    text = TAG_RE.sub('', BLOCK_TAG_RE.sub(' ', markup))
    return ' '.join(html.unescape(text).split())


def session_cookie_flags(secure):
    if secure:
        return {'httponly': True, 'samesite': 'None', 'secure': True}
    return {'httponly': True, 'samesite': 'Lax', 'secure': False}


def fetchall_dict(cursor):
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def fetchone_dict(cursor):
    columns = [col[0] for col in cursor.description]
    row = cursor.fetchone()
    return dict(zip(columns, row)) if row else None
