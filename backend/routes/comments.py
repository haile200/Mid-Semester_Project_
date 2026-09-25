from flask import Blueprint, request, jsonify, g

import services
from routes.auth import login_required
from utils import parse_pagination

comments_bp = Blueprint('comments', __name__, url_prefix='/api')


@comments_bp.route('/posts/<int:post_id>/comments', methods=['GET'])
def list_comments(post_id):
    try:
        start, limit = parse_pagination(request.args)
    except ValueError:
        return jsonify({'message': 'Invalid query parameters'}), 400

    if not services.post_exists(post_id):
        return jsonify({'message': 'Post not found'}), 404

    return jsonify(services.list_comments(post_id, start, limit)), 200


@comments_bp.route('/posts/<int:post_id>/comments', methods=['POST'])
@login_required
def create_comment(post_id):
    data = request.get_json(silent=True)
    if not data or not isinstance(data, dict):
        return jsonify({'message': 'Invalid JSON payload'}), 400

    parent_id = data.get('parent_id')
    # bool is a subclass of int in Python, so True would otherwise pass as comment id 1.
    if parent_id is not None and (not isinstance(parent_id, int) or isinstance(parent_id, bool)):
        return jsonify({'message': 'Invalid input types'}), 400

    try:
        comment = services.create_comment(post_id, g.user_id, data.get('body'), parent_id)
    except LookupError as error:
        return jsonify({'message': str(error)}), 404
    except ValueError as error:
        return jsonify({'message': str(error)}), 400

    return jsonify({'message': 'Comment created successfully', 'comment': comment}), 201
