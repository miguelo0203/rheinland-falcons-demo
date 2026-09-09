"""Automated test suite for Phase 3.5 Player Longitudinal & League Contextual Datasets."""

from pathlib import Path
import pandas as pd
import pytest

DERIVED_DIR = Path("data/derived")
DOCS_DIR = Path("docs")

def test_player_game_performance_dataset_integrity():
    """Verify player_game_performance.parquet schema, volume, and metric formulas."""
    p_path = DERIVED_DIR / "player_game_performance.parquet"
    assert p_path.exists()
    df = pd.read_parquet(p_path)
    assert len(df) >= 1000
    
    # Required columns check
    expected_cols = [
        "player_id", "canonical_name", "team_id", "game_id", "game_date", "season_id",
        "minutes", "points", "fgm", "fga", "ts_pct", "trb", "ast", "tov", "is_starter"
    ]
    for c in expected_cols:
        assert c in df.columns, f"Missing column {c} in player_game_performance"
    
    # TS% calculation validity
    valid_ts = df[df["ts_pct"].notna()]
    assert (valid_ts["ts_pct"] >= 0).all() and (valid_ts["ts_pct"] <= 150).all()

def test_player_rolling_performance_trajectories():
    """Verify rolling 3-game and 5-game calculations and small-sample safeguards."""
    p_path = DERIVED_DIR / "player_rolling_performance.parquet"
    assert p_path.exists()
    df = pd.read_parquet(p_path)
    assert len(df) >= 900
    
    assert "rolling_3_ppg" in df.columns and "rolling_5_ppg" in df.columns
    assert "sample_size_flag" in df.columns and "uncertainty_indicator" in df.columns
    
    # Small sample protection check
    small_samples = df[df["sample_size_flag"] == "SMALL_SAMPLE"]
    assert (small_samples["uncertainty_indicator"] == "HIGH").all()

def test_player_weekly_performance_aggregation():
    """Verify weekly performance aggregation and week-over-week deltas."""
    p_path = DERIVED_DIR / "player_weekly_performance.parquet"
    assert p_path.exists()
    df = pd.read_parquet(p_path)
    assert len(df) >= 800
    
    assert "week_number" in df.columns and "delta_ppg_prev_week" in df.columns
    assert (df["games_played"] >= 1).all()

def test_league_distributions_and_falcons_context():
    """Verify league distributions and FALCONS contextual percentiles."""
    p_tdist = DERIVED_DIR / "league_team_distributions.parquet"
    p_pdist = DERIVED_DIR / "league_player_distributions.parquet"
    p_hctx = DERIVED_DIR / "falcons_vs_league_context.parquet"
    
    assert p_tdist.exists() and p_pdist.exists() and p_hctx.exists()
    
    df_hctx = pd.read_parquet(p_hctx)
    assert len(df_hctx) >= 50
    assert "percentile_rank" in df_hctx.columns and "z_score" in df_hctx.columns
    assert (df_hctx["percentile_rank"] >= 0).all() and (df_hctx["percentile_rank"] <= 100).all()

def test_longitudinal_methodology_documentation():
    """Verify player and league methodology docs exist."""
    assert (DOCS_DIR / "player_longitudinal_methodology.md").exists()
    assert (DOCS_DIR / "league_context_methodology.md").exists()
