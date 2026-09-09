"""Automated Test Suite for Video Evidence & Clip Reference Layer (v1).

Covers:
1. Valid video metadata extraction (dimensions, fps, duration, container, sha256).
2. Invalid/corrupted file handling without unhandled exceptions.
3. Rule-based video analysis readiness evaluation (READY, LIMITED, UNSUPPORTED).
4. Timestamp parsing and formatting utilities (MM:SS, HH:MM:SS, seconds).
5. Clip temporal boundary validation (start >= 0, end > start, end <= duration).
6. Video registration and relational integrity in DuckDB.
7. Official vs Practice fixture separation and mathematical isolation.
8. First-class VideoEvidence creation with temporal bounds.
9. Player evidence lookup and cross-referencing for Player #7 (PLY_DEMO_102).
10. Coach note creation with attached evidence IDs.
11. Player development objective creation and evidence attachment.
12. Future AI-source evidence compatibility (source="AI", confidence=0.82, review_status).
13. Evidence deletion and cascading integrity.
14. Streamlit AppTest verification for Hub 7 rendering without exceptions.
"""

from datetime import date
from pathlib import Path
import pytest
import duckdb
import pandas as pd

from python.database.duckdb_manager import DuckDBManager
from python.database.video_evidence_repository import VideoEvidenceRepository
from python.analytics.video_metadata import (
    format_seconds_to_timestamp,
    parse_timestamp_to_seconds,
    validate_clip_range,
    classify_video_readiness,
    extract_video_metadata
)
from app.services.data_service import DataService
from app.components.video_hub import generate_sample_demo_video

PROJECT_ROOT = Path(__file__).resolve().parents[1]
TEST_MEDIA_DIR = PROJECT_ROOT / "scratch" / "test_media"
TEST_MEDIA_DIR.mkdir(parents=True, exist_ok=True)


@pytest.fixture(scope="module")
def sample_video_path():
    """Generates a small 5-second sample video for testing."""
    v_path = TEST_MEDIA_DIR / "unit_test_sample.mp4"
    ok = generate_sample_demo_video(v_path, duration_s=5)
    assert ok, "Failed to create sample video fixture"
    yield v_path
    if v_path.exists():
        try:
            v_path.unlink()
        except Exception:
            pass


@pytest.fixture(scope="module")
def repo():
    """Provides a clean VideoEvidenceRepository instance."""
    manager = DuckDBManager(read_only=False)
    r = VideoEvidenceRepository(db_manager=manager)
    yield r
    manager.close()


@pytest.fixture(scope="module")
def ds():
    """Provides a DataService instance."""
    s = DataService(read_only=False)
    yield s
    s.close()


# ------------------------------------------------------------------------------
# 1. TIMESTAMP UTILITIES & BOUNDARY VALIDATION
# ------------------------------------------------------------------------------
def test_01_timestamp_formatting():
    assert format_seconds_to_timestamp(0.0) == "00:00.0"
    assert format_seconds_to_timestamp(45.5) == "00:45.5"
    assert format_seconds_to_timestamp(871.2) == "14:31.2"
    assert format_seconds_to_timestamp(3665.0) == "01:01:05.0"
    assert format_seconds_to_timestamp(-5.0) == "00:00.0"


def test_02_timestamp_parsing():
    assert parse_timestamp_to_seconds("00:45.5") == 45.5
    assert parse_timestamp_to_seconds("14:31.2") == 871.2
    assert parse_timestamp_to_seconds("14:31") == 871.0
    assert parse_timestamp_to_seconds("01:01:05") == 3665.0
    assert parse_timestamp_to_seconds("871.2") == 871.2
    assert parse_timestamp_to_seconds("") == 0.0
    assert parse_timestamp_to_seconds("invalid") == 0.0


def test_03_clip_boundary_validation():
    # Valid range
    ok, msg = validate_clip_range(871.2, 888.7, 1000.0)
    assert ok
    assert "Valid" in msg

    # Negative start
    ok, msg = validate_clip_range(-1.0, 10.0, 100.0)
    assert not ok
    assert "negative" in msg

    # Inverted range
    ok, msg = validate_clip_range(20.0, 15.0, 100.0)
    assert not ok
    assert "greater" in msg

    # Equal start and end
    ok, msg = validate_clip_range(15.0, 15.0, 100.0)
    assert not ok

    # Exceeding total duration
    ok, msg = validate_clip_range(50.0, 120.0, 100.0)
    assert not ok
    assert "exceeds" in msg


