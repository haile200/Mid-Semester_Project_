from flask import Blueprint, request, jsonify, g

import services
from routes.auth import admin_required, login_required

moderation_bp = Blueprint('moderation', __name__, url_prefix='/api')


def _json_object():
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) and data else None


@moderation_bp.route('/posts/<int:post_id>/reports', methods=['POST'])
@login_required
def report_post(post_id):
    data = _json_object()
    if data is None:
        return jsonify({'message': 'Invalid JSON payload'}), 400

    try:
        report_id = services.create_report(post_id, g.user_id, data.get('reason'), data.get('note'))
    except LookupError as error:
        return jsonify({'message': str(error)}), 404
    except services.AlreadyReported as error:
        return jsonify({'message': str(error)}), 409
    except ValueError as error:
        return jsonify({'message': str(error)}), 400

    return jsonify({'message': 'Report received', 'reportId': report_id}), 201


@moderation_bp.route('/admin/reports', methods=['GET'])
@admin_required
def list_reports():
    return jsonify(services.list_open_reports()), 200


@moderation_bp.route('/admin/posts/<int:post_id>/reports', methods=['PATCH'])
@admin_required
def dismiss_reports(post_id):
    data = _json_object()
    if data is None or data.get('status') != 'dismissed':
        return jsonify({'message': 'Only {"status": "dismissed"} is supported'}), 400

    dismissed = services.dismiss_reports(post_id, g.user_id)
    if dismissed is None:
        return jsonify({'message': 'Post not found'}), 404
    return jsonify({'message': 'Reports dismissed', 'dismissed': dismissed}), 200


@moderation_bp.route('/admin/posts/<int:post_id>', methods=['DELETE'])
@admin_required
def delete_post(post_id):
    if not services.delete_post(post_id):
        return jsonify({'message': 'Post not found'}), 404
    return jsonify({'message': 'Post deleted'}), 200


@moderation_bp.route('/admin/users/<int:user_id>/ban', methods=['PUT', 'DELETE'])
@admin_required
def ban(user_id):
    try:
        if request.method == 'PUT':
            user = services.ban_user(user_id, g.user_id)
            message = 'User banned'
        else:
            user = services.unban_user(user_id)
            message = 'User unbanned'
    except LookupError as error:
        return jsonify({'message': str(error)}), 404
    except ValueError as error:
        return jsonify({'message': str(error)}), 400

    return jsonify({'message': message, 'user': user}), 200
