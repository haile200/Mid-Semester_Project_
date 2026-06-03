import mysql.connector
import bcrypt
import os
from dotenv import load_dotenv

load_dotenv()

def setup_database():
    # Connect to MySQL server (without specifying a database)
    conn = mysql.connector.connect(
        host=os.getenv('DB_HOST'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
    )
    cursor = conn.cursor()

    # Create the database if it doesn't exist
    cursor.execute("CREATE DATABASE IF NOT EXISTS hw_2")
    cursor.execute("USE hw_2")

    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            email VARCHAR(255) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            bio VARCHAR(500) DEFAULT '',
            profile_picture VARCHAR(500) DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create posts table with image support and timestamp
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS posts (
            id INT AUTO_INCREMENT PRIMARY KEY,
            title VARCHAR(255) NOT NULL,
            body TEXT NOT NULL,
            image_url VARCHAR(500) DEFAULT '',
            author_id INT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (author_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')

    # Create followers table for follow/unfollow functionality
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS followers (
            follower_id INT NOT NULL,
            following_id INT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (follower_id, following_id),
            FOREIGN KEY (follower_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (following_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')

    # Insert default admin user with hashed password
    hashed = bcrypt.hashpw('password123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    try:
        cursor.execute('''
            INSERT INTO users (name, email, password, bio)
            VALUES (%s, %s, %s, %s)
        ''', ('Admin User', 'admin@example.com', hashed, 'I am the admin'))
        print("Admin user created.")
    except mysql.connector.IntegrityError:
        print("Admin already exists.")

    conn.commit()
    cursor.close()
    conn.close()
    print("Database setup complete.")

if __name__ == '__main__':
    setup_database()