# ------------------------------------------------------------------------------
# 2. TECHNICAL METADATA EXTRACTION & READINESS EVALUATION
# ------------------------------------------------------------------------------
def test_04_valid_video_metadata_extraction(sample_video_path):
    meta = extract_video_metadata(sample_video_path)
    assert meta["is_valid"] is True
    assert meta["resolution_width"] == 1280
    assert meta["resolution_height"] == 720
    assert meta["fps"] == 25.0
    assert meta["duration_seconds"] >= 4.5
    assert meta["container_format"] == "MP4"
    assert len(meta["checksum_sha256"]) == 64
    assert meta["readiness_status"] in ["READY", "LIMITED"]


def test_05_invalid_or_missing_file_handling():
    # Non-existent file
    meta_missing = extract_video_metadata("non_existent_file.mp4")
    assert meta_missing["is_valid"] is False
    assert meta_missing["processing_status"] == "FAILED"
    assert meta_missing["readiness_status"] == "UNSUPPORTED"

    # Corrupt zero-byte file
    corrupt_path = TEST_MEDIA_DIR / "corrupt_sample.mp4"
    corrupt_path.write_bytes(b"")
    meta_corrupt = extract_video_metadata(corrupt_path)
    assert meta_corrupt["is_valid"] is False
    assert meta_corrupt["readiness_status"] == "UNSUPPORTED"
    corrupt_path.unlink()


def test_06_deterministic_readiness_classifier():
    # 1080p 25fps long match -> READY
    res_ready = classify_video_readiness(
        width=1920, height=1080, fps=25.0, duration_s=3600.0, container_format="MP4", stream_readable=True, audio_present=True
    )
    assert res_ready["status"] == "READY"
    assert res_ready["is_ready"] is True

    # 360p low res -> LIMITED
    res_lim = classify_video_readiness(
        width=640, height=360, fps=15.0, duration_s=1200.0, container_format="MP4", stream_readable=True, audio_present=True
    )
    assert res_lim["status"] == "LIMITED"
    assert res_lim["is_ready"] is True

    # Corrupt unreadable stream -> UNSUPPORTED
    res_unsup = classify_video_readiness(
        width=0, height=0, fps=0.0, duration_s=0.0, container_format="MP4", stream_readable=False
    )
    assert res_unsup["status"] == "UNSUPPORTED"
    assert res_unsup["is_ready"] is False


# ------------------------------------------------------------------------------
# 3. VIDEO REGISTRATION & MATCH RELATION
# ------------------------------------------------------------------------------
def test_07_video_registration_and_match_relation(repo, sample_video_path):
    test_gid = "GAM_TEST_NECKAR_WOLVES_01"
    repo.register_match_if_not_exists(
        game_id=test_gid,
        home_team_id="TEM_DEMO_U16",
        away_team_id="TEM_NECKAR_WOLVES_U16",
        game_date="2026-03-20",
        game_type="PRACTICE",
        season_id="SEA_2025"
    )

    vid_id = repo.register_video({
        "video_id": "VID_TEST_001",
        "game_id": test_gid,
        "file_path": str(sample_video_path),
        "filename": "sample_demo_clip.mp4",
        "duration_seconds": 5.0,
        "container_format": "MP4",
        "codec": "mp4v",
        "resolution_width": 1280,
        "resolution_height": 720,
        "fps": 25.0,
        "checksum_sha256": "abc1234567890",
        "analysis_focus": ["Defense", "Weak-side rotation"],
        "notes": "Test recording",
        "processing_status": "READY",
        "readiness_status": "READY"
    })
    assert vid_id == "VID_TEST_001"

    # Query back
    vid = repo.get_video("VID_TEST_001")
    assert vid is not None
    assert vid["game_id"] == test_gid
    assert vid["resolution_width"] == 1280
    assert "Defense" in vid["analysis_focus"]

    # Match games query
    v_list = repo.get_videos_for_game(test_gid)
    assert len(v_list) >= 1
    assert v_list[0]["video_id"] == "VID_TEST_001"


