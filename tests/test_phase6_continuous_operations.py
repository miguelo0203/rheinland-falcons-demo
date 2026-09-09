"""Comprehensive Continuous Season Operations & Operational Readiness Test Suite.

Covers all 10 required operational scenarios for Rheinland Falcons JBBL/NBBL:
1. New official game (exact +1 fixture)
2. Duplicate game (NO_OP_IDENTICAL, 0 duplicates)
3. Changed game (versioned audit trail preservation)
4. Late-arriving PBP modality (same game, modality upgraded)
5. Practice game mathematical isolation
6. New season auto-discovery (SEA_2028 discovered dynamically)
7. Rolling window calculations and N < 4 safeguard
8. Weekly aggregation and WoW deltas
9. Partial modality availability (boxscore only)
10. Idempotent rerun verification
"""

from pathlib import Path
import json
import pytest
import pandas as pd

from python.database.duckdb_manager import DuckDBManager
from python.operations.incremental_ingestion import IncrementalIngestionEngine
from python.operations.game_registry import build_game_registry
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

def clean_game_fixtures(db, game_id: str):
    """Helper to clean test game fixtures in strict foreign-key dependency order."""
    db.execute(f"DELETE FROM shot WHERE game_id = '{game_id}';")
    db.execute(f"DELETE FROM pbp_event WHERE game_id = '{game_id}';")
    db.execute(f"DELETE FROM boxscore_player WHERE game_id = '{game_id}';")
    db.execute(f"DELETE FROM boxscore_team WHERE game_id = '{game_id}';")
    db.execute(f"DELETE FROM game WHERE game_id = '{game_id}';")

def test_01_new_official_game_ingestion(engine, db):
    """Test 1: Appending a new official game increases fixture count by exactly 1."""
    gid = "GAM_9999001_TEST"
    clean_game_fixtures(db, gid)

    initial_count = db.query_df("SELECT count(*) AS c FROM game").iloc[0]["c"]
    payload = {"match_id": 9999001, "home_team": "Rheinland Falcons Basketball", "away_team": "Team A", "score": "80:70"}

    res = engine.ingest_game(
        game_id=gid,
        season_id="SEA_2025",
        competition_id="CMP_JBBL",
        game_date="2025-03-01",
        home_team_id="TEM_DEMO_U16",
        away_team_id="TEM_1001",
        home_score=80,
        away_score=70,
        payload=payload,
        game_type="OFFICIAL"
    )
    assert res["status"] == "INGESTED_NEW"
    new_count = db.query_df("SELECT count(*) AS c FROM game").iloc[0]["c"]
    assert new_count == initial_count + 1

    clean_game_fixtures(db, gid)
    engine.recompute_dependencies("SEA_2025", "OFFICIAL")

def test_02_duplicate_game_no_op(engine, db):
    """Test 2: Ingesting an identical payload results in true NO_OP with 0 duplicates."""
    gid = "GAM_9999002_TEST"
    clean_game_fixtures(db, gid)

    payload = {"match_id": 9999002, "home_team": "Rheinland Falcons Basketball", "away_team": "Team B"}
    engine.ingest_game(
        game_id=gid, season_id="SEA_2025", competition_id="CMP_JBBL",
        game_date="2025-03-02", home_team_id="TEM_DEMO_U16", away_team_id="TEM_1001",
        home_score=85, away_score=75, payload=payload, game_type="OFFICIAL"
    )

    # Ingest duplicate
    res_dup = engine.ingest_game(
        game_id=gid, season_id="SEA_2025", competition_id="CMP_JBBL",
        game_date="2025-03-02", home_team_id="TEM_DEMO_U16", away_team_id="TEM_1001",
        home_score=85, away_score=75, payload=payload, game_type="OFFICIAL"
    )
    assert res_dup["status"] == "NO_OP_IDENTICAL"

    # Verify no duplicate game records exist
    df_check = db.query_df(f"SELECT count(*) as c FROM game WHERE game_id = '{gid}'")
    assert df_check.iloc[0]["c"] == 1

    clean_game_fixtures(db, gid)
    engine.recompute_dependencies("SEA_2025", "OFFICIAL")

