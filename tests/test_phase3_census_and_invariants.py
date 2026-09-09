"""Automated Pytest Suite for Phase 3 Historical Census & Invariants."""

from pathlib import Path
import pytest
from python.database.duckdb_manager import DuckDBManager

DOCS_DIR = Path("docs")
DATA_DIR = Path("data/normalized")

@pytest.fixture(scope="module")
def db():
    manager = DuckDBManager()
    yield manager
    manager.close()

def test_phase3_documentation_deliverables():
    """Verify that all Phase 3 required documentation artifacts exist and are non-empty."""
    required_docs = [
        "historical_scope.md",
        "league_census.md",
        "data_availability_matrix.md",
        "cross_season_schema_audit.md",
        "metric_definitions.md",
        "statistical_analysis_protocol.md",
        "data_quality_report.md",
        "PHASE3_FINAL_CENSUS.md",
    ]
    for doc_name in required_docs:
        doc_path = DOCS_DIR / doc_name
        assert doc_path.exists(), f"Missing required deliverable: {doc_name}"
        assert doc_path.stat().st_size > 500, f"Deliverable {doc_name} is too small / incomplete"

def test_phase3_census_table_counts(db):
    """Verify DuckDB canonical relational tables are populated with expected historical volume."""
    assert db.get_table_count("game") >= 48
    assert db.get_table_count("team") >= 30
    assert db.get_table_count("player") >= 700
    assert db.get_table_count("boxscore_team") >= 80
    assert db.get_table_count("boxscore_player") >= 1000
    assert db.get_table_count("pbp_event") >= 15000
    assert db.get_table_count("shot") >= 4500
    assert db.get_table_count("lineup_stint") >= 300

def test_phase3_parquet_files_integrity():
    """Verify exported Parquet files in data/normalized/ exist and are valid."""
    parquet_tables = [
        "competition", "season", "team", "player", "game",
        "boxscore_team", "boxscore_player", "pbp_event", "shot", "lineup_stint"
    ]
    for tbl in parquet_tables:
        p_path = DATA_DIR / f"{tbl}.parquet"
        assert p_path.exists(), f"Missing exported Parquet file: {p_path}"
        assert p_path.stat().st_size > 0

def test_phase3_falcons_matches_presence(db):
    """Verify Rheinland Falcons Basketball (Team 2048) matches in Season 2025 and absence of 2023."""
    df_falcons = db.query_df("""
        SELECT season_id, COUNT(*) as match_count
        FROM game
        WHERE home_team_id = 'TEM_DEMO_U16' OR away_team_id = 'TEM_DEMO_U16'
        GROUP BY season_id
    """)
    assert len(df_falcons) >= 1
    counts_by_season = dict(zip(df_falcons["season_id"], df_falcons["match_count"]))
    assert counts_by_season.get("SEA_2025", 0) >= 20
    assert "SEA_2023" not in counts_by_season

def test_phase3_boxscore_mathematical_points_formula(db):
    """Verify PTS = FTM + 2*FG2M + 3*FG3M across all team boxscores."""
    df_bxt = db.query_df("""
        SELECT points, ftm, fg2m, fg3m, (ftm + 2*fg2m + 3*fg3m) AS calc_points
        FROM boxscore_team
    """)
    assert len(df_bxt) >= 80
    discrepancies = df_bxt[df_bxt["points"] != df_bxt["calc_points"]]
    assert len(discrepancies) == 0, f"Found {len(discrepancies)} boxscore team point discrepancies"

def test_phase3_pbp_clock_monotonicity_and_validation_detection(db):
    """Verify clock monotonicity validation correctly audits clean vs inverted period clocks."""
    df_val = db.query_df("""
        SELECT game_id, status, message
        FROM validation_log
        WHERE rule_id = 'RULE_PBP_CLOCK_MONO'
    """)
    assert len(df_val) >= 25
    # The vast majority of games pass monotonic clock validation
    passed_games = df_val[df_val["status"] == "PASSED"]
    assert len(passed_games) >= 20
    # Any game with clock inversion is explicitly caught by validation engine
    failed_games = df_val[df_val["status"] == "FAILED"]
    if len(failed_games) > 0:
        for _, row in failed_games.iterrows():
            assert "Clock inversion detected" in row["message"]

def test_phase3_shot_spatial_coordinate_bounds(db):
    """Verify shot coordinate bounding box [0..300] x [0..200]."""
    df_shots = db.query_df("""
        SELECT x_coord, y_coord
        FROM shot
        WHERE shot_location_status = 'OBSERVED'
    """)
    assert len(df_shots) >= 3000
    assert (df_shots["x_coord"] >= 0).all() and (df_shots["x_coord"] <= 300).all()
    assert (df_shots["y_coord"] >= 0).all() and (df_shots["y_coord"] <= 200).all()

def test_phase3_analytical_views_execution(db):
    """Verify that analytical SQL views execute cleanly and return valid aggregations."""
    df_ratings = db.query_df("SELECT * FROM view_team_game_ratings LIMIT 10")
    assert len(df_ratings) > 0
    assert "ortg" in df_ratings.columns and "drtg" in df_ratings.columns and "efg_pct" in df_ratings.columns

    df_players = db.query_df("SELECT * FROM view_player_season_stats LIMIT 10")
    assert len(df_players) > 0
    assert "ppg" in df_players.columns and "ts_pct" in df_players.columns

    df_shots = db.query_df("SELECT * FROM view_shot_spatial_summary LIMIT 10")
    assert len(df_shots) > 0
    assert "fg_pct" in df_shots.columns
