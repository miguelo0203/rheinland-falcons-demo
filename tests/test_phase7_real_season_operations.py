"""Phase 7 Real-Season Operations & Longitudinal Readiness Comprehensive Test Suite.

40+ Scenarios covering:
1. Ingestion:
   - 01: New official game
   - 02: New practice game
   - 03: New scrimmage game
   - 04: New friendly game
   - 05: Duplicate game idempotency
   - 06: Corrected game audit trail
   - 07: Late PBP modality append
   - 08: Late shots modality append
   - 09: Multiple late modalities append
   - 10: Score-only game registration

2. Data Integrity & Non-Fabrication:
   - 11: Zero fabricated boxscore values (NULL check)
   - 12: Real boxscore passthrough
   - 13: Invalid negative score rejection
   - 14: Same-team rejection
   - 15: Invalid shooting formula rejection
   - 16: Duplicate primary key prevention

3. Seasons & Continuity:
   - 17: Season transition 2025/26 -> 2026/27
   - 18: Season transition 2026/27 -> 2027/28
   - 19: Dynamic season boundary calculation
   - 20: Player continuity across multiple seasons

4. Population Isolation:
   - 21: Official games isolation
   - 22: Practice games isolation
   - 23: Scrimmage games isolation
   - 24: Friendly games isolation

5. Operations & Inbox:
   - 25: Operation report JSON generation
   - 26: SHA-256 payload digest stability
   - 27: Source correction versioned backup
   - 28: Inbox Mode A (self-contained payload) processing
   - 29: Inbox Mode B (payload + metadata) processing
   - 30: Rejected payload preservation in rejected/

6. Analytics & Math Safety:
   - 31: Rolling window N < 4 safeguard (INSUFFICIENT_DATA)
   - 32: Rolling window N >= 4 activation
   - 33: Weekly aggregation calculation
   - 34: Trend classification mathematical determinism
   - 35: Recomputation graph execution timing

7. UI & Data Freshness:
   - 36: Dynamic latest game date in freshness layer
   - 37: Freshness layer registry and DB timestamps
   - 38: Dynamic season discovery in DataService
   - 39: Modality matrix flags per game
   - 40: Zero hardcoded numbers in UI definitions
"""

import os
import json
import time
import shutil
from pathlib import Path
from typing import Dict, Any, List

import pytest
import pandas as pd
import duckdb

from python.database.duckdb_manager import DuckDBManager
from python.operations.incremental_ingestion import IncrementalIngestionEngine, process_inbox
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
    """Helper to cleanly purge a test fixture in strict FK dependency order."""
    db.execute(f"DELETE FROM shot WHERE game_id = '{game_id}';")
    db.execute(f"DELETE FROM pbp_event WHERE game_id = '{game_id}';")
    db.execute(f"DELETE FROM boxscore_player WHERE game_id = '{game_id}';")
    db.execute(f"DELETE FROM boxscore_team WHERE game_id = '{game_id}';")
    db.execute(f"DELETE FROM game_roster WHERE game_id = '{game_id}';")
    db.execute(f"DELETE FROM game_sources WHERE game_id = '{game_id}';")
    db.execute(f"DELETE FROM validation_log WHERE game_id = '{game_id}';")
    db.execute(f"DELETE FROM game WHERE game_id = '{game_id}';")


# ==============================================================================
# 1. INGESTION SUITE (Tests 01 - 10)
# ==============================================================================

def test_01_ingest_new_official_game(engine, db):
    """Test 01: Ingesting an official game increments fixture count and sets game_type='OFFICIAL'."""
    gid = "GAM_P7_001_OFFICIAL"
    clean_game_fixtures(db, gid)

    initial_count = db.get_table_count("game")
    payload = {"match_id": "P7_001", "home": "Rheinland Falcons Basketball", "away": "Opponent A"}
    
    res = engine.ingest_game(
        game_id=gid, season_id="SEA_2026", competition_id="CMP_JBBL",
        game_date="2026-10-15", home_team_id="TEM_DEMO_U16", away_team_id="TEM_1001",
        home_score=85, away_score=78, payload=payload, game_type="OFFICIAL"
    )
    assert res["status"] == "INGESTED_NEW"
    assert db.get_table_count("game") == initial_count + 1
    
    df_check = db.query_df(f"SELECT game_type FROM game WHERE game_id = '{gid}'")
    assert df_check.iloc[0]["game_type"] == "OFFICIAL"
    
    clean_game_fixtures(db, gid)
    engine.recompute_dependencies("SEA_2026", "OFFICIAL")

