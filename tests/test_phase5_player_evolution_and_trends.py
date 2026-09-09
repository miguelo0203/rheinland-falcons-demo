"""Automated test suite for Phase 5 Player Evolution and Rule-Based Trend Classifications."""

from pathlib import Path
import pandas as pd
import pytest

from python.analytics.phase5_player_evolution import classify_player_trend, compute_trend_slope

DERIVED_DIR = Path("data/derived")
DOCS_DIR = Path("docs")

def test_player_evolution_dataset_structure():
    """Verify player_evolution.parquet columns, ordering, and season phase assignments."""
    p_path = DERIVED_DIR / "player_evolution.parquet"
    assert p_path.exists()
    df_pe = pd.read_parquet(p_path)
    assert len(df_pe) >= 900
    
    expected_cols = [
        "player_id", "canonical_name", "game_number", "season_phase", "minutes", "points",
        "delta_pts_vs_prev_game", "delta_ts_vs_prev_game", "rolling_4_ppg",
        "delta_rolling_4_vs_baseline_ppg", "trend_classification", "trend_slope"
    ]
    for c in expected_cols:
        assert c in df_pe.columns, f"Missing column {c} in player_evolution"
        
    # Season phases should only be valid enums
    assert set(df_pe["season_phase"]).issubset({"EARLY_SEASON", "MID_SEASON", "LATE_SEASON_PLAYOFFS"})

def test_rule_based_trend_classification_synthetic_logic():
    """Verify rule-based trend classification logic against synthetic test vectors."""
    # 1. Improving pattern: 10 -> 12 -> 16 -> 20 (N=4, slope > 0.5, diff >= 2.0 vs baseline 12.0)
    improving_pts = [10.0, 12.0, 16.0, 20.0]
    t_class, slope, _ = classify_player_trend(improving_pts, [50.0, 55.0, 60.0, 65.0], baseline_ppg=12.0)
    assert t_class == "IMPROVING"
    assert slope > 0.5
    
    # 2. Declining pattern: 20 -> 16 -> 12 -> 10 (N=4, slope < -0.5, diff <= -2.0 vs baseline 18.0)
    declining_pts = [20.0, 16.0, 12.0, 10.0]
    t_class, slope, _ = classify_player_trend(declining_pts, [65.0, 60.0, 55.0, 50.0], baseline_ppg=18.0)
    assert t_class == "DECLINING"
    assert slope < -0.5
    
    # 3. Stable pattern: 15.0, 15.0, 16.0, 15.0 (N=4, |slope| <= 0.5, |diff| <= 1.5 vs baseline 15.0)
    stable_pts = [15.0, 15.0, 16.0, 15.0]
    t_class, slope, _ = classify_player_trend(stable_pts, [50.0, 50.0, 52.0, 50.0], baseline_ppg=15.0)
    assert t_class == "STABLE"
    
    # 4. Insufficient data: N < 4
    short_pts = [15.0, 18.0, 20.0]
    t_class, _, _ = classify_player_trend(short_pts, [50.0, 55.0, 60.0], baseline_ppg=15.0)
    assert t_class == "INSUFFICIENT_DATA"

def test_player_intelligence_profiles():
    """Verify player_intelligence.parquet production and role definitions."""
    p_path = DERIVED_DIR / "player_intelligence.parquet"
    assert p_path.exists()
    df_pi = pd.read_parquet(p_path)
    assert len(df_pi) >= 300
    
    assert "primary_role" in df_pi.columns
    assert "pts_per_40" in df_pi.columns
    assert "trend_classification" in df_pi.columns
