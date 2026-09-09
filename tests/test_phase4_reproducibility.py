"""Automated test suite for Phase 4 Deterministic Reproducibility & Mathematical Invariants."""

from pathlib import Path
import pandas as pd
import pytest

from python.database.duckdb_manager import DuckDBManager

DERIVED_DIR = Path("data/derived")

@pytest.fixture(scope="module")
def db():
    manager = DuckDBManager()
    yield manager
    manager.close()

def test_all_ten_phase4_parquet_datasets_exist():
    """Verify presence and non-emptiness of all 10 derived datasets."""
    datasets = [
        "coach_findings.parquet",
        "team_game_analysis.parquet",
        "team_season_analysis.parquet",
        "player_game_analysis.parquet",
        "player_weekly_analysis.parquet",
        "player_rolling_analysis.parquet",
        "league_context_analysis.parquet",
        "shot_analysis.parquet",
        "finding_evidence.parquet",
        "hypotheses.parquet"
    ]
    for d in datasets:
        p = DERIVED_DIR / d
        assert p.exists(), f"Missing dataset: {d}"
        df = pd.read_parquet(p)
        assert len(df) > 0, f"Dataset {d} is empty"

def test_shot_analysis_coordinate_integrity():
    """Verify shot coordinate statuses and valid spatial boundaries."""
    df_shots = pd.read_parquet(DERIVED_DIR / "shot_analysis.parquet")
    assert len(df_shots) >= 5000
    
    # Check status values
    assert set(df_shots["shot_location_status"]).issubset({"OBSERVED", "NOT_AVAILABLE"})
    
    # For OBSERVED shots, check coordinate ranges
    obs_shots = df_shots[df_shots["shot_location_status"] == "OBSERVED"]
    assert (obs_shots["x_coord"] >= 0).all() and (obs_shots["x_coord"] <= 300).all()
    assert (obs_shots["y_coord"] >= 0).all() and (obs_shots["y_coord"] <= 300).all()

def test_mathematical_scoring_formula_in_player_games(db):
    """Verify PTS = FTM + 2*FG2M + 3*FG3M across player game logs."""
    df_players = db.query_df("""
        SELECT points, ftm, fg2m, fg3m
        FROM boxscore_player
        WHERE is_dnp = FALSE
    """)
    assert len(df_players) >= 900
    calc_pts = df_players["ftm"] + 2 * df_players["fg2m"] + 3 * df_players["fg3m"]
    assert (df_players["points"] == calc_pts).all()
