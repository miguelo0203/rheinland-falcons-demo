"""Automated test suite for Phase 6 Practice / Scrimmage Game Population Isolation."""

from pathlib import Path
import pandas as pd
import pytest

from python.database.duckdb_manager import DuckDBManager
from python.operations.incremental_ingestion import IncrementalIngestionEngine
from python.analytics.population_filter import filter_by_population, get_population_metadata
from app.services.data_service import DataService

@pytest.fixture(scope="module")
def db():
    manager = DuckDBManager()
    yield manager
    manager.close()

@pytest.fixture(scope="module")
def engine(db):
    return IncrementalIngestionEngine(db)

def test_practice_game_mathematical_isolation(engine, db):
    """Verify that PRACTICE games do not contaminate OFFICIAL competition populations."""
    prac_game_id = "GAM_8888881_PRAC"
    prac_payload = {
        "match_id": 8888881,
        "type": "PRACTICE_SCRIMMAGE",
        "home_team": "Rheinland Falcons Basketball",
        "away_team": "Internal Academy Scrimmage",
        "home_score": 90,
        "away_score": 60
    }

    # Ingest Practice Game
    engine.ingest_game(
        game_id=prac_game_id,
        season_id="SEA_2025",
        competition_id="JBBL_PRACTICE",
        game_date="2025-05-01",
        home_team_id="TEM_DEMO_U16",
        away_team_id="TEM_1001",
        home_score=90,
        away_score=60,
        payload=prac_payload,
        game_type="PRACTICE",
    )

    ds = DataService()
    
    # 1. Query Official Population
    df_official = ds.get_game_registry(population_mode="OFFICIAL_ONLY")
    assert prac_game_id not in df_official["game_id"].values
    
    # 2. Query All Games Population (Official + Practice)
    df_all = ds.get_game_registry(population_mode="ALL_GAMES")
    assert prac_game_id in df_all["game_id"].values
    
    # 3. Verify Population Metadata explicitly detects practice game
    pop_meta = get_population_metadata(df_all)
    assert pop_meta["practice_count"] >= 1

    # Cleanup test practice game
    db.execute(f"DELETE FROM boxscore_player WHERE game_id = '{prac_game_id}';")
    db.execute(f"DELETE FROM boxscore_team WHERE game_id = '{prac_game_id}';")
    db.execute(f"DELETE FROM shot WHERE game_id = '{prac_game_id}';")
    db.execute(f"DELETE FROM game WHERE game_id = '{prac_game_id}';")
    engine.recompute_dependencies(season_id="SEA_2025", game_type="OFFICIAL")
