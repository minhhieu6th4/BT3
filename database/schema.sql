-- BT3 shared schema. MySQL >= 8.0.16, InnoDB, UTC timestamps.
-- Select an EMPTY database before executing; never run as a reset script.
SET NAMES utf8mb4;
SET time_zone = '+00:00';

CREATE TABLE schema_migrations (
 version VARCHAR(64) PRIMARY KEY,
 applied_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
) ENGINE=InnoDB;

CREATE TABLE users (
 id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
 username VARCHAR(64) NOT NULL UNIQUE,
 password_hash VARCHAR(255) NOT NULL,
 account_type ENUM('ADMIN','TEAM','STUDENT') NOT NULL,
 full_name VARCHAR(150),
 student_code VARCHAR(32) UNIQUE,
 school_email VARCHAR(254) UNIQUE,
 email_verified_at DATETIME(6),
 active BOOLEAN NOT NULL DEFAULT TRUE,
 created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
) ENGINE=InnoDB;

CREATE TABLE competitions (
 id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
 code VARCHAR(64) NOT NULL UNIQUE,
 name VARCHAR(150) NOT NULL,
 mode ENUM('DEMO','MAIN') NOT NULL,
 status ENUM('DRAFT','REGISTRATION','CODING','VALIDATING','PLAYING','FINISHED') NOT NULL DEFAULT 'DRAFT',
 max_teams SMALLINT UNSIGNED NOT NULL,
 registration_open BOOLEAN NOT NULL DEFAULT FALSE,
 submission_open BOOLEAN NOT NULL DEFAULT FALSE,
 registration_opens_at DATETIME(6),
 registration_closes_at DATETIME(6),
 submission_opens_at DATETIME(6),
 submission_closes_at DATETIME(6),
 format_config JSON NOT NULL,
 created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
 CONSTRAINT ck_capacity CHECK (max_teams > 0),
 CONSTRAINT ck_open_phases CHECK (NOT (registration_open AND submission_open)),
 CONSTRAINT ck_registration_window CHECK (registration_closes_at IS NULL OR registration_opens_at IS NULL OR registration_closes_at > registration_opens_at),
 CONSTRAINT ck_submission_window CHECK (submission_closes_at IS NULL OR submission_opens_at IS NULL OR submission_closes_at > submission_opens_at)
) ENGINE=InnoDB;

CREATE TABLE teams (
 id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
 competition_id BIGINT UNSIGNED NOT NULL,
 name VARCHAR(100) NOT NULL,
 owner_user_id BIGINT UNSIGNED NOT NULL,
 status ENUM('REGISTERED','APPROVED','DISQUALIFIED','WITHDRAWN') NOT NULL DEFAULT 'REGISTERED',
 registered_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
 UNIQUE (competition_id, name),
 UNIQUE (competition_id, owner_user_id),
 UNIQUE (competition_id, id),
 FOREIGN KEY (competition_id) REFERENCES competitions(id),
 FOREIGN KEY (owner_user_id) REFERENCES users(id)
) ENGINE=InnoDB;

CREATE TABLE team_members (
 competition_id BIGINT UNSIGNED NOT NULL,
 team_id BIGINT UNSIGNED NOT NULL,
 user_id BIGINT UNSIGNED NOT NULL,
 role ENUM('CAPTAIN','MEMBER') NOT NULL DEFAULT 'MEMBER',
 confirmed_at DATETIME(6),
 PRIMARY KEY (competition_id, user_id),
 FOREIGN KEY (competition_id, team_id) REFERENCES teams(competition_id, id),
 FOREIGN KEY (user_id) REFERENCES users(id)
) ENGINE=InnoDB;

