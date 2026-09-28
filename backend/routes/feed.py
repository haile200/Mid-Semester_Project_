from flask import Blueprint, request, jsonify, g

import services
from routes.auth import current_user_id, login_required
from utils import parse_pagination

feed_bp = Blueprint('feed', __name__, url_prefix='/api')


@feed_bp.route('/feed/following', methods=['GET'])
@login_required
def get_following_feed():
    try:
        start, limit = parse_pagination(request.args)
    except ValueError:
        return jsonify({'message': 'Invalid query parameters'}), 400
    return jsonify(services.list_following_feed(g.user_id, start, limit)), 200


@feed_bp.route('/feed', methods=['GET'])
def get_feed():
    try:
        start, limit = parse_pagination(request.args)
    except ValueError:
        return jsonify({'message': 'Invalid query parameters'}), 400
    return jsonify(services.list_feed(start, limit, current_user_id())), 200
