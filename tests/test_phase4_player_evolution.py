"""Automated test suite for Phase 4 Longitudinal Player Performance & Role Evolution."""

from pathlib import Path
import pandas as pd
import pytest

DERIVED_DIR = Path("data/derived")

def test_player_game_analysis_dataset():
    """Verify player_game_analysis columns, rate metrics, and starter flags."""
    df_pga = pd.read_parquet(DERIVED_DIR / "player_game_analysis.parquet")
    assert len(df_pga) >= 1000
    
    expected_cols = [
        "player_id", "canonical_name", "team_id", "game_id", "minutes",
        "pts_per_40", "reb_per_40", "ast_per_40", "ts_pct", "is_starter"
    ]
    for c in expected_cols:
        assert c in df_pga.columns, f"Missing column {c} in player_game_analysis"

def test_player_rolling_analysis_role_tracking():
    """Verify player_rolling_analysis role changes and small-sample safeguards."""
    df_pra = pd.read_parquet(DERIVED_DIR / "player_rolling_analysis.parquet")
    assert len(df_pra) >= 900
    
    assert "observed_role_change" in df_pra.columns
    assert "interpreted_role_change" in df_pra.columns
    assert "trend_classification" in df_pra.columns
    assert "sample_size_flag" in df_pra.columns

def test_player_weekly_analysis_aggregations():
    """Verify player_weekly_analysis week-over-week deltas and games played."""
    df_pwa = pd.read_parquet(DERIVED_DIR / "player_weekly_analysis.parquet")
    assert len(df_pwa) >= 800
    assert (df_pwa["games_played"] >= 1).all()
    assert "delta_ppg_prev_week" in df_pwa.columns