def test_08_match_type_separation_official_vs_practice(repo, ds):
    """Verifies that PRACTICE / FRIENDLY games remain strictly separated from official populations."""
    prac_gid = "GAM_TEST_NECKAR_WOLVES_01"
    
    # 1. DuckDB table isolation
    df_duck_off = repo.conn.execute("SELECT game_id FROM game WHERE game_type = 'OFFICIAL'").df()
    assert prac_gid not in df_duck_off["game_id"].values

    df_duck_all = repo.conn.execute("SELECT game_id FROM game WHERE game_id = 'GAM_TEST_NECKAR_WOLVES_01'").df()
    assert not df_duck_all.empty
    assert df_duck_all.iloc[0]["game_id"] == prac_gid

    # 2. Mathematical Population Filter Layer
    test_df = pd.DataFrame([
        {"game_id": "GAM_OFF_01", "game_type": "OFFICIAL"},
        {"game_id": prac_gid, "game_type": "PRACTICE"},
    ])
    from python.analytics.population_filter import filter_by_population, get_population_metadata
    df_off_filtered = filter_by_population(test_df, population_mode="OFFICIAL_ONLY")
    assert prac_gid not in df_off_filtered["game_id"].values
    assert len(df_off_filtered) == 1

    df_all_filtered = filter_by_population(test_df, population_mode="ALL_GAMES")
    assert prac_gid in df_all_filtered["game_id"].values
    assert len(df_all_filtered) == 2

    pop_meta = get_population_metadata(df_all_filtered)
    assert pop_meta["official_count"] == 1
    assert pop_meta["practice_count"] == 1


# ------------------------------------------------------------------------------
# 4. FIRST-CLASS VIDEO EVIDENCE CREATION & RETRIEVAL
# ------------------------------------------------------------------------------
def test_09_video_evidence_creation_and_player_association(repo):
    eid = repo.create_evidence({
        "evidence_id": "EVD_TEST_001",
        "video_id": "VID_TEST_001",
        "game_id": "GAM_TEST_NECKAR_WOLVES_01",
        "start_time_s": 871.2,
        "end_time_s": 888.7,
        "title": "Weak-side defensive rotation",
        "category": "Defense",
        "subcategory": "Weak-side rotation",
        "tags": ["defense", "rotation", "weak-side"],
        "description": "Late rotation from weak side.",
        "player_ids": ["PLY_DEMO_102"],  # Player #7 Jonas Keller
        "team_id": "TEM_DEMO_U16",
        "source": "Coach",
        "created_by": "Coach Staff"
    })
    assert eid == "EVD_TEST_001"

    # Query single evidence
    ev = repo.get_evidence("EVD_TEST_001")
    assert ev is not None
    assert ev["start_time_s"] == 871.2
    assert ev["end_time_s"] == 888.7
    assert ev["title"] == "Weak-side defensive rotation"
    assert "PLY_DEMO_102" in ev["player_ids"]

    # Query by player ID (Jonas Keller #7)
    player_evs = repo.get_evidence_for_player("PLY_DEMO_102")
    assert any(e["evidence_id"] == "EVD_TEST_001" for e in player_evs)

    # Query by game ID
    game_evs = repo.get_evidence_for_game("GAM_TEST_NECKAR_WOLVES_01")
    assert any(e["evidence_id"] == "EVD_TEST_001" for e in game_evs)


# ------------------------------------------------------------------------------
# 5. CROSS-MODULE REFERENCES: COACH NOTES & DEVELOPMENT OBJECTIVES
# ------------------------------------------------------------------------------
def test_10_coach_note_with_attached_evidence_ids(repo):
    nid = repo.create_coach_note({
        "note_id": "NOT_TEST_001",
        "author": "Head Coach",
        "player_id": "PLY_DEMO_102",
        "game_id": "GAM_TEST_NECKAR_WOLVES_01",
        "title": "Need better communication when defending P&R",
        "content": "Weak-side tag was late. Review film timestamps.",
        "category": "Tactical",
        "evidence_ids": ["EVD_TEST_001"]
    })
    assert nid == "NOT_TEST_001"

    notes = repo.get_coach_notes(player_id="PLY_DEMO_102")
    assert len(notes) >= 1
    found = next((n for n in notes if n["note_id"] == "NOT_TEST_001"), None)
    assert found is not None
    assert "EVD_TEST_001" in found["evidence_ids"]

    # Cleanup note
    assert repo.delete_coach_note("NOT_TEST_001") is True


