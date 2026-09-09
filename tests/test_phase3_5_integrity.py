"""Automated test suite for Phase 3.5 Idempotency, Mathematical Invariants & Incremental Ingestion."""

from pathlib import Path
import pandas as pd
import pytest

from python.database.duckdb_manager import DuckDBManager
from python.ingestion.base import NormalizedPayload
from python.models.canonical import Game

DERIVED_DIR = Path("data/derived")

@pytest.fixture(scope="module")
def db():
    manager = DuckDBManager()
    yield manager
    manager.close()

def test_game_data_quality_dataset_integrity():
    """Verify game_data_quality.parquet completeness and metric boundaries."""
    p_path = DERIVED_DIR / "game_data_quality.parquet"
    assert p_path.exists()
    df = pd.read_parquet(p_path)
    assert len(df) >= 48
    assert "composite_quality_score" in df.columns
    assert (df["composite_quality_score"] >= 0.0).all() and (df["composite_quality_score"] <= 1.0).all()

def test_idempotent_ingestion_simulation(db):
    """Verify that re-inserting existing payloads does not duplicate records in DuckDB."""
    initial_game_count = db.get_table_count("game")
    initial_player_count = db.get_table_count("player")
    
    # Query a sample existing game from database
    df_sample = db.query_df("SELECT * FROM game LIMIT 1")
    sample_game_id = df_sample["game_id"].iloc[0]
    
    # Attempt duplicate insert of the same game entity
    existing_game = Game(
        game_id=sample_game_id,
        season_id=df_sample["season_id"].iloc[0],
        competition_id=df_sample["competition_id"].iloc[0],
        game_date=df_sample["game_date"].iloc[0],
        home_team_id=df_sample["home_team_id"].iloc[0],
        away_team_id=df_sample["away_team_id"].iloc[0],
        home_score=int(df_sample["home_score"].iloc[0]),
        away_score=int(df_sample["away_score"].iloc[0]),
        game_status=df_sample["game_status"].iloc[0],
    )
    
    from datetime import datetime, timezone
    from python.models.canonical import SourceProvenance
    from python.models.enums import SourceType

    prov = SourceProvenance(
        provenance_id="PRV_TEST_SIM",
        source_type=SourceType.BOXSCORE,
        source_provider="TEST",
        source_file_path="test.json",
        source_file_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        ingestion_timestamp=datetime.now(timezone.utc),
        parser_version="1.0",
        pipeline_version="1.0",
    )
    payload = NormalizedPayload(provenance=prov, games=[existing_game])
    db.insert_normalized_payload(payload)
    
    # Verify row counts remain identical (idempotency guarantee)
    assert db.get_table_count("game") == initial_game_count
    assert db.get_table_count("player") == initial_player_count

def test_four_factors_mathematical_consistency(db):
    """Verify four factors bounds in view_team_game_ratings."""
    df_ratings = db.query_df("""
        SELECT efg_pct, tov_pct, orb_pct, ftr, ortg, drtg, net_rtg
        FROM view_team_game_ratings
        WHERE possessions > 40
    """)
    assert len(df_ratings) >= 50
    assert (df_ratings["efg_pct"] >= 0).all() and (df_ratings["efg_pct"] <= 100).all()
    assert (df_ratings["tov_pct"] >= 0).all() and (df_ratings["tov_pct"] <= 100).all()
    assert (df_ratings["orb_pct"] >= 0).all() and (df_ratings["orb_pct"] <= 100).all()
