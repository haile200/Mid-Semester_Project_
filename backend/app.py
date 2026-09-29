import os

from flask import Flask, jsonify
from flask_cors import CORS
from brain import select_mode
from config import Config
from db import get_db
from utils import fetchall_dict
from routes.auth import auth_bp
from routes.posts import posts_bp
from routes.users import users_bp
from routes.feed import feed_bp
from routes.comments import comments_bp
from routes.ai import ai_bp
from routes.moderation import moderation_bp
from routes.uploads import uploads_bp

# Fail at startup on a broken BRAIN_MODE, not on the first post someone writes.
select_mode(Config.BRAIN_MODE, Config.GEMINI_API_KEY)

app = Flask(__name__)
# Flask stops reading a request body past this size and answers 413.
app.config['MAX_CONTENT_LENGTH'] = Config.MAX_UPLOAD_MB * 1024 * 1024
CORS(app, supports_credentials=True, origins=Config.CORS_ORIGINS)
os.makedirs(Config.UPLOAD_DIR, exist_ok=True)

app.register_blueprint(auth_bp)
app.register_blueprint(posts_bp)
app.register_blueprint(users_bp)
app.register_blueprint(feed_bp)
app.register_blueprint(comments_bp)
app.register_blueprint(ai_bp)
app.register_blueprint(moderation_bp)
app.register_blueprint(uploads_bp)


@app.errorhandler(413)
def request_too_large(error):
    return jsonify({'message': f'The file is too large. Images can be up to {Config.MAX_UPLOAD_MB} MB.'}), 413


@app.route('/api/health')
def health():
    return jsonify({'status': 'ok'}), 200

if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')