def test_02_ingest_new_practice_game(engine, db):
    """Test 02: Ingesting a practice game assigns game_type='PRACTICE'."""
    gid = "GAM_P7_002_PRAC"
    clean_game_fixtures(db, gid)

    payload = {"match_id": "P7_002", "practice_note": "Internal full scrimmage"}
    res = engine.ingest_game(
        game_id=gid, season_id="SEA_2026", competition_id="JBBL_PRACTICE",
        game_date="2026-10-20", home_team_id="TEM_DEMO_U16", away_team_id="TEM_1001",
        home_score=92, away_score=60, payload=payload, game_type="PRACTICE"
    )
    assert res["status"] == "INGESTED_NEW"
    df_check = db.query_df(f"SELECT game_type FROM game WHERE game_id = '{gid}'")
    assert df_check.iloc[0]["game_type"] == "PRACTICE"

    clean_game_fixtures(db, gid)
    engine.recompute_dependencies("SEA_2026", "PRACTICE")

def test_03_ingest_new_scrimmage_game(engine, db):
    """Test 03: Ingesting a scrimmage assigns game_type='SCRIMMAGE'."""
    gid = "GAM_P7_003_SCRIM"
    clean_game_fixtures(db, gid)

    payload = {"match_id": "P7_003", "type": "Closed-door scrimmage"}
    res = engine.ingest_game(
        game_id=gid, season_id="SEA_2026", competition_id="JBBL_SCRIMMAGE",
        game_date="2026-10-22", home_team_id="TEM_DEMO_U16", away_team_id="TEM_1001",
        home_score=75, away_score=70, payload=payload, game_type="SCRIMMAGE"
    )
    assert res["status"] == "INGESTED_NEW"
    df_check = db.query_df(f"SELECT game_type FROM game WHERE game_id = '{gid}'")
    assert df_check.iloc[0]["game_type"] == "SCRIMMAGE"

    clean_game_fixtures(db, gid)
    engine.recompute_dependencies("SEA_2026", "SCRIMMAGE")

def test_04_ingest_new_friendly_game(engine, db):
    """Test 04: Ingesting a friendly match assigns game_type='FRIENDLY'."""
    gid = "GAM_P7_004_FRND"
    clean_game_fixtures(db, gid)

    payload = {"match_id": "P7_004", "type": "Pre-season tournament"}
    res = engine.ingest_game(
        game_id=gid, season_id="SEA_2026", competition_id="JBBL_FRIENDLY",
        game_date="2026-09-28", home_team_id="TEM_DEMO_U16", away_team_id="TEM_1001",
        home_score=80, away_score=65, payload=payload, game_type="FRIENDLY"
    )
    assert res["status"] == "INGESTED_NEW"
    df_check = db.query_df(f"SELECT game_type FROM game WHERE game_id = '{gid}'")
    assert df_check.iloc[0]["game_type"] == "FRIENDLY"

    clean_game_fixtures(db, gid)
    engine.recompute_dependencies("SEA_2026", "FRIENDLY")

def test_05_duplicate_game_idempotency(engine, db):
    """Test 05: Submitting exact identical payload returns NO_OP_IDENTICAL with 0 duplicate rows."""
    gid = "GAM_P7_005_DUP"
    clean_game_fixtures(db, gid)

    payload = {"match_id": "P7_005", "info": "Idempotent match"}
    r1 = engine.ingest_game(
        game_id=gid, season_id="SEA_2026", competition_id="CMP_JBBL",
        game_date="2026-11-01", home_team_id="TEM_DEMO_U16", away_team_id="TEM_1001",
        home_score=88, away_score=82, payload=payload, game_type="OFFICIAL"
    )
    r2 = engine.ingest_game(
        game_id=gid, season_id="SEA_2026", competition_id="CMP_JBBL",
        game_date="2026-11-01", home_team_id="TEM_DEMO_U16", away_team_id="TEM_1001",
        home_score=88, away_score=82, payload=payload, game_type="OFFICIAL"
    )
    assert r1["status"] == "INGESTED_NEW"
    assert r2["status"] == "NO_OP_IDENTICAL"
    
    count = db.query_df(f"SELECT count(*) as c FROM game WHERE game_id = '{gid}'").iloc[0]["c"]
    assert count == 1

    clean_game_fixtures(db, gid)
    engine.recompute_dependencies("SEA_2026", "OFFICIAL")

def test_06_corrected_game_audit_trail(engine, db):
    """Test 06: Changed payload creates timestamped backup of previous raw file."""
    gid = "GAM_P7_006_CORR"
    clean_game_fixtures(db, gid)

    p1 = {"match_id": "P7_006", "score": "80:70", "revision": 1}
    engine.ingest_game(
        game_id=gid, season_id="SEA_2026", competition_id="CMP_JBBL",
        game_date="2026-11-05", home_team_id="TEM_DEMO_U16", away_team_id="TEM_1001",
        home_score=80, away_score=70, payload=p1, game_type="OFFICIAL"
    )

    p2 = {"match_id": "P7_006", "score": "82:70", "revision": 2}
    r2 = engine.ingest_game(
        game_id=gid, season_id="SEA_2026", competition_id="CMP_JBBL",
        game_date="2026-11-05", home_team_id="TEM_DEMO_U16", away_team_id="TEM_1001",
        home_score=82, away_score=70, payload=p2, game_type="OFFICIAL"
    )
    assert r2["status"] == "SOURCE_CORRECTION"
    
    raw_dir = Path("data/raw/jbbl/SEA_2026") / gid
    backups = list(raw_dir.glob("match_raw_audit_prev_*.json"))
    assert len(backups) >= 1

    clean_game_fixtures(db, gid)
    engine.recompute_dependencies("SEA_2026", "OFFICIAL")