CREATE TABLE email_verifications (
 id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
 user_id BIGINT UNSIGNED NOT NULL,
 email VARCHAR(254) NOT NULL,
 token_hash CHAR(64) CHARACTER SET ascii COLLATE ascii_bin NOT NULL UNIQUE,
 expires_at DATETIME(6) NOT NULL,
 used_at DATETIME(6),
 FOREIGN KEY (user_id) REFERENCES users(id)
) ENGINE=InnoDB;

CREATE TABLE submissions (
 id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
 team_id BIGINT UNSIGNED NOT NULL,
 submitted_by BIGINT UNSIGNED NOT NULL,
 version INT UNSIGNED NOT NULL,
 source_file_path VARCHAR(500) NOT NULL,
 source_sha256 CHAR(64) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
 received_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
 validation_status ENUM('PENDING','RUNNING','VALID','INVALID','SYSTEM_ERROR') NOT NULL DEFAULT 'PENDING',
 validation_message TEXT,
 validated_at DATETIME(6),
 UNIQUE (team_id, version),
 UNIQUE (team_id, id),
 INDEX ix_submission_selection (team_id, validation_status, received_at),
 CONSTRAINT ck_submission_version CHECK (version > 0),
 FOREIGN KEY (team_id) REFERENCES teams(id),
 FOREIGN KEY (submitted_by) REFERENCES users(id)
) ENGINE=InnoDB;

-- A single locked choice per team; preserves all earlier submission versions.
CREATE TABLE selected_submissions (
 team_id BIGINT UNSIGNED PRIMARY KEY,
 submission_id BIGINT UNSIGNED NOT NULL,
 selected_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
 FOREIGN KEY (team_id, submission_id) REFERENCES submissions(team_id, id)
) ENGINE=InnoDB;

CREATE TABLE rule_sets (
 id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
 code VARCHAR(64) NOT NULL,
 version INT UNSIGNED NOT NULL,
 configuration JSON NOT NULL,
 created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
 UNIQUE (code, version),
 CONSTRAINT ck_rule_version CHECK (version > 0)
) ENGINE=InnoDB;

CREATE TABLE rounds (
 id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
 competition_id BIGINT UNSIGNED NOT NULL,
 code VARCHAR(64) NOT NULL,
 name VARCHAR(100) NOT NULL,
 sequence_number SMALLINT UNSIGNED NOT NULL,
 kind ENUM('ROUND_ROBIN','KNOCKOUT') NOT NULL,
 best_of SMALLINT UNSIGNED NOT NULL,
 rule_set_id BIGINT UNSIGNED,
 status ENUM('PENDING','RUNNING','COMPLETED','FAILED') NOT NULL DEFAULT 'PENDING',
 published_at DATETIME(6),
 published_by BIGINT UNSIGNED,
 UNIQUE (competition_id, code),
 UNIQUE (competition_id, sequence_number),
 UNIQUE (competition_id, id),
 CONSTRAINT ck_round_bo CHECK (best_of > 0 AND MOD(best_of, 2) = 1),
 CONSTRAINT ck_round_publish CHECK (published_at IS NULL OR status = 'COMPLETED'),
 FOREIGN KEY (competition_id) REFERENCES competitions(id),
 FOREIGN KEY (rule_set_id) REFERENCES rule_sets(id),
 FOREIGN KEY (published_by) REFERENCES users(id)
) ENGINE=InnoDB;

CREATE TABLE tournament_groups (
 id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
 competition_id BIGINT UNSIGNED NOT NULL,
 round_id BIGINT UNSIGNED NOT NULL,
 name VARCHAR(32) NOT NULL,
 UNIQUE (round_id, name),
 UNIQUE (round_id, id),
 UNIQUE (competition_id, round_id, id),
 FOREIGN KEY (competition_id, round_id) REFERENCES rounds(competition_id, id)
) ENGINE=InnoDB;

