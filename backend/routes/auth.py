from functools import wraps
from flask import Blueprint, request, jsonify, g

import services
from config import Config
from utils import SESSION_COOKIE_NAME, is_valid_email, session_cookie_flags

auth_bp = Blueprint('auth', __name__, url_prefix='/api')


def current_user():
    token = request.cookies.get(SESSION_COOKIE_NAME)
    return services.get_user_by_session(token)


def current_user_id():
    user = current_user()
    return user['id'] if user else None


def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        user = current_user()
        if not user:
            return jsonify({'message': 'Unauthorized. Please log in.'}), 401
        g.user = user
        g.user_id = user['id']
        return view(*args, **kwargs)
    return wrapped_view


def admin_required(view):
    """401 when not logged in, 403 when logged in without admin rights."""
    @wraps(view)
    @login_required
    def wrapped_view(*args, **kwargs):
        if not g.user.get('is_admin'):
            return jsonify({'message': 'Admin access required'}), 403
        return view(*args, **kwargs)
    return wrapped_view


@auth_bp.route('/signup', methods=['POST'])
def signup():
    data = request.get_json(silent=True)  # Use silent=True to avoid exceptions on invalid JSON
    if not data:
        return jsonify({'message': 'Invalid JSON payload'}), 400

    name = data.get('name')
    email = data.get('email')
    plain_pass = data.get('password')

    if not all(isinstance(field, str) for field in (name, email, plain_pass) if field is not None):
        return jsonify({'message': 'Invalid input types'}), 400

    name = (name or '').strip()
    email = (email or '').strip()

    if not name or not email or not plain_pass:
        return jsonify({'message': 'Name, email, and password are required'}), 400

    if len(name) > 255:
        return jsonify({'message': 'Name is too long'}), 400

    if not is_valid_email(email):
        return jsonify({'message': 'Invalid email address'}), 400

    if len(plain_pass) < 8 or len(plain_pass) > 72:
        return jsonify({'message': 'Password must be between 8 and 72 characters'}), 400

    user_id = services.create_user(name, email, plain_pass)
    if user_id is None:
        return jsonify({'message': 'Email already registered'}), 400

    return jsonify({'message': 'Registered successfully'}), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'message': 'Invalid JSON payload'}), 400

    email = data.get('email')
    plain_pass = data.get('password')

    if not all(isinstance(field, str) for field in (email, plain_pass) if field is not None):
        return jsonify({'message': 'Invalid input types'}), 400

    email = (email or '').strip()

    if not email or not plain_pass:
        return jsonify({'message': 'Email and password are required'}), 400

    try:
        user = services.authenticate(email, plain_pass)
    except services.AccountBanned:
        return jsonify({'message': 'This account has been banned'}), 403
    if not user:
        return jsonify({'message': 'Invalid credentials'}), 401

    token = services.create_session(user['id'])

    response = jsonify({'message': 'Login successful', 'user': user})
    response.set_cookie(
        SESSION_COOKIE_NAME, token,
        **session_cookie_flags(Config.SESSION_SECURE)
    )
    return response, 200


@auth_bp.route('/logout', methods=['POST'])
def logout():
    services.delete_session(request.cookies.get(SESSION_COOKIE_NAME))
    response = jsonify({'message': 'Logged out successfully'})
    response.delete_cookie(SESSION_COOKIE_NAME)
    return response, 200


@auth_bp.route('/auth/me', methods=['GET'])
@login_required
def get_current_user():
    return jsonify({'user': g.user}), 200
