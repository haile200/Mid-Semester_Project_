from flask import Blueprint, request, jsonify
from db import get_db
from utils import fetchall_dict
from routes.auth import current_user_id

feed_bp = Blueprint('feed', __name__, url_prefix='/api')


@feed_bp.route('/feed/following', methods=['GET'])
def get_following_feed():
    viewer_id = current_user_id()
    if not viewer_id:
        return jsonify({'message': 'Unauthorized. Please log in.'}), 401

    start = int(request.args.get('start', 0))
    limit = int(request.args.get('limit', 10))

    query = """
        SELECT posts.id, posts.title, posts.body, posts.image_url, posts.created_at,
               users.id AS userId,
               users.name AS author_name,
               users.profile_picture AS author_profile_picture
        FROM posts
        JOIN users ON posts.author_id = users.id
        JOIN followers ON posts.author_id = followers.following_id
        WHERE followers.follower_id = %s
        ORDER BY posts.id DESC LIMIT %s OFFSET %s
    """

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(query, (viewer_id, limit, start))
    posts = fetchall_dict(cursor)
    cursor.close()
    conn.close()

    return jsonify(posts), 200


@feed_bp.route('/feed', methods=['GET'])
def get_feed():
    start = int(request.args.get('start', 0))
    limit = int(request.args.get('limit', 10))

    conn = get_db()
    cursor = conn.cursor()

    query = """
        SELECT posts.id, posts.title, posts.body, posts.image_url, posts.created_at,
               users.id AS userId,
               users.name AS author_name,
               users.profile_picture AS author_profile_picture
        FROM posts
        JOIN users ON posts.author_id = users.id
        ORDER BY posts.id DESC LIMIT %s OFFSET %s
    """

    cursor.execute(query, (limit, start))
    posts = fetchall_dict(cursor)

    cursor.close()
    conn.close()
    return jsonify(posts), 200