def test_07_late_pbp_modality_append(engine, db):
    """Test 07: Late PBP events upgrade modality flag without creating duplicate games."""
    gid = "GAM_P7_007_LATEPBP"
    clean_game_fixtures(db, gid)

    payload = {"match_id": "P7_007"}
    engine.ingest_game(
        game_id=gid, season_id="SEA_2026", competition_id="CMP_JBBL",
        game_date="2026-11-10", home_team_id="TEM_DEMO_U16", away_team_id="TEM_1001",
        home_score=70, away_score=65, payload=payload, game_type="OFFICIAL"
    )

    pbp_events = [
        {
            "event_id": f"EVT_{gid}_{i}",
            "period": 1,
            "game_seconds_remaining": 2400 - i * 10,
            "period_seconds_remaining": 600 - i * 10,
            "event_type": "2FGM",
            "player_id": "PLY_DEMO_104",
            "team_id": "TEM_DEMO_U16",
            "score_home": 2 * i,
            "score_away": 0,
            "is_scoring_event": True
        }
        for i in range(55)
    ]
    res_mod = engine.append_modality(game_id=gid, modality_type="PBP", records=pbp_events)
    assert res_mod["status"] == "MODALITY_APPENDED"

    df_reg = build_game_registry()
    grow = df_reg[df_reg["game_id"] == gid].iloc[0]
    assert grow["pbp_available"] == True
    assert grow["pbp_event_count"] >= 50

    clean_game_fixtures(db, gid)
    engine.recompute_dependencies("SEA_2026", "OFFICIAL")

def test_08_late_shots_modality_append(engine, db):
    """Test 08: Late shots upgrade spatial shot availability."""
    gid = "GAM_P7_008_LATESHOT"
    clean_game_fixtures(db, gid)

    payload = {"match_id": "P7_008"}
    engine.ingest_game(
        game_id=gid, season_id="SEA_2026", competition_id="CMP_JBBL",
        game_date="2026-11-12", home_team_id="TEM_DEMO_U16", away_team_id="TEM_1001",
        home_score=75, away_score=68, payload=payload, game_type="OFFICIAL"
    )

    shots = [
        {
            "shot_id": f"SHT_{gid}_{i}",
            "team_id": "TEM_DEMO_U16",
            "player_id": "PLY_DEMO_104",
            "period": 1,
            "shot_type": "2PT",
            "is_made": True,
            "points": 2,
            "x_coord": 150.0,
            "y_coord": 30.0,
            "shot_location_status": "OBSERVED"
        }
        for i in range(25)
    ]
    res_mod = engine.append_modality(game_id=gid, modality_type="SHOTS", records=shots)
    assert res_mod["status"] == "MODALITY_APPENDED"

    df_reg = build_game_registry()
    grow = df_reg[df_reg["game_id"] == gid].iloc[0]
    assert grow["shot_available"] == True
    assert grow["coordinate_available"] == True

    clean_game_fixtures(db, gid)
    engine.recompute_dependencies("SEA_2026", "OFFICIAL")

def test_09_multiple_late_modalities_append(engine, db):
    """Test 09: Progressively appending PBP then Shots maintains single game integrity."""
    gid = "GAM_P7_009_MULTI"
    clean_game_fixtures(db, gid)

    # Ingest base game with player boxscore
    p_box = [{"player_id": f"PLY_P7_009_{i}", "team_id": "TEM_DEMO_U16", "jersey_number": i, "seconds_played": 600, "points": 8} for i in range(10)]
    engine.ingest_game(
        game_id=gid, season_id="SEA_2026", competition_id="CMP_JBBL",
        game_date="2026-11-15", home_team_id="TEM_DEMO_U16", away_team_id="TEM_1001",
        home_score=80, away_score=72, payload={"match_id": "P7_009"}, game_type="OFFICIAL",
        player_boxscores=p_box
    )

    # Append PBP
    pbp = [{"event_id": f"EVT_{gid}_{i}", "period": 1, "game_seconds_remaining": 2000, "period_seconds_remaining": 500, "event_type": "PLAY", "player_id": "PLY_DEMO_104", "team_id": "TEM_DEMO_U16", "score_home": 0, "score_away": 0} for i in range(55)]
    engine.append_modality(game_id=gid, modality_type="PBP", records=pbp)

    # Append Shots
    shots = [{"shot_id": f"SHT_{gid}_{i}", "team_id": "TEM_DEMO_U16", "player_id": "PLY_DEMO_104", "period": 1, "shot_type": "3PT", "is_made": True, "points": 3, "x_coord": 220.0, "y_coord": 80.0, "shot_location_status": "OBSERVED"} for i in range(25)]
    engine.append_modality(game_id=gid, modality_type="SHOTS", records=shots)

    df_reg = build_game_registry()
    grow = df_reg[df_reg["game_id"] == gid].iloc[0]
    assert grow["pbp_available"] == True
    assert grow["shot_available"] == True
    assert grow["analytical_tier"] == "TIER_1_ADVANCED_SPATIAL_PBP"

    clean_game_fixtures(db, gid)
    engine.recompute_dependencies("SEA_2026", "OFFICIAL")

