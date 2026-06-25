import bcrypt
from flask import Blueprint, request, jsonify, session
from db import get_db
from utils import fetchone_dict

auth_bp = Blueprint('auth', __name__, url_prefix='/api')


@auth_bp.route('/signup', methods=['POST'])
def signup():
    data = request.get_json(silent=True)  # Use silent=True to avoid exceptions on invalid JSON
    if not data:
        return jsonify({'message': 'Invalid JSON payload'}), 400

    name = data.get('name', '').strip()
    email = data.get('email', '').strip()
    plain_pass = data.get('password')

    if not name or not email or not plain_pass:
        return jsonify({'message': 'Name, email, and password are required'}), 400

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
    if fetchone_dict(cursor):
        cursor.close()
        conn.close()
        return jsonify({'message': 'Email already registered'}), 400

    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(plain_pass.encode('utf-8'), salt).decode('utf-8')

    cursor.execute(
        "INSERT INTO users (name, email, password) VALUES (%s, %s, %s)",
        (name, email, hashed_password)
    )
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({'message': 'Registered successfully'}), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'message': 'Invalid JSON payload'}), 400

    email = data.get('email', '').strip()
    plain_pass = data.get('password')

    if not email or not plain_pass:
        return jsonify({'message': 'Email and password are required'}), 400

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT id, name, email, password, profile_picture FROM users WHERE email = %s", (email,))
    user = fetchone_dict(cursor)

    cursor.close()
    conn.close()

    if not user or not bcrypt.checkpw(plain_pass.encode('utf-8'), user['password'].encode('utf-8')):
        return jsonify({'message': 'Invalid credentials'}), 401

    session['user_id'] = user['id']

    return jsonify({
        'message': 'Login successful',
        'user': {
            'id': user['id'],
            'name': user['name'],
            'email': user['email'],
            'profile_picture': user['profile_picture']
        }
    }), 200


@auth_bp.route('/logout', methods=['POST'])
def logout():
    session.pop('user_id', None)
    return jsonify({'message': 'Logged out successfully'}), 200