def test_11_player_development_objective_with_attached_evidence(repo):
    oid = repo.create_development_objective({
        "objective_id": "OBJ_TEST_001",
        "player_id": "PLY_DEMO_102",
        "title": "Improve weak-side defensive rotations",
        "category": "Defense",
        "target_description": "Close out on catch without biting on pump fakes.",
        "status": "IN_PROGRESS",
        "evidence_ids": ["EVD_TEST_001"],
        "created_by": "Coach"
    })
    assert oid == "OBJ_TEST_001"

    objs = repo.get_development_objectives("PLY_DEMO_102")
    assert len(objs) >= 1
    found = next((o for o in objs if o["objective_id"] == "OBJ_TEST_001"), None)
    assert found is not None
    assert "EVD_TEST_001" in found["evidence_ids"]

    # Attach another evidence ID
    ok = repo.attach_evidence_to_objective("OBJ_TEST_001", "EVD_TEST_002")
    assert ok is True
    objs_updated = repo.get_development_objectives("PLY_DEMO_102")
    found_up = next((o for o in objs_updated if o["objective_id"] == "OBJ_TEST_001"), None)
    assert "EVD_TEST_002" in found_up["evidence_ids"]

    # Cleanup objective
    assert repo.delete_development_objective("OBJ_TEST_001") is True


# ------------------------------------------------------------------------------
# 6. FUTURE AI SOURCE ARCHITECTURE
# ------------------------------------------------------------------------------
def test_12_future_ai_architecture_compatibility(repo):
    """Verifies that future AI-generated evidence with confidence scores and review status integrates natively."""
    ai_eid = repo.create_evidence({
        "evidence_id": "EVD_AI_TEST_001",
        "video_id": "VID_TEST_001",
        "game_id": "GAM_TEST_NECKAR_WOLVES_01",
        "start_time_s": 140.0,
        "end_time_s": 155.0,
        "title": "AI Detected: Potential defensive rotation breakdown",
        "category": "Defense",
        "subcategory": "Weak-side rotation",
        "tags": ["ai_detected", "defensive_rotation"],
        "description": "CV tracking indicates 1.2s delay on weak-side recovery.",
        "player_ids": ["PLY_DEMO_102"],
        "source": "AI",
        "confidence": 0.82,
        "review_status": "PENDING_REVIEW",
        "created_by": "Automated CV Pipeline"
    })
    assert ai_eid == "EVD_AI_TEST_001"

    ev = repo.get_evidence("EVD_AI_TEST_001")
    assert ev["source"] == "AI"
    assert ev["confidence"] == 0.82
    assert ev["review_status"] == "PENDING_REVIEW"

    # Coach confirms and updates AI evidence
    ok = repo.update_evidence("EVD_AI_TEST_001", {
        "review_status": "CONFIRMED",
        "source": "AI + Coach Review",
        "description": "Confirmed by Coach: Late rotation confirmed on film."
    })
    assert ok is True

    ev_confirmed = repo.get_evidence("EVD_AI_TEST_001")
    assert ev_confirmed["review_status"] == "CONFIRMED"
    assert ev_confirmed["source"] == "AI + Coach Review"

    # Cleanup
    assert repo.delete_evidence("EVD_AI_TEST_001") is True


# ------------------------------------------------------------------------------
# 7. CLEANUP & DELETION INTEGRITY
# ------------------------------------------------------------------------------
def test_13_evidence_deletion(repo):
    assert repo.delete_evidence("EVD_TEST_001") is True
    assert repo.get_evidence("EVD_TEST_001") is None

    # Delete video
    assert repo.delete_video("VID_TEST_001") is True
    assert repo.get_video("VID_TEST_001") is None

    # Cleanup test game record
    repo.conn.execute("DELETE FROM game WHERE game_id = 'GAM_TEST_NECKAR_WOLVES_01';")


# ------------------------------------------------------------------------------
# 8. STREAMLIT APPTEST INTEGRATION (HUB 7 RENDERING)
# ------------------------------------------------------------------------------
def test_14_hub7_renders_cleanly_via_apptest(repo, ds):
    """Verifies that Hub 7 (Video Analysis & Match Film) renders without exceptions."""
    repo.db_manager.close()
    ds.close()
    from streamlit.testing.v1 import AppTest

    at = AppTest.from_file("app/main.py")
    at.run(timeout=30)

    # Authenticate
    if len(at.text_input) > 0 and len(at.button) > 0:
        at.text_input[0].input("demotool")
        at.button[0].click().run(timeout=30)

    assert len(at.exception) == 0

    # Select Hub 7
    nav_radio = None
    for r in at.sidebar.radio:
        if "Navigation" in r.label:
            nav_radio = r
            break

    assert nav_radio is not None
    nav_radio.set_value("7. 📹 Video Analysis & Match Film").run(timeout=30)

    assert len(at.exception) == 0, f"Exceptions in Hub 7: {[e.value for e in at.exception]}"