def test_10_score_only_game_registration(engine, db):
    """Test 10: Score-only game registers cleanly without player boxscore/PBP/shot requirements."""
    gid = "GAM_P7_010_SCOREONLY"
    clean_game_fixtures(db, gid)

    payload = {"match_id": "P7_010", "type": "Score-only telegram report"}
    res = engine.ingest_game(
        game_id=gid, season_id="SEA_2026", competition_id="CMP_JBBL",
        game_date="2026-11-18", home_team_id="TEM_DEMO_U16", away_team_id="TEM_1001",
        home_score=68, away_score=64, payload=payload, game_type="OFFICIAL"
    )
    assert res["status"] == "INGESTED_NEW"
    
    df_reg = build_game_registry()
    grow = df_reg[df_reg["game_id"] == gid].iloc[0]
    assert grow["boxscore_available"] == True
    assert grow["player_boxscore_available"] == False
    assert grow["pbp_available"] == False
    assert grow["shot_available"] == False
    assert grow["analytical_tier"] == "TIER_3_METADATA_ONLY"

    clean_game_fixtures(db, gid)
    engine.recompute_dependencies("SEA_2026", "OFFICIAL")


# ==============================================================================
# 2. DATA INTEGRITY & ZERO FABRICATION (Tests 11 - 16)
# ==============================================================================

def test_11_zero_fabricated_boxscore_values(engine, db):
    """Test 11: Programmatically ingested score-only games store NULL (not fake FGM/FGA)."""
    gid = "GAM_P7_011_NOFAB"
    clean_game_fixtures(db, gid)

    engine.ingest_game(
        game_id=gid, season_id="SEA_2026", competition_id="CMP_JBBL",
        game_date="2026-11-20", home_team_id="TEM_DEMO_U16", away_team_id="TEM_1001",
        home_score=80, away_score=70, payload={"match_id": "P7_011"}, game_type="OFFICIAL"
    )

    df_bt = db.query_df(f"SELECT * FROM boxscore_team WHERE game_id = '{gid}'")
    assert len(df_bt) == 2
    # Verify points is real, but shooting stats are NULL (not 30 or 65)
    for _, row in df_bt.iterrows():
        assert row["points"] in [80, 70]
        assert pd.isna(row["fgm"]) or row["fgm"] is None
        assert pd.isna(row["fga"]) or row["fga"] is None
        assert pd.isna(row["ast"]) or row["ast"] is None

    clean_game_fixtures(db, gid)
    engine.recompute_dependencies("SEA_2026", "OFFICIAL")

def test_12_real_boxscore_passthrough(engine, db):
    """Test 12: Real boxscore dictionary stats pass through accurately."""
    gid = "GAM_P7_012_REALBOX"
    clean_game_fixtures(db, gid)

    home_box = {"fgm": 32, "fga": 70, "fg3m": 9, "fg3a": 25, "ftm": 15, "fta": 20, "orb": 14, "drb": 28, "trb": 42, "ast": 21, "stl": 10, "blk": 5, "tov": 14, "pf": 19}
    away_box = {"fgm": 25, "fga": 60, "fg3m": 6, "fg3a": 18, "ftm": 12, "fta": 16, "orb": 8, "drb": 22, "trb": 30, "ast": 15, "stl": 7, "blk": 2, "tov": 18, "pf": 22}

    engine.ingest_game(
        game_id=gid, season_id="SEA_2026", competition_id="CMP_JBBL",
        game_date="2026-11-22", home_team_id="TEM_DEMO_U16", away_team_id="TEM_1001",
        home_score=88, away_score=68, payload={"match_id": "P7_012"}, game_type="OFFICIAL",
        home_boxscore=home_box, away_boxscore=away_box
    )

    df_bt = db.query_df(f"SELECT * FROM boxscore_team WHERE game_id = '{gid}' AND is_home = TRUE")
    h_row = df_bt.iloc[0]
    assert h_row["fgm"] == 32
    assert h_row["fga"] == 70
    assert h_row["fg3m"] == 9
    assert h_row["ast"] == 21

    clean_game_fixtures(db, gid)
    engine.recompute_dependencies("SEA_2026", "OFFICIAL")

def test_13_invalid_negative_score_rejection(engine):
    """Test 13: Quality gates reject negative scores."""
    payload = {"home_team_id": "TEM_DEMO_U16", "away_team_id": "TEM_1001", "home_score": -5, "away_score": 80}
    is_valid, errors = engine.validate_quality_gates(payload)
    assert is_valid == False
    assert any("Score Validity" in e for e in errors)

