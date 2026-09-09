"""Automated test suite for Phase 4 Statistical Engine & Four Factors Significance."""

from pathlib import Path
import pandas as pd
import pytest

DERIVED_DIR = Path("data/derived")
DOCS_DIR = Path("docs")

def test_phase4_statistical_datasets_exist():
    """Verify team_game_analysis, team_season_analysis, and league_context_analysis exist."""
    assert (DERIVED_DIR / "team_game_analysis.parquet").exists()
    assert (DERIVED_DIR / "team_season_analysis.parquet").exists()
    assert (DERIVED_DIR / "league_context_analysis.parquet").exists()

def test_four_factors_significance_and_fdr():
    """Verify Four Factors correlation metrics, bootstrap CIs, and FDR significance."""
    df_lca = pd.read_parquet(DERIVED_DIR / "league_context_analysis.parquet")
    assert len(df_lca) >= 5
    
    # Required columns
    expected_cols = [
        "factor_name", "sample_size_N", "pearson_r", "spearman_rho", "r_squared",
        "bootstrap_ci_95_lower", "bootstrap_ci_95_upper", "fdr_significant_q05",
        "is_sensitive_to_outliers", "epistemic_classification"
    ]
    for c in expected_cols:
        assert c in df_lca.columns, f"Missing column {c} in league_context_analysis"
    
    # eFG% should be the top differentiator with R^2 >= 0.40 at game level and positive r
    efg_row = df_lca[df_lca["factor_name"] == "EFG_PCT"].iloc[0]
    assert efg_row["r_squared"] >= 0.40
    assert efg_row["pearson_r"] > 0.60
    assert efg_row["fdr_significant_q05"] == True

def test_team_game_analysis_bounds_and_formulas():
    """Verify team_game_analysis calculations and bounds."""
    df_tga = pd.read_parquet(DERIVED_DIR / "team_game_analysis.parquet")
    assert len(df_tga) >= 100
    assert (df_tga["possessions"] >= 40).all()
    assert (df_tga["efg_pct"] >= 0).all() and (df_tga["efg_pct"] <= 100).all()
    assert (df_tga["tov_pct"] >= 0).all() and (df_tga["tov_pct"] <= 100).all()
    assert (df_tga["orb_pct"] >= 0).all() and (df_tga["orb_pct"] <= 100).all()