CREATE TABLE group_teams (
 competition_id BIGINT UNSIGNED NOT NULL,
 round_id BIGINT UNSIGNED NOT NULL,
 group_id BIGINT UNSIGNED NOT NULL,
 team_id BIGINT UNSIGNED NOT NULL,
 PRIMARY KEY (group_id, team_id),
 UNIQUE (round_id, team_id),
 FOREIGN KEY (competition_id, round_id, group_id) REFERENCES tournament_groups(competition_id, round_id, id),
 FOREIGN KEY (competition_id, team_id) REFERENCES teams(competition_id, id)
) ENGINE=InnoDB;

CREATE TABLE matches (
 id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
 competition_id BIGINT UNSIGNED NOT NULL,
 round_id BIGINT UNSIGNED NOT NULL,
 group_id BIGINT UNSIGNED,
 bracket_slot INT UNSIGNED NOT NULL,
 team_a_id BIGINT UNSIGNED,
 team_b_id BIGINT UNSIGNED,
 best_of SMALLINT UNSIGNED NOT NULL,
 status ENUM('PENDING','RUNNING','COMPLETED','BYE','FAILED') NOT NULL DEFAULT 'PENDING',
 result_type ENUM('WIN','DRAW'),
 winner_team_id BIGINT UNSIGNED,
 result_reason TEXT,
 started_at DATETIME(6),
 finished_at DATETIME(6),
 UNIQUE (round_id, bracket_slot),
 UNIQUE (id, team_a_id),
 UNIQUE (id, team_b_id),
 FOREIGN KEY (competition_id, round_id) REFERENCES rounds(competition_id, id),
 FOREIGN KEY (round_id, group_id) REFERENCES tournament_groups(round_id, id),
 FOREIGN KEY (competition_id, team_a_id) REFERENCES teams(competition_id, id),
 FOREIGN KEY (competition_id, team_b_id) REFERENCES teams(competition_id, id),
 FOREIGN KEY (competition_id, winner_team_id) REFERENCES teams(competition_id, id),
 CONSTRAINT ck_match_teams CHECK (team_a_id IS NULL OR team_b_id IS NULL OR team_a_id <> team_b_id),
 CONSTRAINT ck_match_bo CHECK (best_of > 0 AND MOD(best_of, 2) = 1),
 CONSTRAINT ck_match_winner CHECK (winner_team_id IS NULL OR winner_team_id = COALESCE(team_a_id, 0) OR winner_team_id = COALESCE(team_b_id, 0)),
 CONSTRAINT ck_match_result CHECK (result_type IS NULL OR (result_type = 'DRAW' AND winner_team_id IS NULL) OR (result_type = 'WIN' AND winner_team_id IS NOT NULL)),
 CONSTRAINT ck_match_complete CHECK (status <> 'COMPLETED' OR (team_a_id IS NOT NULL AND team_b_id IS NOT NULL AND result_type IS NOT NULL)),
 CONSTRAINT ck_match_bye CHECK (status <> 'BYE' OR ((team_a_id IS NULL) <> (team_b_id IS NULL) AND winner_team_id IS NOT NULL AND result_type IS NOT NULL AND result_type = 'WIN'))
) ENGINE=InnoDB;