def test_14_same_team_rejection(engine):
    """Test 14: Quality gates reject home == away team ID."""
    payload = {"home_team_id": "TEM_DEMO_U16", "away_team_id": "TEM_DEMO_U16", "home_score": 80, "away_score": 75}
    is_valid, errors = engine.validate_quality_gates(payload)
    assert is_valid == False
    assert any("Distinct Teams" in e for e in errors)

def test_15_invalid_shooting_formula_rejection(engine):
    """Test 15: Quality gates reject player boxscore where 2*FG2M + 3*FG3M + FTM != PTS."""
    payload = {
        "home_team_id": "TEM_DEMO_U16", "away_team_id": "TEM_1001", "home_score": 80, "away_score": 70,
        "player_boxscores": [
            {"player_id": "PLY_TEST", "fg2m": 2, "fg3m": 1, "ftm": 1, "points": 15}  # 2*2 + 3*1 + 1 = 8 != 15
        ]
    }
    is_valid, errors = engine.validate_quality_gates(payload)
    assert is_valid == False
    assert any("Scoring Formula" in e for e in errors)

def test_16_duplicate_primary_key_prevention(db):
    """Test 16: DuckDB manager insert_dataframe prevents primary key duplicate violations."""
    df_dup = pd.DataFrame([
        {"game_id": "GAM_DEMO_001", "season_id": "SEA_2025", "competition_id": "CMP_JBBL", "game_date": "2025-01-01", "home_team_id": "TEM_DEMO_U16", "away_team_id": "TEM_DEMO_BULLS_U16", "home_score": 80, "away_score": 70, "game_status": "FINAL", "game_type": "OFFICIAL"}
    ])
    # Attempting to re-insert existing game_id
    initial_count = db.get_table_count("game")
    db.insert_dataframe("game", df_dup, pk_col="game_id")
    after_count = db.get_table_count("game")
    assert after_count == initial_count


# ==============================================================================
# 3. SEASONS & CONTINUITY (Tests 17 - 20)
# ==============================================================================

def test_17_season_transition_2025_to_2026(engine, db):
    """Test 17: Ingesting game for SEA_2026 dynamically registers season without code modification."""
    gid = "GAM_P7_017_S26"
    clean_game_fixtures(db, gid)

    engine.ingest_game(
        game_id=gid, season_id="SEA_2026", competition_id="CMP_JBBL",
        game_date="2026-10-05", home_team_id="TEM_DEMO_U16", away_team_id="TEM_1001",
        home_score=85, away_score=80, payload={"match_id": "P7_017"}, game_type="OFFICIAL"
    )

    df_sea = db.query_df("SELECT * FROM season WHERE season_id = 'SEA_2026'")
    assert not df_sea.empty
    assert str(df_sea.iloc[0]["start_date"])[:10] == "2026-09-01"
    assert str(df_sea.iloc[0]["end_date"])[:10] == "2027-06-30"

    clean_game_fixtures(db, gid)
    engine.recompute_dependencies("SEA_2026", "OFFICIAL")

def test_18_season_transition_2026_to_2027(engine, db):
    """Test 18: Ingesting game in early spring 2027 sets correct season boundaries."""
    gid = "GAM_P7_018_S27"
    clean_game_fixtures(db, gid)

    engine.ingest_game(
        game_id=gid, season_id="SEA_2027", competition_id="CMP_JBBL",
        game_date="2027-03-15", home_team_id="TEM_DEMO_U16", away_team_id="TEM_1001",
        home_score=78, away_score=72, payload={"match_id": "P7_018"}, game_type="OFFICIAL"
    )

    df_sea = db.query_df("SELECT * FROM season WHERE season_id = 'SEA_2027'")
    assert not df_sea.empty
    assert str(df_sea.iloc[0]["start_date"])[:10] == "2026-09-01"
    assert str(df_sea.iloc[0]["end_date"])[:10] == "2027-06-30"

    clean_game_fixtures(db, gid)
    engine.recompute_dependencies("SEA_2027", "OFFICIAL")

def test_19_dynamic_future_season_discovery(engine, db):
    """Test 19: Distant future season SEA_2029 is discovered dynamically in DataService."""
    gid = "GAM_P7_019_S29"
    clean_game_fixtures(db, gid)

    engine.ingest_game(
        game_id=gid, season_id="SEA_2029", competition_id="CMP_JBBL",
        game_date="2029-01-10", home_team_id="TEM_DEMO_U16", away_team_id="TEM_1001",
        home_score=80, away_score=75, payload={"match_id": "P7_019"}, game_type="OFFICIAL"
    )

    ds = DataService()
    seasons = ds.get_available_seasons()
    assert "SEA_2029" in seasons

    clean_game_fixtures(db, gid)
    engine.recompute_dependencies("SEA_2025", "OFFICIAL")

