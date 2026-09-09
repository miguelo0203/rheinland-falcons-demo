"""Automated test suite for Phase 6 Continuous Season Incremental Ingestion & Idempotency."""

import json
from pathlib import Path
import pandas as pd
import pytest

from python.database.duckdb_manager import DuckDBManager
from python.operations.incremental_ingestion import IncrementalIngestionEngine

RAW_DIR = Path("data/raw")
DERIVED_DIR = Path("data/derived")

@pytest.fixture(scope="module")
def db():
    manager = DuckDBManager()
    yield manager
    manager.close()

@pytest.fixture(scope="module")
def engine(db):
    return IncrementalIngestionEngine(db)

def test_incremental_ingestion_new_game_lifecycle(engine, db):
    """Test full lifecycle of a newly arriving FALCONS match with idempotency and raw preservation."""
    test_game_id = "GAM_9999991_TEST"
    test_season = "SEA_2025"
    test_payload = {
        "match_id": 9999991,
        "home_team": "Rheinland Falcons Basketball",
        "away_team": "Test Opponent",
        "home_score": 85,
        "away_score": 72,
        "status": "FINAL"
    }

    # 1. Clean previous test artifact if any
    db.execute(f"DELETE FROM boxscore_player WHERE game_id = '{test_game_id}';")
    db.execute(f"DELETE FROM boxscore_team WHERE game_id = '{test_game_id}';")
    db.execute(f"DELETE FROM shot WHERE game_id = '{test_game_id}';")
    db.execute(f"DELETE FROM game WHERE game_id = '{test_game_id}';")

    # 2. Ingest New Game
    res1 = engine.ingest_game(
        game_id=test_game_id,
        season_id=test_season,
        competition_id="JBBL_TEST",
        game_date="2025-04-20",
        home_team_id="TEM_DEMO_U16",
        away_team_id="TEM_1001",
        home_score=85,
        away_score=72,
        payload=test_payload,
        game_type="OFFICIAL",
        phase="PLAYOFFS",
    )
    assert res1["status"] == "INGESTED_NEW"
    
    # Verify raw file and SHA-256 manifest exist
    raw_path = RAW_DIR / "jbbl" / test_season / test_game_id / "match_raw.json"
    manifest_path = RAW_DIR / "jbbl" / test_season / test_game_id / "manifest.sha256"
    assert raw_path.exists()
    assert manifest_path.exists()
    assert len(manifest_path.read_text(encoding="utf-8").strip()) == 64

    # 3. Ingest SAME Game again -> Must produce true NO_OP_IDENTICAL
    res2 = engine.ingest_game(
        game_id=test_game_id,
        season_id=test_season,
        competition_id="JBBL_TEST",
        game_date="2025-04-20",
        home_team_id="TEM_DEMO_U16",
        away_team_id="TEM_1001",
        home_score=85,
        away_score=72,
        payload=test_payload,
        game_type="OFFICIAL",
        phase="PLAYOFFS",
    )
    assert res2["status"] == "NO_OP_IDENTICAL"

    # 4. Cleanup test game from database to preserve historical baseline
    db.execute(f"DELETE FROM boxscore_player WHERE game_id = '{test_game_id}';")
    db.execute(f"DELETE FROM boxscore_team WHERE game_id = '{test_game_id}';")
    db.execute(f"DELETE FROM shot WHERE game_id = '{test_game_id}';")
    db.execute(f"DELETE FROM game WHERE game_id = '{test_game_id}';")
    engine.recompute_dependencies(season_id="SEA_2025", game_type="OFFICIAL")
