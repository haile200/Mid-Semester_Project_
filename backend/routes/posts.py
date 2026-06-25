from flask import Blueprint, request, jsonify, session
from db import get_db
from utils import fetchall_dict

posts_bp = Blueprint('posts', __name__, url_prefix='/api')


@posts_bp.route('/posts', methods=['GET'])
def get_posts():
    start = int(request.args.get('start', 0))
    limit = int(request.args.get('limit', 10))
    user_id = request.args.get('userId')

    query = """
        SELECT posts.id, posts.title, posts.body, posts.image_url, posts.created_at,
               users.id AS userId,
               users.name AS author_name,
               users.profile_picture AS author_profile_picture
        FROM posts
        JOIN users ON posts.author_id = users.id
    """
    params = []

    if user_id:
        query += " WHERE posts.author_id = %s"
        params.append(int(user_id))

    query += " ORDER BY posts.id DESC LIMIT %s OFFSET %s"
    params.extend([limit, start])

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(query, tuple(params))
    posts = fetchall_dict(cursor)
    cursor.close()
    conn.close()

    return jsonify(posts), 200


@posts_bp.route('/posts', methods=['POST'])
def create_post():
    author_id = session.get('user_id')
    if not author_id:
        return jsonify({'message': 'Unauthorized. Please log in.'}), 401

    data = request.get_json(silent=True)
    if not data:
        return jsonify({'message': 'Invalid JSON payload'}), 400

    title = data.get('title', '').strip()
    body = data.get('body', '').strip()
    image_url = data.get('imageUrl', None)

    if not title or not body:
        return jsonify({'message': 'Title and body are required'}), 400

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO posts (title, body, image_url, author_id) VALUES (%s, %s, %s, %s)",
        (title, body, image_url, author_id)
    )
    conn.commit()
    post_id = cursor.lastrowid
    cursor.close()
    conn.close()

    return jsonify({'message': 'Post created successfully', 'postId': post_id}), 201
