-- Read-only checks. Select bt3_demo or bt3_main before running.
SELECT DATABASE() AS selected_database, VERSION() AS server_version;
SELECT version, applied_at FROM schema_migrations ORDER BY version;
SELECT table_name FROM information_schema.tables
WHERE table_schema = DATABASE() AND table_type = 'BASE TABLE' ORDER BY table_name;
SELECT constraint_type, COUNT(*) AS constraint_count
FROM information_schema.table_constraints
WHERE table_schema = DATABASE() GROUP BY constraint_type;
SELECT code, mode, max_teams, registration_open, submission_open FROM competitions;
SELECT r.code, r.status, r.published_at, g.name AS group_name
FROM rounds r LEFT JOIN tournament_groups g ON g.round_id = r.id
ORDER BY r.competition_id, r.sequence_number, g.name;