-- Preserve reruns. Backend chooses one official attempt per game_number.
CREATE TABLE games (
 id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
 match_id BIGINT UNSIGNED NOT NULL,
 game_number SMALLINT UNSIGNED NOT NULL,
 attempt_number SMALLINT UNSIGNED NOT NULL DEFAULT 1,
 is_official BOOLEAN NOT NULL DEFAULT FALSE,
 official_slot SMALLINT UNSIGNED GENERATED ALWAYS AS (CASE WHEN is_official THEN game_number ELSE NULL END) STORED,
 team_a_id BIGINT UNSIGNED NOT NULL,
 team_b_id BIGINT UNSIGNED NOT NULL,
 a_submission_id BIGINT UNSIGNED NOT NULL,
 b_submission_id BIGINT UNSIGNED NOT NULL,
 red_team_id BIGINT UNSIGNED NOT NULL,
 rule_set_id BIGINT UNSIGNED NOT NULL,
 initial_state JSON,
 status ENUM('PENDING','RUNNING','COMPLETED','FAILED') NOT NULL DEFAULT 'PENDING',
 result_type ENUM('WIN','DRAW'),
 winner_team_id BIGINT UNSIGNED,
 result_reason TEXT,
 started_at DATETIME(6),
 finished_at DATETIME(6),
 UNIQUE (match_id, game_number, attempt_number),
 UNIQUE (match_id, official_slot),
 CONSTRAINT ck_game_numbers CHECK (game_number > 0 AND attempt_number > 0),
 CONSTRAINT ck_red_team CHECK (red_team_id IN (team_a_id, team_b_id)),
 CONSTRAINT ck_game_winner CHECK (winner_team_id IS NULL OR winner_team_id IN (team_a_id, team_b_id)),
 CONSTRAINT ck_game_result CHECK (result_type IS NULL OR (result_type = 'DRAW' AND winner_team_id IS NULL) OR (result_type = 'WIN' AND winner_team_id IS NOT NULL)),
 CONSTRAINT ck_game_complete CHECK (status <> 'COMPLETED' OR result_type IS NOT NULL),
 CONSTRAINT ck_game_official CHECK (NOT is_official OR status = 'COMPLETED'),
 FOREIGN KEY (match_id, team_a_id) REFERENCES matches(id, team_a_id),
 FOREIGN KEY (match_id, team_b_id) REFERENCES matches(id, team_b_id),
 FOREIGN KEY (team_a_id, a_submission_id) REFERENCES submissions(team_id, id),
 FOREIGN KEY (team_b_id, b_submission_id) REFERENCES submissions(team_id, id),
 FOREIGN KEY (rule_set_id) REFERENCES rule_sets(id)
) ENGINE=InnoDB;

CREATE TABLE moves (
 id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
 game_id BIGINT UNSIGNED NOT NULL,
 sequence_number INT UNSIGNED NOT NULL,
 turn_number INT UNSIGNED NOT NULL,
 team_color ENUM('RED','BLUE') NOT NULL,
 move_data JSON NOT NULL,
 UNIQUE (game_id, sequence_number),
 CONSTRAINT ck_move_sequence CHECK (sequence_number > 0 AND turn_number > 0),
 FOREIGN KEY (game_id) REFERENCES games(id)
) ENGINE=InnoDB;

-- Snapshot computed by Tournament, never a second implementation of scoring.
CREATE TABLE rankings (
 group_id BIGINT UNSIGNED NOT NULL,
 team_id BIGINT UNSIGNED NOT NULL,
 played INT UNSIGNED NOT NULL DEFAULT 0,
 wins INT UNSIGNED NOT NULL DEFAULT 0,
 draws INT UNSIGNED NOT NULL DEFAULT 0,
 losses INT UNSIGNED NOT NULL DEFAULT 0,
 points INT UNSIGNED NOT NULL DEFAULT 0,
 position INT UNSIGNED,
 tie_break_details JSON,
 updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
 PRIMARY KEY (group_id, team_id),
 CONSTRAINT ck_rank_counts CHECK (played = wins + draws + losses),
 CONSTRAINT ck_rank_position CHECK (position IS NULL OR position > 0),
 FOREIGN KEY (group_id, team_id) REFERENCES group_teams(group_id, team_id)
) ENGINE=InnoDB;

CREATE TABLE audit_logs (
 id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
 competition_id BIGINT UNSIGNED,
 actor_user_id BIGINT UNSIGNED,
 action VARCHAR(100) NOT NULL,
 details JSON,
 occurred_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
 FOREIGN KEY (competition_id) REFERENCES competitions(id),
 FOREIGN KEY (actor_user_id) REFERENCES users(id)
) ENGINE=InnoDB;

INSERT INTO schema_migrations(version) VALUES ('0001_initial');
