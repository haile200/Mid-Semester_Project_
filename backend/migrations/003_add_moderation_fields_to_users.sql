-- is_admin marks moderators. banned_at is NULL for active accounts and records when a ban began.
ALTER TABLE users
    ADD COLUMN is_admin BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN banned_at TIMESTAMP NULL;