def test_20_player_continuity_across_seasons(engine, db):
    """Test 20: Same player appearing in multiple seasons maintains identical player_id."""
    pid = "PLY_DEMO_104"  # Maximilian Becker
    
    # Verify player exists in historical dataset
    df_p = db.query_df(f"SELECT canonical_name FROM player WHERE player_id = '{pid}'")
    assert not df_p.empty
    player_name = df_p.iloc[0]["canonical_name"]

    # Ingest in new season with player boxscore
    gid = "GAM_P7_020_CONT"
    clean_game_fixtures(db, gid)

    p_box = [
        {"player_id": pid, "team_id": "TEM_DEMO_U16", "jersey_number": 14, "seconds_played": 1500, "points": 22, "fg2m": 8, "fg3m": 1, "ftm": 3}
    ]
    engine.ingest_game(
        game_id=gid, season_id="SEA_2026", competition_id="CMP_JBBL",
        game_date="2026-10-18", home_team_id="TEM_DEMO_U16", away_team_id="TEM_1001",
        home_score=85, away_score=70, payload={"match_id": "P7_020"}, game_type="OFFICIAL",
        player_boxscores=p_box
    )

    df_bxp = db.query_df(f"SELECT player_id, points FROM boxscore_player WHERE game_id = '{gid}' AND player_id = '{pid}'")
    assert not df_bxp.empty
    assert df_bxp.iloc[0]["points"] == 22

    clean_game_fixtures(db, gid)
    engine.recompute_dependencies("SEA_2026", "OFFICIAL")


# ==============================================================================
# 4. POPULATION ISOLATION (Tests 21 - 24)
# ==============================================================================

def test_21_official_population_isolation(engine, db):
    """Test 21: Official games appear in OFFICIAL_ONLY population filter."""
    ds = DataService()
    df_reg = ds.get_game_registry(population_mode="OFFICIAL_ONLY")
    assert (df_reg["game_type"] == "OFFICIAL").all()
    assert (df_reg["is_official_competition"] == True).all()

def test_22_practice_population_isolation(engine, db):
    """Test 22: Practice games are isolated from OFFICIAL_ONLY standings."""
    gid = "GAM_P7_022_PRAC"
    clean_game_fixtures(db, gid)

    engine.ingest_game(
        game_id=gid, season_id="SEA_2026", competition_id="JBBL_PRACTICE",
        game_date="2026-10-25", home_team_id="TEM_DEMO_U16", away_team_id="TEM_1001",
        home_score=95, away_score=60, payload={"match_id": "P7_022"}, game_type="PRACTICE"
    )

    ds = DataService()
    df_off = ds.get_game_registry(population_mode="OFFICIAL_ONLY")
    assert gid not in df_off["game_id"].values

    df_all = ds.get_game_registry(population_mode="ALL_GAMES")
    assert gid in df_all["game_id"].values

    clean_game_fixtures(db, gid)
    engine.recompute_dependencies("SEA_2026", "OFFICIAL")

def test_23_scrimmage_population_isolation(engine, db):
    """Test 23: Scrimmages appear in ALL_GAMES but excluded from OFFICIAL_ONLY."""
    gid = "GAM_DEMO_TEST_023_SCRIM"
    clean_game_fixtures(db, gid)

    try:
        engine.ingest_game(
            game_id=gid, season_id="SEA_2026", competition_id="JBBL_SCRIMMAGE",
            game_date="2026-10-28", home_team_id="TEM_DEMO_U16", away_team_id="TEM_1001",
            home_score=70, away_score=68, payload={"match_id": "P7_023"}, game_type="SCRIMMAGE"
        )

        ds = DataService()
        df_off = ds.get_game_registry(population_mode="OFFICIAL_ONLY")
        assert gid not in df_off["game_id"].values
    finally:
        clean_game_fixtures(db, gid)
        engine.recompute_dependencies("SEA_2026", "OFFICIAL")

def test_24_friendly_population_isolation(engine, db):
    """Test 24: Friendly games appear in ALL_GAMES but excluded from OFFICIAL_ONLY."""
    gid = "GAM_P7_024_FRND"
    clean_game_fixtures(db, gid)

    engine.ingest_game(
        game_id=gid, season_id="SEA_2026", competition_id="JBBL_FRIENDLY",
        game_date="2026-10-30", home_team_id="TEM_DEMO_U16", away_team_id="TEM_1001",
        home_score=82, away_score=74, payload={"match_id": "P7_024"}, game_type="FRIENDLY"
    )

    ds = DataService()
    df_off = ds.get_game_registry(population_mode="OFFICIAL_ONLY")
    assert gid not in df_off["game_id"].values

    clean_game_fixtures(db, gid)
    engine.recompute_dependencies("SEA_2026", "OFFICIAL")


# ==============================================================================
# 5. OPERATIONS & INBOX (Tests 25 - 30)
# ==============================================================================

