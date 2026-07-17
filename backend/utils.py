import re

import bcrypt

SESSION_COOKIE_NAME = 'session_token'

EMAIL_RE = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')


def is_valid_email(email):
    return bool(email) and len(email) <= 255 and bool(EMAIL_RE.match(email))


def hash_password(plain_password):
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(plain_password.encode('utf-8'), salt).decode('utf-8')


def verify_password(plain_password, hashed_password):
    if not hashed_password:
        return False
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except ValueError:
        return False


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
