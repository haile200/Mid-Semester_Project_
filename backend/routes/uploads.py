import math

from flask import Blueprint, g, jsonify, request, send_from_directory

import images
from config import Config
from rate_limit import SlidingWindowLimiter
from routes.auth import login_required

uploads_bp = Blueprint('uploads', __name__)

# Protects the server's disk; generous for people adding photos to their posts.
upload_limiter = SlidingWindowLimiter(30, 60 * 60)


@uploads_bp.route('/api/uploads', methods=['POST'])
@login_required
def upload_image():
    retry_after = upload_limiter.hit(g.user_id)
    if retry_after:
        response = jsonify({'message': 'Too many uploads. Please try again later.'})
        response.headers['Retry-After'] = str(math.ceil(retry_after))
        return response, 429

    file = request.files.get('image')
    if file is None:
        return jsonify({'message': 'Choose an image to upload'}), 400

    try:
        name = images.save_image(file.read(), Config.UPLOAD_DIR)
    except images.InvalidImage as error:
        return jsonify({'message': str(error)}), 400

    return jsonify({'url': f'/uploads/{name}'}), 201


# In production nginx serves /uploads straight from the shared volume; this covers development.
@uploads_bp.route('/uploads/<name>', methods=['GET'])
def serve_upload(name):
    # send_from_directory refuses any name that would leave the folder, such as "../config.py".
    return send_from_directory(Config.UPLOAD_DIR, name)
