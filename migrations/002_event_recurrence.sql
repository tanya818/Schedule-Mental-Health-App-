-- Migration 002: replace events.recurring (true/false) with a recurrence rule.
--
-- Only needed if your database already has the events table from before this change.
-- On a fresh database, just start the app (init_db creates the full table).
--
-- Run with:  psql mentalhealth -f migrations/002_event_recurrence.sql
--
-- Existing events with recurring = true become "weekly, every 1 week, no end date"
-- (the old flag didn't say how often). Review them afterwards if that's not right.

BEGIN;

ALTER TABLE events
    ADD COLUMN recurrence_frequency TEXT,
    ADD COLUMN recurrence_interval  SMALLINT,
    ADD COLUMN recurrence_days      TEXT[],
    ADD COLUMN recurrence_until     DATE;

UPDATE events
SET recurrence_frequency = 'weekly',
    recurrence_interval  = 1
WHERE recurring = true;

ALTER TABLE events DROP COLUMN recurring;

ALTER TABLE events
    ADD CONSTRAINT ck_events_recurrence_frequency
        CHECK (recurrence_frequency IN ('daily', 'weekly', 'monthly', 'yearly')),
    ADD CONSTRAINT ck_events_recurrence_complete
        CHECK ((recurrence_frequency IS NULL AND recurrence_interval IS NULL
                AND recurrence_days IS NULL AND recurrence_until IS NULL)
            OR (recurrence_frequency IS NOT NULL AND recurrence_interval >= 1)),
    ADD CONSTRAINT ck_events_recurrence_days_weekly_only
        CHECK (recurrence_days IS NULL OR recurrence_frequency = 'weekly');

COMMIT;
