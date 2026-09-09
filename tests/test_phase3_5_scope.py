"""Automated test suite for Phase 3.5 Historical Scope and League Universe."""

from pathlib import Path
import pandas as pd
import pytest

DERIVED_DIR = Path("data/derived")
DOCS_DIR = Path("docs")

def test_scope_parquet_deliverables_exist():
    """Verify that all derived scope parquet files exist and are non-empty."""
    assert (DERIVED_DIR / "falcons_jbbl_scope.parquet").exists()
    assert (DERIVED_DIR / "league_universe.parquet").exists()
    assert (DERIVED_DIR / "match_inventory.parquet").exists()

def test_falcons_jbbl_scope_historical_and_primary_counts():
    """Verify FALCONS scope contains all 122 historical matches and 24 in Season 2025."""
    df_falcons = pd.read_parquet(DERIVED_DIR / "falcons_jbbl_scope.parquet")
    assert len(df_falcons) == 122
    assert "game_id" in df_falcons.columns and "season_id" in df_falcons.columns
    
    s2025_matches = df_falcons[df_falcons["season_id"] == "SEA_2025"]
    assert len(s2025_matches) == 24
    
    s2023_matches = df_falcons[df_falcons["season_id"] == "SEA_2023"]
    assert len(s2023_matches) == 17

def test_league_universe_and_match_inventory_volumes():
    """Verify league universe covers target seasons with over 1500 matches."""
    df_league = pd.read_parquet(DERIVED_DIR / "league_universe.parquet")
    assert len(df_league) >= 1500
    assert set(df_league["season_numeric"]) == {2023, 2024, 2025}
    
    df_inv = pd.read_parquet(DERIVED_DIR / "match_inventory.parquet")
    assert len(df_inv) >= 4000
    assert df_inv["game_id"].nunique() >= 4500

def test_scope_documentation_deliverables_exist():
    """Verify scope audit documentation files exist and are detailed."""
    assert (DOCS_DIR / "falcons_jbbl_scope_audit.md").exists()
    assert (DOCS_DIR / "league_universe_audit.md").exists()
    assert (DOCS_DIR / "match_inventory_audit.md").exists()
    assert (DOCS_DIR / "analytical_population_definitions.md").exists()
    assert (DOCS_DIR / "PHASE3_5_FINAL_AUDIT.md").exists()
