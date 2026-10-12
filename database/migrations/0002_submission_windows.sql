-- Run once on the selected BT3 database as a MySQL schema administrator.
-- Do NOT run schema.sql again. MySQL DDL auto-commits: back up before running.
ALTER TABLE competitions
    ADD COLUMN registration_mode ENUM('MANUAL','SCHEDULED') NOT NULL DEFAULT 'MANUAL',
    ADD COLUMN submission_mode ENUM('MANUAL','SCHEDULED') NOT NULL DEFAULT 'MANUAL';

-- Keep ck_open_phases and the existing manual open/closed values.
-- Existing dates remain stored; activate a schedule explicitly through the admin UI.

ALTER TABLE submissions
    ADD COLUMN source_size_bytes INT UNSIGNED NULL;

INSERT INTO schema_migrations(version) VALUES ('0002_submission_windows');