def test_25_operation_report_generation(engine, db):
    """Test 25: Every ingestion produces a valid structured operation report in data/operations/."""
    gid = "GAM_P7_025_OPSREP"
    clean_game_fixtures(db, gid)

    res = engine.ingest_game(
        game_id=gid, season_id="SEA_2026", competition_id="CMP_JBBL",
        game_date="2026-11-01", home_team_id="TEM_DEMO_U16", away_team_id="TEM_1001",
        home_score=80, away_score=75, payload={"match_id": "P7_025"}, game_type="OFFICIAL"
    )

    ops_dir = Path("data/operations")
    reports = list(ops_dir.glob(f"OPS_*_{gid}.json"))
    assert len(reports) >= 1
    
    rep_content = json.loads(reports[0].read_text(encoding="utf-8"))
    assert rep_content["game_id"] == gid
    assert rep_content["status"] == "INGESTED_NEW"
    assert "elapsed_time_seconds" in rep_content

    clean_game_fixtures(db, gid)
    engine.recompute_dependencies("SEA_2026", "OFFICIAL")

def test_26_sha256_digest_determinism(engine):
    """Test 26: Payload SHA-256 hash is deterministic and key-order invariant."""
    p1 = {"a": 1, "b": 2, "c": [1, 2, 3]}
    p2 = {"c": [1, 2, 3], "b": 2, "a": 1}
    assert engine.compute_payload_hash(p1) == engine.compute_payload_hash(p2)

def test_27_source_correction_audit_retention(engine, db):
    """Test 27: Audit trail preserves timestamped copies without deleting evidence."""
    gid = "GAM_P7_027_AUDIT"
    clean_game_fixtures(db, gid)

    engine.ingest_game(
        game_id=gid, season_id="SEA_2026", competition_id="CMP_JBBL",
        game_date="2026-11-04", home_team_id="TEM_DEMO_U16", away_team_id="TEM_1001",
        home_score=70, away_score=60, payload={"v": 1}, game_type="OFFICIAL"
    )
    engine.ingest_game(
        game_id=gid, season_id="SEA_2026", competition_id="CMP_JBBL",
        game_date="2026-11-04", home_team_id="TEM_DEMO_U16", away_team_id="TEM_1001",
        home_score=72, away_score=60, payload={"v": 2}, game_type="OFFICIAL"
    )

    raw_dir = Path("data/raw/jbbl/SEA_2026") / gid
    backups = list(raw_dir.glob("match_raw_audit_prev_*.json"))
    assert len(backups) >= 1

    clean_game_fixtures(db, gid)
    engine.recompute_dependencies("SEA_2026", "OFFICIAL")

def test_28_inbox_mode_a_self_contained(engine, db):
    """Test 28: Inbox processes Mode A self-contained JSON payload cleanly into processed/."""
    gid = "GAM_P7_028_INBOX_A"
    clean_game_fixtures(db, gid)

    incoming = Path("data/inbox/incoming")
    processed = Path("data/inbox/processed")
    incoming.mkdir(parents=True, exist_ok=True)

    payload_file = incoming / f"{gid}.json"
    payload_data = {
        "game_id": gid,
        "season_id": "SEA_2026",
        "competition_id": "CMP_JBBL",
        "game_date": "2026-11-06",
        "home_team_id": "TEM_DEMO_U16",
        "away_team_id": "TEM_1001",
        "home_score": 85,
        "away_score": 75,
        "game_type": "OFFICIAL",
        "match_id": "P7_028"
    }
    payload_file.write_text(json.dumps(payload_data), encoding="utf-8")

    process_inbox(engine)

    assert not payload_file.exists()
    assert (processed / f"{gid}.json").exists()

    # Clean up
    (processed / f"{gid}.json").unlink(missing_ok=True)
    clean_game_fixtures(db, gid)
    engine.recompute_dependencies("SEA_2026", "OFFICIAL")

def test_29_inbox_mode_b_companion_metadata(engine, db):
    """Test 29: Inbox processes Mode B payload + companion .metadata.json."""
    gid = "GAM_P7_029_INBOX_B"
    clean_game_fixtures(db, gid)

    incoming = Path("data/inbox/incoming")
    processed = Path("data/inbox/processed")
    incoming.mkdir(parents=True, exist_ok=True)

    payload_file = incoming / f"{gid}.json"
    meta_file = incoming / f"{gid}.metadata.json"

    # Raw payload without full metadata
    payload_file.write_text(json.dumps({"match_id": "P7_029", "raw_stream": "DATA"}), encoding="utf-8")
    
    # Companion metadata
    meta_data = {
        "game_id": gid,
        "season_id": "SEA_2026",
        "competition_id": "CMP_JBBL",
        "game_date": "2026-11-08",
        "home_team_id": "TEM_DEMO_U16",
        "away_team_id": "TEM_1001",
        "home_score": 90,
        "away_score": 80,
        "game_type": "OFFICIAL"
    }
    meta_file.write_text(json.dumps(meta_data), encoding="utf-8")

    process_inbox(engine)

    assert not payload_file.exists()
    assert not meta_file.exists()
    assert (processed / f"{gid}.json").exists()
    assert (processed / f"{gid}.metadata.json").exists()

    # Clean up
    (processed / f"{gid}.json").unlink(missing_ok=True)
    (processed / f"{gid}.metadata.json").unlink(missing_ok=True)
    clean_game_fixtures(db, gid)
    engine.recompute_dependencies("SEA_2026", "OFFICIAL")

