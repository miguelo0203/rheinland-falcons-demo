"""Automated Regression Test Suite for JBBL Pilot Match 9995585."""

from pathlib import Path
import pytest

from python.database.duckdb_manager import DuckDBManager
from python.ingestion.jbbl_adapter import JBBLAdapter
from python.ingestion.entity_resolver import EntityResolver
from python.ingestion.provenance import ProvenanceTracker
from python.ingestion.conflict_detector import ConflictDetector
from python.validation.engine import ValidationEngine
from python.models.enums import ObservationStatus, ValidationStatus

RAW_DIR = Path("data/raw/jbbl/9995585")

@pytest.fixture(scope="module")
def pilot_data():
    """Extract and normalize match 9995585."""
    if not (RAW_DIR / "raw_game_header.json").exists():
        pytest.skip(f"Raw directory {RAW_DIR} missing. Run acquire_raw_pilot.py first.")
    
    resolver = EntityResolver()
    prov_tracker = ProvenanceTracker()
    adapter = JBBLAdapter(entity_resolver=resolver, provenance_tracker=prov_tracker)
    
    raw_data = adapter.extract(RAW_DIR)
    payload = adapter.normalize(
        raw_data=raw_data,
        file_path=RAW_DIR / "raw_socket_stream_9995585.txt",
        game_id="GAM_DEMO_001",
        season_id="SEA_2024_2025",
        competition_id="CMP_JBBL",
    )
    return payload

def test_raw_artifacts_integrity():
    """Verify all 5 raw artifacts exist and are non-empty."""
    if not (RAW_DIR / "raw_game_header.json").exists():
        pytest.skip(f"Raw directory {RAW_DIR} missing in synthetic demo distribution.")
    assert (RAW_DIR / "raw_game_header.json").exists()
    assert (RAW_DIR / "raw_team_2048_rheinland.json").exists()
    assert (RAW_DIR / "raw_team_2054_wuerzburg.json").exists()
    assert (RAW_DIR / "raw_socket_stream_9995585.txt").exists()
    assert (RAW_DIR / "raw_provenance_manifest.json").exists()

def test_game_metadata_normalization(pilot_data):
    """Verify game entity properties and scores."""
    assert len(pilot_data.games) == 1
    game = pilot_data.games[0]
    assert game.game_id == "GAM_DEMO_001"
    assert game.home_score == 86
    assert game.away_score == 73
    assert game.home_team_id == "TEM_DEMO_U16"
    assert game.away_team_id == "TEM_DEMO_BULLS_U16"
    assert game.game_status == "FINAL"

def test_boxscore_mathematical_invariants(pilot_data):
    """Verify Boxscore team and player sums."""
    assert len(pilot_data.boxscore_teams) == 2
    bxt_home = next(t for t in pilot_data.boxscore_teams if t.team_id == "TEM_DEMO_U16")
    bxt_away = next(t for t in pilot_data.boxscore_teams if t.team_id == "TEM_DEMO_BULLS_U16")
    
    assert bxt_home.points == 86
    assert bxt_away.points == 73
    
    # Mathematical identities: points = ftm + 2*fg2m + 3*fg3m
    assert bxt_home.points == bxt_home.ftm + (2 * bxt_home.fg2m) + (3 * bxt_home.fg3m)
    assert bxt_away.points == bxt_away.ftm + (2 * bxt_away.fg2m) + (3 * bxt_away.fg3m)
    
    # Player sum reconciliation
    p_pts_home = sum(p.points for p in pilot_data.boxscore_players if p.team_id == "TEM_DEMO_U16")
    p_pts_away = sum(p.points for p in pilot_data.boxscore_players if p.team_id == "TEM_DEMO_BULLS_U16")
    assert p_pts_home == 86
    assert p_pts_away == 73

def test_pbp_stream_integrity(pilot_data):
    """Verify PBP action count, monotonicity, and final score."""
    assert len(pilot_data.pbp_events) == 470
    
    # Verify clock counts down within each period
    for q in range(1, 5):
        q_events = [e for e in pilot_data.pbp_events if e.period == q]
        clocks = [e.period_seconds_remaining for e in q_events]
        for i in range(len(clocks) - 1):
            assert clocks[i] >= clocks[i+1], f"Clock inversion detected in Quarter {q} at index {i}"
            
    # Final event score matches game score
    last_event = pilot_data.pbp_events[-1]
    assert last_event.home_score == 86
    assert last_event.away_score == 73

def test_shot_spatial_distribution(pilot_data):
    """Verify shot coordinate status, bounding box, and nullability."""
    assert len(pilot_data.shots) == 142
    
    shots_with_coords = [s for s in pilot_data.shots if s.shot_location_status == ObservationStatus.OBSERVED]
    shots_missing_coords = [s for s in pilot_data.shots if s.shot_location_status == ObservationStatus.NOT_AVAILABLE]
    
    assert len(shots_with_coords) > 100
    assert len(shots_missing_coords) > 0  # Missing coordinates handled as NOT_AVAILABLE without failing
    
    # Bounds check
    for s in shots_with_coords:
        assert 0 <= s.x_coord <= 300
        assert 0 <= s.y_coord <= 200

def test_validation_engine_execution(pilot_data):
    """Verify full validation suite runs cleanly."""
    conflict_detector = ConflictDetector()
    validator = ValidationEngine(conflict_detector=conflict_detector)
    
    val_out = validator.validate_game(
        game_id="GAM_DEMO_001",
        game=pilot_data.games[0],
        boxscore_teams=pilot_data.boxscore_teams,
        boxscore_players=pilot_data.boxscore_players,
        pbp_events=pilot_data.pbp_events,
        shots=pilot_data.shots,
    )
    
    assert val_out["game_sources"].validation_status == ValidationStatus.PASS
    assert all(r.passed for r in val_out["validation_results"])

def test_duckdb_persisted_state():
    """Verify DuckDB database queryability and row counts."""
    db = DuckDBManager()
    assert db.get_table_count("game") >= 1
    assert db.get_table_count("boxscore_team") >= 2
    assert db.get_table_count("boxscore_player") >= 24
    assert db.get_table_count("pbp_event") >= 470
    assert db.get_table_count("shot") >= 142
    assert db.get_table_count("lineup_stint") >= 8
