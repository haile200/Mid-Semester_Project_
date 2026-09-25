from flask import Flask, jsonify
from flask_cors import CORS
from config import Config
from db import get_db
from utils import fetchall_dict
from routes.auth import auth_bp
from routes.posts import posts_bp
from routes.users import users_bp
from routes.feed import feed_bp
from routes.comments import comments_bp

app = Flask(__name__)
app.secret_key = Config.SECRET_KEY
CORS(app, supports_credentials=True, origins=Config.CORS_ORIGINS)

app.register_blueprint(auth_bp)
app.register_blueprint(posts_bp)
app.register_blueprint(users_bp)
app.register_blueprint(feed_bp)
app.register_blueprint(comments_bp)


@app.route('/api/health')
def health():
    return jsonify({'status': 'ok'}), 200

if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')
