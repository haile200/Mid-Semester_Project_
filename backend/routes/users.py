import mysql.connector
from flask import Blueprint, request, jsonify, session
from db import get_db
from utils import fetchall_dict, fetchone_dict

users_bp = Blueprint('users', __name__, url_prefix='/api')


@users_bp.route('/users', methods=['GET'])
def get_users():
    start = int(request.args.get('start', 0))
    limit = int(request.args.get('limit', 10))
    search = request.args.get('search', '').strip()

    query = """
        SELECT
            users.id,
            users.name,
            users.email,
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

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(query, tuple(params))
    users = fetchall_dict(cursor)
    cursor.close()
    conn.close()

    return jsonify(users), 200


@users_bp.route('/users/<int:user_id>', methods=['GET'])
def get_user_by_id(user_id):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            users.id,
            users.name,
            users.email,
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
        cursor.close()
        conn.close()
        return jsonify({'message': 'User not found'}), 404

    current_user_id = session.get('user_id')
    is_following = False

    if current_user_id:
        cursor.execute("SELECT 1 FROM followers WHERE follower_id = %s AND following_id = %s", (current_user_id, user_id))
        is_following = bool(cursor.fetchone())

    user['is_following'] = is_following

    cursor.close()
    conn.close()

    return jsonify(user), 200


@users_bp.route('/users/profile', methods=['PUT'])
def update_profile():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'message': 'Unauthorized. Please log in.'}), 401

    data = request.get_json(silent=True)
    if not data:
        return jsonify({'message': 'Invalid JSON payload'}), 400

    bio = data.get('bio', '').strip()
    profile_picture = data.get('profilePicture', '').strip()

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE users SET bio = %s, profile_picture = %s WHERE id = %s",
        (bio, profile_picture, user_id)
    )
    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({'message': 'Profile updated successfully'}), 200


@users_bp.route('/follow/<int:following_id>', methods=['POST', 'DELETE'])
def follow_user(following_id):
    follower_id = session.get('user_id')
    if not follower_id:
        return jsonify({'message': 'Unauthorized. Please log in.'}), 401

    if follower_id == following_id:
        return jsonify({'message': 'You cannot follow yourself.'}), 400

    conn = get_db()
    cursor = conn.cursor()

    if request.method == 'POST':
        try:
            cursor.execute("INSERT INTO followers (follower_id, following_id) VALUES (%s, %s)", (follower_id, following_id))
            conn.commit()
            msg = 'Successfully followed user'
        except mysql.connector.IntegrityError:
            msg = 'Already following this user'

    elif request.method == 'DELETE':
        cursor.execute("DELETE FROM followers WHERE follower_id = %s AND following_id = %s", (follower_id, following_id))
        conn.commit()
        msg = 'Successfully unfollowed user'

    cursor.close()
    conn.close()
    return jsonify({'message': msg}), 200
