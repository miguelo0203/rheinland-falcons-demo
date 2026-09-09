-- Canonical DuckDB SQL Schema for JBBL / NBBL Experimental Sandbox
-- Version: 1.0.0
-- Dialect: DuckDB SQL

-- 1. COMPETITION & SEASON ENTITIES
CREATE TABLE IF NOT EXISTS competition (
    competition_id VARCHAR PRIMARY KEY,
    name VARCHAR NOT NULL,
    gender VARCHAR,
    age_category VARCHAR,
    country VARCHAR,
    governing_body VARCHAR,
    created_at TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS season (
    season_id VARCHAR PRIMARY KEY,
    competition_id VARCHAR NOT NULL REFERENCES competition(competition_id),
    name VARCHAR NOT NULL,
    start_date DATE,
    end_date DATE
);

-- 2. TEAM & PLAYER ENTITIES
CREATE TABLE IF NOT EXISTS team (
    team_id VARCHAR PRIMARY KEY,
    canonical_name VARCHAR NOT NULL,
    short_name VARCHAR,
    club_name VARCHAR,
    age_category VARCHAR,
    created_at TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS player (
    player_id VARCHAR PRIMARY KEY,
    canonical_name VARCHAR NOT NULL,
    first_name VARCHAR,
    last_name VARCHAR,
    birth_date DATE,
    height_cm DOUBLE,
    listed_position VARCHAR,
    nationality VARCHAR,
    created_at TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS player_team (
    player_team_id VARCHAR PRIMARY KEY,
    player_id VARCHAR NOT NULL REFERENCES player(player_id),
    team_id VARCHAR NOT NULL REFERENCES team(team_id),
    season_id VARCHAR NOT NULL REFERENCES season(season_id),
    jersey_number VARCHAR,
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);

-- 3. GAME & ROSTER ENTITIES
CREATE TABLE IF NOT EXISTS game (
    game_id VARCHAR PRIMARY KEY,
    season_id VARCHAR NOT NULL REFERENCES season(season_id),
    competition_id VARCHAR NOT NULL REFERENCES competition(competition_id),
    game_date DATE NOT NULL,
    game_time VARCHAR,
    round_number INTEGER,
    home_team_id VARCHAR NOT NULL REFERENCES team(team_id),
    away_team_id VARCHAR NOT NULL REFERENCES team(team_id),
    venue VARCHAR,
    periods_played INTEGER NOT NULL DEFAULT 4,
    home_score INTEGER,
    away_score INTEGER,
    game_status VARCHAR NOT NULL DEFAULT 'FINAL',
    game_type VARCHAR NOT NULL DEFAULT 'OFFICIAL'
);

CREATE TABLE IF NOT EXISTS game_sources (
    game_id VARCHAR PRIMARY KEY REFERENCES game(game_id),
    boxscore_available BOOLEAN NOT NULL,
    pbp_available BOOLEAN NOT NULL,
    video_available BOOLEAN NOT NULL,
    shot_chart_available BOOLEAN NOT NULL,
    boxscore_file_path VARCHAR,
    pbp_file_path VARCHAR,
    video_file_path VARCHAR,
    validation_status VARCHAR NOT NULL,
    completeness_score VARCHAR NOT NULL,
    overall_quality VARCHAR NOT NULL,
    updated_at TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS source_provenance (
    provenance_id VARCHAR PRIMARY KEY,
    source_type VARCHAR NOT NULL,
    source_provider VARCHAR NOT NULL,
    source_file_path VARCHAR NOT NULL,
    source_file_hash VARCHAR NOT NULL,
    parser_version VARCHAR NOT NULL,
    pipeline_version VARCHAR NOT NULL,
    ingestion_timestamp TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS game_roster (
    game_roster_id VARCHAR PRIMARY KEY,
    game_id VARCHAR NOT NULL REFERENCES game(game_id),
    team_id VARCHAR NOT NULL REFERENCES team(team_id),
    player_id VARCHAR NOT NULL REFERENCES player(player_id),
    jersey_number VARCHAR,
    is_starter BOOLEAN,
    is_captain BOOLEAN,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    provenance_id VARCHAR NOT NULL REFERENCES source_provenance(provenance_id)
);

-- 4. BOXSCORE ENTITIES
CREATE TABLE IF NOT EXISTS boxscore_team (
    boxscore_team_id VARCHAR PRIMARY KEY,
    game_id VARCHAR NOT NULL REFERENCES game(game_id),
    team_id VARCHAR NOT NULL REFERENCES team(team_id),
    is_home BOOLEAN NOT NULL,
    points INTEGER NOT NULL,
    fgm INTEGER,
    fga INTEGER,
    fg2m INTEGER,
    fg2a INTEGER,
    fg3m INTEGER,
    fg3a INTEGER,
    ftm INTEGER,
    fta INTEGER,
    orb INTEGER,
    drb INTEGER,
    trb INTEGER,
    ast INTEGER,
    stl INTEGER,
    blk INTEGER,
    tov INTEGER,
    pf INTEGER,
    team_rebounds INTEGER,
    team_turnovers INTEGER,
    provenance_id VARCHAR NOT NULL REFERENCES source_provenance(provenance_id)
);

CREATE TABLE IF NOT EXISTS boxscore_player (
    boxscore_player_id VARCHAR PRIMARY KEY,
    game_id VARCHAR NOT NULL REFERENCES game(game_id),
    team_id VARCHAR NOT NULL REFERENCES team(team_id),
    player_id VARCHAR NOT NULL REFERENCES player(player_id),
    jersey_number VARCHAR,
    seconds_played INTEGER,
    points INTEGER NOT NULL,
    fgm INTEGER,
    fga INTEGER,
    fg2m INTEGER,
    fg2a INTEGER,
    fg3m INTEGER,
    fg3a INTEGER,
    ftm INTEGER,
    fta INTEGER,
    orb INTEGER,
    drb INTEGER,
    trb INTEGER,
    ast INTEGER,
    stl INTEGER,
    blk INTEGER,
    tov INTEGER,
    pf INTEGER,
    plus_minus INTEGER,
    is_dnp BOOLEAN NOT NULL DEFAULT FALSE,
    dnp_reason VARCHAR,
    observation_status VARCHAR NOT NULL DEFAULT 'OBSERVED',
    provenance_id VARCHAR NOT NULL REFERENCES source_provenance(provenance_id)
);

-- 5. PLAY-BY-PLAY, SHOTS & LINEUPS
CREATE TABLE IF NOT EXISTS pbp_event (
    event_id VARCHAR PRIMARY KEY,
    game_id VARCHAR NOT NULL REFERENCES game(game_id),
    period INTEGER NOT NULL,
    period_type VARCHAR NOT NULL DEFAULT 'REGULAR',
    clock_display VARCHAR NOT NULL,
    game_seconds_remaining DOUBLE NOT NULL,
    period_seconds_remaining DOUBLE NOT NULL,
    event_index INTEGER NOT NULL,
    event_type VARCHAR NOT NULL,
    event_subtype VARCHAR,
    team_id VARCHAR REFERENCES team(team_id),
    player_id VARCHAR REFERENCES player(player_id),
    secondary_player_id VARCHAR REFERENCES player(player_id),
    home_score INTEGER NOT NULL,
    away_score INTEGER NOT NULL,
    score_margin INTEGER NOT NULL,
    points_scored INTEGER NOT NULL DEFAULT 0,
    description VARCHAR,
    possession_id VARCHAR,
    provenance_id VARCHAR NOT NULL REFERENCES source_provenance(provenance_id)
);

CREATE TABLE IF NOT EXISTS shot (
    shot_id VARCHAR PRIMARY KEY,
    event_id VARCHAR REFERENCES pbp_event(event_id),
    game_id VARCHAR NOT NULL REFERENCES game(game_id),
    team_id VARCHAR NOT NULL REFERENCES team(team_id),
    player_id VARCHAR NOT NULL REFERENCES player(player_id),
    period INTEGER NOT NULL,
    game_seconds_remaining DOUBLE,
    shot_type VARCHAR NOT NULL,
    shot_subtype VARCHAR,
    is_made BOOLEAN NOT NULL,
    points INTEGER NOT NULL,
    x_coord DOUBLE,
    y_coord DOUBLE,
    shot_distance_m DOUBLE,
    shot_zone VARCHAR,
    shot_location_status VARCHAR NOT NULL DEFAULT 'NOT_AVAILABLE',
    assisted_by_player_id VARCHAR REFERENCES player(player_id),
    provenance_id VARCHAR NOT NULL REFERENCES source_provenance(provenance_id)
);

CREATE TABLE IF NOT EXISTS lineup_stint (
    stint_id VARCHAR PRIMARY KEY,
    game_id VARCHAR NOT NULL REFERENCES game(game_id),
    team_id VARCHAR NOT NULL REFERENCES team(team_id),
    period INTEGER NOT NULL,
    start_game_seconds DOUBLE NOT NULL,
    end_game_seconds DOUBLE NOT NULL,
    duration_seconds DOUBLE NOT NULL,
    player_ids VARCHAR NOT NULL,
    is_home BOOLEAN NOT NULL,
    points_for INTEGER NOT NULL,
    points_against INTEGER NOT NULL,
    reconstruction_method VARCHAR NOT NULL DEFAULT 'EXACT_SUB_TRACKING',
    confidence_status VARCHAR NOT NULL DEFAULT 'EXACT',
    provenance_id VARCHAR NOT NULL REFERENCES source_provenance(provenance_id)
);

-- 6. VIDEO & SYNCHRONIZATION
CREATE TABLE IF NOT EXISTS video (
    video_id VARCHAR PRIMARY KEY,
    game_id VARCHAR NOT NULL REFERENCES game(game_id),
    file_path VARCHAR NOT NULL,
    duration_seconds DOUBLE,
    container_format VARCHAR,
    codec VARCHAR,
    resolution_width INTEGER,
    resolution_height INTEGER,
    fps DOUBLE,
    file_size_bytes BIGINT,
    checksum_sha256 VARCHAR NOT NULL,
    camera_angle VARCHAR,
    ingestion_timestamp TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS video_event_sync (
    sync_id VARCHAR PRIMARY KEY,
    event_id VARCHAR REFERENCES pbp_event(event_id),
    game_id VARCHAR NOT NULL REFERENCES game(game_id),
    video_id VARCHAR NOT NULL REFERENCES video(video_id),
    video_start_time_s DOUBLE NOT NULL,
    video_end_time_s DOUBLE NOT NULL,
    confidence_level VARCHAR NOT NULL DEFAULT 'HIGH',
    sync_method VARCHAR NOT NULL DEFAULT 'MANUAL',
    verified_by VARCHAR
);

-- 7. RESOLUTION, CONFLICTS & AUDIT LOGS
CREATE TABLE IF NOT EXISTS entity_alias (
    alias_id VARCHAR PRIMARY KEY,
    entity_type VARCHAR NOT NULL,
    canonical_id VARCHAR NOT NULL,
    source_provider VARCHAR NOT NULL,
    source_id VARCHAR,
    source_name_raw VARCHAR NOT NULL,
    normalized_name VARCHAR NOT NULL,
    jersey_number VARCHAR,
    match_confidence DOUBLE NOT NULL,
    requires_review BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS source_conflict_log (
    conflict_id VARCHAR PRIMARY KEY,
    game_id VARCHAR NOT NULL REFERENCES game(game_id),
    entity_table VARCHAR NOT NULL,
    entity_id VARCHAR NOT NULL,
    field_name VARCHAR NOT NULL,
    source_a_type VARCHAR NOT NULL,
    source_a_value VARCHAR NOT NULL,
    source_b_type VARCHAR NOT NULL,
    source_b_value VARCHAR NOT NULL,
    resolution_policy VARCHAR NOT NULL,
    resolved_value VARCHAR NOT NULL,
    logged_at TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS validation_log (
    validation_id VARCHAR PRIMARY KEY,
    game_id VARCHAR NOT NULL REFERENCES game(game_id),
    rule_id VARCHAR NOT NULL,
    rule_category VARCHAR NOT NULL,
    severity VARCHAR NOT NULL,
    status VARCHAR NOT NULL,
    message VARCHAR NOT NULL,
    details_json VARCHAR,
    timestamp TIMESTAMP NOT NULL
);
