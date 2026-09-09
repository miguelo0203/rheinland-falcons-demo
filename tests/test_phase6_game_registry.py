"""Automated test suite for Phase 6 Game Registry & Modality Denominators."""

from pathlib import Path
import pandas as pd
import pytest

from python.operations.game_registry import build_game_registry

DERIVED_DIR = Path("data/derived")
DOCS_DIR = Path("docs")

def test_canonical_game_registry_dataset():
    """Verify game_registry.parquet schema, modality flags, and analytical tiers."""
    df_reg = build_game_registry()
    assert len(df_reg) >= 48
    
    required_cols = [
        "game_id", "season_id", "competition_id", "game_type", "phase",
        "home_team_id", "away_team_id", "home_score", "away_score",
        "is_official_competition", "boxscore_available", "player_boxscore_available",
        "pbp_available", "shot_available", "coordinate_available", "analytical_tier"
    ]
    for col in required_cols:
        assert col in df_reg.columns, f"Missing {col} in game_registry"
        
    # Check that official competition games are recognized
    df_official = df_reg[df_reg["game_type"] == "OFFICIAL"]
    assert (df_official["is_official_competition"] == True).all()

def test_game_registry_documentation_exists():
    """Verify that docs/game_registry_and_incremental_operations.md exists and is non-empty."""
    doc_path = DOCS_DIR / "game_registry_and_incremental_operations.md"
    assert doc_path.exists()
    content = doc_path.read_text(encoding="utf-8")
    assert len(content) > 300
    assert "OFFICIAL" in content
