-- Password reset links. Only a SHA-256 hash of each token is stored, so a copy of this table
-- cannot be used to reset anyone's password. A link is valid for a limited time after created_at
-- and is deleted when used or replaced by a newer one.
CREATE TABLE password_resets (
    token_hash CHAR(64) PRIMARY KEY,
    user_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
