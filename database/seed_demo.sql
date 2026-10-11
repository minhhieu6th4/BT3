-- DEMO ONLY. Explicit target prevents loading into main by accident.
-- One-time seed: conflicts cause an error instead of overwriting existing data.
USE bt3_demo;
SET time_zone = '+00:00';
START TRANSACTION;
INSERT INTO competitions (code, name, mode, max_teams, format_config)
VALUES ('demo', 'BT3 Demo', 'DEMO', 6,
 JSON_OBJECT('group_count', 2, 'group_capacity', 3,
 'qualification_best_of', 1, 'knockout_rounds', JSON_ARRAY('final'),
 'win_points', 3, 'draw_points', 1, 'loss_points', 0,
 'display_delay', 3));
SET @demo_competition_id = LAST_INSERT_ID();
INSERT INTO rounds (competition_id, code, name, sequence_number, kind, best_of)
VALUES (@demo_competition_id, 'qualification', 'Vòng bảng', 1, 'ROUND_ROBIN', 1);
SET @qualification_id = LAST_INSERT_ID();
INSERT INTO tournament_groups (competition_id, round_id, name)
VALUES (@demo_competition_id, @qualification_id, 'A'),
       (@demo_competition_id, @qualification_id, 'B');
-- Final best_of and RuleSet are intentionally NOT seeded: pending decisions.
-- No teams, credentials, submissions, results or unapproved rules are invented.
COMMIT;