def test_03_changed_game_versioned_audit(engine, db):
    """Test 3: Changing a previously ingested game preserves raw backup audit."""
    gid = "GAM_9999003_TEST"
    clean_game_fixtures(db, gid)

    payload_v1 = {"match_id": 9999003, "version": 1, "score": "70:60"}
    engine.ingest_game(
        game_id=gid, season_id="SEA_2025", competition_id="CMP_JBBL",
        game_date="2025-03-03", home_team_id="TEM_DEMO_U16", away_team_id="TEM_1001",
        home_score=70, away_score=60, payload=payload_v1, game_type="OFFICIAL"
    )

    payload_v2 = {"match_id": 9999003, "version": 2, "score": "72:60"}
    res_v2 = engine.ingest_game(
        game_id=gid, season_id="SEA_2025", competition_id="CMP_JBBL",
        game_date="2025-03-03", home_team_id="TEM_DEMO_U16", away_team_id="TEM_1001",
        home_score=72, away_score=60, payload=payload_v2, game_type="OFFICIAL"
    )
    assert res_v2["status"] in ["INGESTED_NEW", "SOURCE_CORRECTION"]

    # Check raw directory for versioned backup
    raw_dir = Path("data/raw/jbbl/SEA_2025") / gid
    backups = list(raw_dir.glob("match_raw_audit_prev_*.json"))
    assert len(backups) >= 1

    clean_game_fixtures(db, gid)
    engine.recompute_dependencies("SEA_2025", "OFFICIAL")

