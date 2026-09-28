from flask import Blueprint, request, jsonify, g

import services
from routes.auth import current_user_id, login_required
from utils import parse_pagination

users_bp = Blueprint('users', __name__, url_prefix='/api')


@users_bp.route('/users', methods=['GET'])
def get_users():
    try:
        start, limit = parse_pagination(request.args)
    except ValueError:
        return jsonify({'message': 'Invalid query parameters'}), 400
    search = request.args.get('search', '').strip()
    return jsonify(services.list_users(start, limit, search)), 200


MAX_SUGGESTIONS = 20


@users_bp.route('/users/suggestions', methods=['GET'])
@login_required
def get_suggestions():
    try:
        limit = int(request.args.get('limit', 5))
    except ValueError:
        limit = 0
    if not 1 <= limit <= MAX_SUGGESTIONS:
        return jsonify({'message': f'limit must be between 1 and {MAX_SUGGESTIONS}'}), 400
    return jsonify(services.suggest_users(g.user_id, limit)), 200


@users_bp.route('/users/<int:user_id>/followers', methods=['GET'])
@users_bp.route('/users/<int:user_id>/following', methods=['GET'])
def get_follow_list(user_id):
    try:
        start, limit = parse_pagination(request.args)
    except ValueError:
        return jsonify({'message': 'Invalid query parameters'}), 400
    if not services.user_exists(user_id):
        return jsonify({'message': 'User not found'}), 404

    list_people = services.list_followers if request.path.endswith('/followers') else services.list_following
    return jsonify(list_people(user_id, start, limit)), 200


@users_bp.route('/users/<int:user_id>', methods=['GET'])
def get_user_by_id(user_id):
    user = services.get_user_profile(user_id, current_user_id())
    if not user:
        return jsonify({'message': 'User not found'}), 404
    return jsonify(user), 200


@users_bp.route('/users/profile', methods=['PUT'])
@login_required
def update_profile():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'message': 'Invalid JSON payload'}), 400

    bio = data.get('bio', '').strip()
    profile_picture = data.get('profilePicture', '').strip()
    services.update_profile(g.user_id, bio, profile_picture)
    return jsonify({'message': 'Profile updated successfully'}), 200


@users_bp.route('/follow/<int:following_id>', methods=['POST', 'DELETE'])
@login_required
def follow_user(following_id):
    if g.user_id == following_id:
        return jsonify({'message': 'You cannot follow yourself.'}), 400

    if request.method == 'POST':
        created = services.follow_user(g.user_id, following_id)
        msg = 'Successfully followed user' if created else 'Already following this user'
    else:
        services.unfollow_user(g.user_id, following_id)
        msg = 'Successfully unfollowed user'

    return jsonify({'message': msg}), 200