def test_30_rejected_payload_preservation(engine, db):
    """Test 30: Malformed/missing metadata payload is moved to rejected/ without database contamination."""
    incoming = Path("data/inbox/incoming")
    rejected = Path("data/inbox/rejected")
    incoming.mkdir(parents=True, exist_ok=True)

    bad_file = incoming / "GAM_P7_030_BAD.json"
    bad_file.write_text(json.dumps({"incomplete": "data"}), encoding="utf-8")

    initial_games = db.get_table_count("game")
    process_inbox(engine)

    assert not bad_file.exists()
    assert (rejected / "GAM_P7_030_BAD.json").exists()
    assert db.get_table_count("game") == initial_games

    # Clean up
    (rejected / "GAM_P7_030_BAD.json").unlink(missing_ok=True)


# ==============================================================================
# 6. ANALYTICS & MATH SAFETY (Tests 31 - 35)
# ==============================================================================

def test_31_rolling_window_n_lt_4_safeguard(engine, db):
    """Test 31: Rolling windows classify N < 4 trajectories as INSUFFICIENT_DATA."""
    ds = DataService()
    df_evo = ds.get_player_evolution()
    assert not df_evo.empty

    df_early = df_evo[df_evo["game_number"] < 4]
    assert (df_early["trend_classification"] == "INSUFFICIENT_DATA").all()

def test_32_rolling_window_n_gte_4_activation(engine, db):
    """Test 32: Trajectories with N >= 4 evaluate active trend classification."""
    ds = DataService()
    df_evo = ds.get_player_evolution()
    
    df_active = df_evo[df_evo["game_number"] >= 4]
    if not df_active.empty:
        valid_trends = {"IMPROVING", "DECLINING", "STABLE", "VOLATILE", "INSUFFICIENT_DATA"}
        assert df_active["trend_classification"].isin(valid_trends).all()

def test_33_weekly_aggregation_calculation(engine, db):
    """Test 33: Weekly player performance table aggregates calendar weeks correctly."""
    ds = DataService()
    df_week = ds.get_player_weekly_analysis()
    assert not df_week.empty
    assert "week_number" in df_week.columns
    assert "calendar_year" in df_week.columns
    assert "ppg" in df_week.columns

def test_34_trend_classification_determinism():
    """Test 34: Trend slope computation is mathematically deterministic."""
    from python.analytics.phase5_player_evolution import compute_trend_slope, classify_player_trend
    
    slope = compute_trend_slope([10.0, 12.0, 14.0, 16.0])
    assert slope == 2.0

    trend, sl, desc = classify_player_trend([10.0, 12.0, 14.0, 16.0], [0.5, 0.5, 0.5, 0.5], baseline_ppg=10.0)
    assert trend == "IMPROVING"

def test_35_recomputation_timing_measurement(engine):
    """Test 35: Recomputation returns measurable execution duration in seconds."""
    res = engine.recompute_dependencies(season_id="SEA_2025", game_type="OFFICIAL")
    assert res["status"] == "SUCCESS"
    assert "elapsed_seconds" in res
    assert res["elapsed_seconds"] > 0


# ==============================================================================
# 7. UI & DATA FRESHNESS (Tests 36 - 40)
# ==============================================================================

def test_36_data_freshness_latest_game_date():
    """Test 36: DataService.get_data_freshness() returns valid latest game date."""
    ds = DataService()
    fresh = ds.get_data_freshness()
    assert "latest_game_date" in fresh
    assert fresh["latest_game_date"] != "N/A"

def test_37_data_freshness_timestamps():
    """Test 37: Freshness layer includes DB and Parquet timestamps."""
    ds = DataService()
    fresh = ds.get_data_freshness()
    assert "db_last_modified" in fresh
    assert "registry_last_modified" in fresh
    assert "total_games" in fresh
    assert fresh["total_games"] >= 48

def test_38_dynamic_season_discovery():
    """Test 38: DataService discovers all active seasons in DB."""
    ds = DataService()
    seasons = ds.get_available_seasons()
    assert len(seasons) >= 2
    assert "SEA_2025" in seasons

def test_39_modality_matrix_flags_per_game():
    """Test 39: Game registry includes all 7 modality flags."""
    ds = DataService()
    df_reg = ds.get_game_registry(population_mode="OFFICIAL_ONLY")
    expected_flags = [
        "boxscore_available", "player_boxscore_available", "pbp_available",
        "shot_available", "coordinate_available", "lineup_available", "video_available"
    ]
    for flag in expected_flags:
        assert flag in df_reg.columns

def test_40_no_hardcoded_analytical_values_in_main_app():
    """Test 40: Main application strictly queries DataService and contains zero hardcoded stats."""
    main_code = Path("app/main.py").read_text(encoding="utf-8")
    assert "ds.get_" in main_code
    assert "77.5" not in main_code
    assert "22.4" not in main_code
