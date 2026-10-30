-- Migration 001: Google sign-in columns on users.
--
-- Only needed if your database already has the users table from before Google sign-in.
-- On a fresh database, just start the app (init_db creates the full table).
--
-- Run with:  psql mentalhealth -f migrations/001_google_signin.sql

BEGIN;

ALTER TABLE users
    ADD COLUMN IF NOT EXISTS google_sub     TEXT,
    ADD COLUMN IF NOT EXISTS avatar_url     TEXT,
    ADD COLUMN IF NOT EXISTS last_login_at  TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS updated_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    ADD COLUMN IF NOT EXISTS token_version  INTEGER     NOT NULL DEFAULT 0;

-- Same constraint name SQLAlchemy uses on a fresh database
ALTER TABLE users ADD CONSTRAINT users_google_sub_key UNIQUE (google_sub);

COMMIT;
