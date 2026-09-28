import math
from functools import wraps

from flask import Blueprint, request, jsonify, g

import services
from rate_limit import SlidingWindowLimiter
from routes.auth import login_required

ai_bp = Blueprint('ai', __name__, url_prefix='/api')

# Every call costs money, and the model's free tier allows only a few requests per minute.
AI_REQUESTS_PER_MINUTE = 10
ai_limiter = SlidingWindowLimiter(AI_REQUESTS_PER_MINUTE, 60)


def ai_rate_limited(view):
    """Must sit below @login_required, so anonymous requests are refused before they are counted."""
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        retry_after = ai_limiter.hit(g.user_id)
        if retry_after:
            response = jsonify({'message': 'Too many AI requests. Please wait a minute and try again.'})
            response.headers['Retry-After'] = str(math.ceil(retry_after))
            return response, 429
        return view(*args, **kwargs)
    return wrapped_view


@ai_bp.route('/corrections', methods=['POST'])
@login_required
@ai_rate_limited
def create_correction():
    data = request.get_json(silent=True)
    if not data or not isinstance(data, dict):
        return jsonify({'message': 'Invalid JSON payload'}), 400

    try:
        corrected = services.correct_text(data.get('text'))
    except ValueError as error:
        return jsonify({'message': str(error)}), 400

    return jsonify({'text': corrected}), 200


@ai_bp.route('/post-suggestions', methods=['POST'])
@login_required
@ai_rate_limited
def create_post_suggestion():
    data = request.get_json(silent=True)
    if not data or not isinstance(data, dict):
        return jsonify({'message': 'Invalid JSON payload'}), 400

    try:
        draft = services.suggest_post(data.get('style'), data.get('grade'), data.get('title'), data.get('body'))
    except ValueError as error:
        return jsonify({'message': str(error)}), 400

    return jsonify({'title': draft.title, 'body': draft.body}), 200


@ai_bp.route('/posts/<int:post_id>/comment-ideas', methods=['GET'])
@login_required
@ai_rate_limited
def get_comment_ideas(post_id):
    ideas = services.comment_ideas(post_id)
    if ideas is None:
        return jsonify({'message': 'Post not found'}), 404
    return jsonify({'comments': ideas}), 200