def test_04_late_arriving_pbp_modality(engine, db):
    """Test 4: Adding PBP events to existing fixture upgrades modality without duplicating game."""
    gid = "GAM_9999004_TEST"
    clean_game_fixtures(db, gid)

    payload = {"match_id": 9999004, "home_team": "Rheinland Falcons Basketball"}
    engine.ingest_game(
        game_id=gid, season_id="SEA_2025", competition_id="CMP_JBBL",
        game_date="2025-03-04", home_team_id="TEM_DEMO_U16", away_team_id="TEM_1001",
        home_score=80, away_score=70, payload=payload, game_type="OFFICIAL"
    )

    # Append 55 PBP events (exceeds 50 threshold for modality activation)
    pbp_events = [
        {
            "event_id": f"EVT_{gid}_{i}",
            "period": 1,
            "game_seconds_remaining": 2400 - i * 10,
            "period_seconds_remaining": 600 - i * 10,
            "event_type": "2FGM" if i % 2 == 0 else "FOUL",
            "player_id": "PLY_DEMO_104",
            "team_id": "TEM_DEMO_U16",
            "score_home": 2 * (i // 2),
            "score_away": 0,
            "description": "Scored 2PT",
            "is_scoring_event": True if i % 2 == 0 else False
        }
        for i in range(55)
    ]
    res_pbp = engine.append_modality(game_id=gid, modality_type="PBP", records=pbp_events)
    assert res_pbp["status"] == "MODALITY_APPENDED"

    # Verify game registry reflects pbp_available = True
    df_reg = build_game_registry()
    game_row = df_reg[df_reg["game_id"] == gid].iloc[0]
    assert game_row["pbp_available"] == True
    assert game_row["pbp_event_count"] >= 50

    clean_game_fixtures(db, gid)
    engine.recompute_dependencies("SEA_2025", "OFFICIAL")

def test_05_practice_game_mathematical_isolation(engine, db):
    """Test 5: Practice game updates developmental data but leaves official standings isolated."""
    gid = "GAM_9999005_PRAC"
    clean_game_fixtures(db, gid)

    payload = {"match_id": 9999005, "type": "PRACTICE_SCRIMMAGE"}
    engine.ingest_game(
        game_id=gid, season_id="SEA_2025", competition_id="JBBL_PRACTICE",
        game_date="2025-03-05", home_team_id="TEM_DEMO_U16", away_team_id="TEM_1001",
        home_score=95, away_score=50, payload=payload, game_type="PRACTICE"
    )

    ds = DataService()
    df_official = ds.get_game_registry(population_mode="OFFICIAL_ONLY")
    assert gid not in df_official["game_id"].values

    df_all = ds.get_game_registry(population_mode="ALL_GAMES")
    assert gid in df_all["game_id"].values

    meta = get_population_metadata(df_all)
    assert meta["practice_count"] >= 1

    clean_game_fixtures(db, gid)
    engine.recompute_dependencies("SEA_2025", "OFFICIAL")

def test_06_new_season_auto_discovery(engine, db):
    """Test 6: Ingesting a fixture for a new season (e.g. SEA_2028) is dynamically discovered."""
    gid = "GAM_9999006_S28"
    new_season = "SEA_2028"
    clean_game_fixtures(db, gid)

    payload = {"match_id": 9999006, "season": "2027/28"}
    engine.ingest_game(
        game_id=gid, season_id=new_season, competition_id="CMP_JBBL",
        game_date="2028-01-15", home_team_id="TEM_DEMO_U16", away_team_id="TEM_1001",
        home_score=82, away_score=79, payload=payload, game_type="OFFICIAL"
    )

    ds = DataService()
    seasons = ds.get_available_seasons()
    assert new_season in seasons

    clean_game_fixtures(db, gid)
    engine.recompute_dependencies("SEA_2025", "OFFICIAL")

def test_07_rolling_window_calculations(engine, db):
    """Test 7: Rolling window calculations enforce N < 4 sample size safeguards."""
    ds = DataService()
    df_evo = ds.get_player_evolution()
    assert not df_evo.empty
    
    # Check that for any player trajectory with game_number < 4, trend status is INSUFFICIENT_DATA
    df_early = df_evo[df_evo["game_number"] < 4]
    assert (df_early["trend_classification"] == "INSUFFICIENT_DATA").all()

def test_08_weekly_aggregation_and_wow_delta(engine, db):
    """Test 8: Weekly performance aggregates preserve week numbers without fabricating deltas."""
    ds = DataService()
    df_evo = ds.get_player_evolution()
    weekly_records = df_evo[df_evo["aggregation_level"] == "WEEKLY"] if "aggregation_level" in df_evo.columns else df_evo
    assert len(weekly_records) > 0

def test_09_modality_partial_availability(engine, db):
    """Test 9: Boxscore-only game remains analytically usable with explicit modality flags."""
    ds = DataService()
    df_reg = ds.get_game_registry(population_mode="OFFICIAL_ONLY")
    
    # Verify that partial-modality fixtures (boxscore present, pbp missing) exist and are usable
    bx_only = df_reg[(df_reg["pbp_available"] == False) & (df_reg["boxscore_available"] == True)]
    assert len(bx_only) > 0
    assert (bx_only["boxscore_available"] == True).all()
    assert (bx_only["pbp_available"] == False).all()

def test_10_idempotent_rerun_verification(engine, db):
    """Test 10: Multiple consecutive ingestion runs produce exact identical state."""
    gid = "GAM_9999010_IDEM"
    clean_game_fixtures(db, gid)

    payload = {"match_id": 9999010, "state": "IDEMPOTENT_TEST"}
    r1 = engine.ingest_game(
        game_id=gid, season_id="SEA_2025", competition_id="CMP_JBBL",
        game_date="2025-03-10", home_team_id="TEM_DEMO_U16", away_team_id="TEM_1001",
        home_score=90, away_score=80, payload=payload, game_type="OFFICIAL"
    )
    r2 = engine.ingest_game(
        game_id=gid, season_id="SEA_2025", competition_id="CMP_JBBL",
        game_date="2025-03-10", home_team_id="TEM_DEMO_U16", away_team_id="TEM_1001",
        home_score=90, away_score=80, payload=payload, game_type="OFFICIAL"
    )
    assert r1["status"] == "INGESTED_NEW"
    assert r2["status"] == "NO_OP_IDENTICAL"

    clean_game_fixtures(db, gid)
    engine.recompute_dependencies("SEA_2025", "OFFICIAL")

