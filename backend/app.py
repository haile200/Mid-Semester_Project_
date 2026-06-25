from flask import Flask
from flask_cors import CORS
from config import Config
from routes.auth import auth_bp
from routes.posts import posts_bp
from routes.users import users_bp
from routes.feed import feed_bp

app = Flask(__name__)
app.secret_key = Config.SECRET_KEY
CORS(app, supports_credentials=True, origins=Config.CORS_ORIGINS)

app.register_blueprint(auth_bp)
app.register_blueprint(posts_bp)
app.register_blueprint(users_bp)
app.register_blueprint(feed_bp)

if __name__ == '__main__':
    app.run(debug=True, port=5000)

@app.route('/api/posts', methods=['GET'])
def get_posts():
    start = int(request.args.get('start', 0))
    limit = int(request.args.get('limit', 10))
    user_id = request.args.get('userId')

    # Query includes author_profile_picture
    query = """
        SELECT posts.id, posts.title, posts.body, posts.image_url, posts.created_at,
               users.id AS userId,
               users.name AS author_name,
               users.profile_picture AS author_profile_picture
        FROM posts
        JOIN users ON posts.author_id = users.id
    """
    params = []

    if user_id:
        query += " WHERE posts.author_id = %s"
        params.append(int(user_id))

    query += " ORDER BY posts.id DESC LIMIT %s OFFSET %s"
    params.extend([limit, start])

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(query, tuple(params))
    posts = fetchall_dict(cursor)
    cursor.close()
    conn.close()

    return jsonify(posts), 200

@app.route('/api/posts', methods=['POST'])
def create_post():
    author_id = session.get('user_id')
    if not author_id:
        return jsonify({'message': 'Unauthorized. Please log in.'}), 401

    data = request.get_json(silent=True)
    if not data:
        return jsonify({'message': 'Invalid JSON payload'}), 400

    title = data.get('title', '').strip()
    body = data.get('body', '').strip()
    image_url = data.get('imageUrl', None)

    if not title or not body:
        return jsonify({'message': 'Title and body are required'}), 400

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO posts (title, body, image_url, author_id) VALUES (%s, %s, %s, %s)",
        (title, body, image_url, author_id)
    )
    conn.commit()
    post_id = cursor.lastrowid
    cursor.close()
    conn.close()

    return jsonify({'message': 'Post created successfully', 'postId': post_id}), 201

@app.route('/api/users', methods=['GET'])
def get_users():
    start = int(request.args.get('start', 0))
    limit = int(request.args.get('limit', 10))
    search = request.args.get('search', '').strip()

    query = """
        SELECT
            users.id,
            users.name,
            users.email,
            users.profile_picture,
            (SELECT COUNT(*) FROM posts WHERE author_id = users.id) AS postCount
        FROM users
    """
    params = []

    if search:
        # Search ONLY by user name 
        query += " WHERE users.name LIKE %s "
        params.append(f"%{search}%")

    query += " ORDER BY users.name LIMIT %s OFFSET %s"
    params.extend([limit, start])

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(query, tuple(params))
    users = fetchall_dict(cursor)
    cursor.close()
    conn.close()

    return jsonify(users), 200

@app.route('/api/users/<int:user_id>', methods=['GET'])
def get_user_by_id(user_id):
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT
            users.id,
            users.name,
            users.email,
            users.bio,
            users.profile_picture,
            users.created_at,
            (SELECT COUNT(*) FROM posts WHERE author_id = users.id) AS postCount,
            (SELECT COUNT(*) FROM followers WHERE following_id = users.id) AS followersCount,
            (SELECT COUNT(*) FROM followers WHERE follower_id = users.id) AS followingCount
        FROM users
        WHERE users.id = %s
    """, (user_id,))
    
    user = fetchone_dict(cursor)
    
    if not user:
        cursor.close()
        conn.close()
        return jsonify({'message': 'User not found'}), 404

    current_user_id = session.get('user_id')
    is_following = False
    
    if current_user_id:
        cursor.execute("SELECT 1 FROM followers WHERE follower_id = %s AND following_id = %s", (current_user_id, user_id))
        is_following = bool(cursor.fetchone())
        
    user['is_following'] = is_following

    cursor.close()
    conn.close()
    
    return jsonify(user), 200

@app.route('/api/users/profile', methods=['PUT'])
def update_profile():
    # Only logged-in users can update their profile
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'message': 'Unauthorized. Please log in.'}), 401

    data = request.get_json(silent=True)
    if not data:
        return jsonify({'message': 'Invalid JSON payload'}), 400

    bio = data.get('bio', '').strip()
    profile_picture = data.get('profilePicture', '').strip()

    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute(
        "UPDATE users SET bio = %s, profile_picture = %s WHERE id = %s",
        (bio, profile_picture, user_id)
    )
    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({'message': 'Profile updated successfully'}), 200

@app.route('/api/follow/<int:following_id>', methods=['POST', 'DELETE'])
def follow_user(following_id):
    follower_id = session.get('user_id')
    if not follower_id:
        return jsonify({'message': 'Unauthorized. Please log in.'}), 401
        
    if follower_id == following_id:
        return jsonify({'message': 'You cannot follow yourself.'}), 400

    conn = get_db()
    cursor = conn.cursor()
    
    if request.method == 'POST':
        try:
            cursor.execute("INSERT INTO followers (follower_id, following_id) VALUES (%s, %s)", (follower_id, following_id))
            conn.commit()
            msg = 'Successfully followed user'
        except mysql.connector.IntegrityError:
            msg = 'Already following this user'
    
    elif request.method == 'DELETE':
        cursor.execute("DELETE FROM followers WHERE follower_id = %s AND following_id = %s", (follower_id, following_id))
        conn.commit()
        msg = 'Successfully unfollowed user'

    cursor.close()
    conn.close()
    return jsonify({'message': msg}), 200

@app.route('/api/feed/following', methods=['GET'])
def get_following_feed():
    current_user_id = session.get('user_id')
    if not current_user_id:
        return jsonify({'message': 'Unauthorized. Please log in.'}), 401

    start = int(request.args.get('start', 0))
    limit = int(request.args.get('limit', 10))

    # Query includes author_profile_picture
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
    cursor.execute(query, (current_user_id, limit, start))
    posts = fetchall_dict(cursor)
    cursor.close()
    conn.close()

    return jsonify(posts), 200

@app.route('/api/feed', methods=['GET'])
def get_feed():
    start = int(request.args.get('start', 0))
    limit = int(request.args.get('limit', 10))
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Query includes author_profile_picture
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

if __name__ == '__main__':
    app.run(debug=True, port=5000)