-- Marks bot accounts and stores the personality text that steers their prompts.
-- Both columns are added in a single ALTER statement so the change is atomic.
ALTER TABLE users
    ADD COLUMN is_bot BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN personality TEXT NULL;
