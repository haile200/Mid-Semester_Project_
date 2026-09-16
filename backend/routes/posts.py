from flask import Blueprint, request, jsonify, g

import services
from routes.auth import login_required
from utils import parse_pagination

posts_bp = Blueprint('posts', __name__, url_prefix='/api')


@posts_bp.route('/posts', methods=['GET'])
def get_posts():
    try:
        start, limit = parse_pagination(request.args)
        user_id = request.args.get('userId')
        author_id = int(user_id) if user_id else None
    except ValueError:
        return jsonify({'message': 'Invalid query parameters'}), 400
    return jsonify(services.list_posts(start, limit, author_id)), 200


@posts_bp.route('/posts', methods=['POST'])
@login_required
def create_post():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'message': 'Invalid JSON payload'}), 400

    try:
        post_id = services.create_post(
            g.user_id, data.get('title'), data.get('body'), data.get('imageUrl')
        )
    except ValueError as error:
        return jsonify({'message': str(error)}), 400

    return jsonify({'message': 'Post created successfully', 'postId': post_id}), 201
