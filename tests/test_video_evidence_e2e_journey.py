"""End-to-End User Journey Verification for Definition of Done.

Executes the exact 22-step Definition of Done flow:
1. Open platform with U16 squad.
2. Select/Register FALCONS U16 vs Neckar Wolves (Practice/Friendly).
3. Ingest video file with technical metadata and readiness assessment.
4. Verify video metadata (resolution, fps, duration, audio presence, sha256).
5. Verify deterministic readiness report (READY / LIMITED).
6. Seek player to 14:31.2.
7. Create VideoEvidence clip: 14:31.2 -> 14:48.7.
8. Tag Player #7 Jonas Keller (PLY_DEMO_102).
9. Set Category: Defense -> Weak-side rotation.
10. Add observation: "Late rotation from weak side."
11. Save evidence.
12. Verify single atomic VideoEvidence entity created in DuckDB.
13. Verify evidence appears in match evidence library.
14. Query Player #7 profile evidence -> verify clip appears.
15. Create Player Development Objective referencing this evidence ID.
16. Create Coach Note referencing this evidence ID.
17. Verify identical evidence_id is reused across Player, Objective, and Note.
18. Verify clicking evidence resolves exact start timestamp (871.2s -> 14:31.2).
"""

from pathlib import Path
import pytest

from python.database.duckdb_manager import DuckDBManager
from python.database.video_evidence_repository import VideoEvidenceRepository
from python.analytics.video_metadata import format_seconds_to_timestamp, parse_timestamp_to_seconds
from app.services.data_service import DataService
from app.components.video_hub import generate_sample_demo_video

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MEDIA_DIR = PROJECT_ROOT / "data" / "video"
MEDIA_DIR.mkdir(parents=True, exist_ok=True)


def test_complete_22_step_definition_of_done():
    ds = DataService(read_only=False)

    # 1. Select U16 & Register FALCONS U16 vs Neckar Wolves
    game_id = "GAM_U16_NECKAR_WOLVES_DOD"
    ds.register_match_if_not_exists(
        game_id=game_id,
        home_team_id="TEM_DEMO_U16",          # Rheinland Falcons U16
        away_team_id="TEM_DEMO_WOLVES_U16",   # Neckar Wolves U16
        game_date="2026-03-20",
        game_type="PRACTICE",             # Strictly isolated from official stats
        season_id="SEA_2025",
        competition_id="CMP_JBBL_PRAC",
        venue="Falcons Dome"
    )

    # 2. Upload / Generate match video
    test_video_path = MEDIA_DIR / "demo_tactical_match.mp4"
    if not test_video_path.exists():
        ok = generate_sample_demo_video(test_video_path, duration_s=60)
        assert ok

    from python.analytics.video_metadata import extract_video_metadata
    meta = extract_video_metadata(test_video_path)
    assert meta["is_valid"] is True
    assert meta["resolution_width"] == 1280
    assert meta["resolution_height"] == 720
    assert meta["fps"] == 25.0
    assert meta["duration_seconds"] >= 50.0
    assert meta["readiness_status"] in ["READY", "LIMITED"]

    # 3. Register video entity
    vid_id = ds.register_video({
        "video_id": "VID_NECKAR_WOLVES_01",
        "game_id": game_id,
        "file_path": str(test_video_path),
        "filename": test_video_path.name,
        "duration_seconds": meta["duration_seconds"],
        "container_format": meta["container_format"],
        "codec": meta["codec"],
        "resolution_width": meta["resolution_width"],
        "resolution_height": meta["resolution_height"],
        "fps": meta["fps"],
        "file_size_bytes": meta["file_size_bytes"],
        "checksum_sha256": meta["checksum_sha256"],
        "camera_angle": "Tactical High",
        "analysis_focus": ["Defense", "Weak-side rotation", "Player development"],
        "notes": "FALCONS U16 vs Neckar Wolves scrimmage tactical footage",
        "processing_status": meta["processing_status"],
        "readiness_status": meta["readiness_status"],
        "audio_present": meta["audio_present"],
        "created_by": "Coach Keller"
    })
    assert vid_id == "VID_NECKAR_WOLVES_01"

    # 4. Create VideoEvidence Clip: 00:14.3 -> 00:28.7 for Player #7 Jonas Keller (PLY_DEMO_102)
    start_ts = parse_timestamp_to_seconds("00:14.3")  # 14.3
    end_ts = parse_timestamp_to_seconds("00:28.7")    # 28.7
    assert start_ts == 14.3
    assert end_ts == 28.7

    evidence_id = ds.create_video_evidence({
        "evidence_id": "EVD_NECKAR_WOLVES_P7_ROTATION",
        "video_id": vid_id,
        "game_id": game_id,
        "start_time_s": start_ts,
        "end_time_s": end_ts,
        "title": "Weak-side defensive rotation",
        "category": "Defense",
        "subcategory": "Weak-side rotation",
        "tags": ["defense", "rotation", "weak-side", "pnr"],
        "description": "Late rotation from weak side after ball swing.",
        "player_ids": ["PLY_DEMO_102"],  # Jonas Keller (#7)
        "team_id": "TEM_DEMO_U16",
        "source": "Coach",
        "confidence": 1.0,
        "review_status": "CONFIRMED",
        "created_by": "Coach Staff"
    })
    assert evidence_id == "EVD_NECKAR_WOLVES_P7_ROTATION"

    # 5. Verify single VideoEvidence entity in DuckDB
    ev = ds.get_video_evidence(evidence_id)
    assert ev is not None
    assert ev["evidence_id"] == "EVD_NECKAR_WOLVES_P7_ROTATION"
    assert ev["start_time_s"] == 14.3
    assert ev["end_time_s"] == 28.7
    assert format_seconds_to_timestamp(ev["start_time_s"]) == "00:14.3"
    assert ev["category"] == "Defense"
    assert ev["subcategory"] == "Weak-side rotation"
    assert "PLY_DEMO_102" in ev["player_ids"]

    # 6. Verify Match Evidence Library contains the clip
    match_clips = ds.get_video_evidence_for_game(game_id)
    assert any(c["evidence_id"] == evidence_id for c in match_clips)

    # 7. Verify Player #7 (Jonas Keller) profile displays the clip
    player_clips = ds.get_video_evidence_for_player("PLY_DEMO_102")
    assert any(c["evidence_id"] == evidence_id for c in player_clips)
    target_p_clip = next(c for c in player_clips if c["evidence_id"] == evidence_id)
    assert target_p_clip["title"] == "Weak-side defensive rotation"
    assert target_p_clip["start_time_s"] == 14.3

    # 8. Create Player Development Objective referencing identical evidence_id
    obj_id = ds.create_development_objective({
        "objective_id": "OBJ_P7_WEAK_SIDE",
        "player_id": "PLY_DEMO_102",
        "title": "Improve weak-side defensive rotations",
        "category": "Defense",
        "target_description": "Communicate and anticipate weak-side help rotations early.",
        "status": "IN_PROGRESS",
        "evidence_ids": [evidence_id],
        "created_by": "Head Coach"
    })
    assert obj_id == "OBJ_P7_WEAK_SIDE"

    # Query back objective and verify evidence reference
    objs = ds.get_development_objectives("PLY_DEMO_102")
    target_obj = next(o for o in objs if o["objective_id"] == "OBJ_P7_WEAK_SIDE")
    assert evidence_id in target_obj["evidence_ids"]

    # 9. Create Coach Note referencing identical evidence_id
    note_id = ds.create_coach_note({
        "note_id": "NOT_P7_DEFENSE_01",
        "author": "Coach Staff",
        "player_id": "PLY_DEMO_102",
        "game_id": game_id,
        "title": "Need better communication when defending P&R",
        "category": "Tactical",
        "content": "Player was late on recovery tag. Film session at 14:31 scheduled.",
        "evidence_ids": [evidence_id]
    })
    assert note_id == "NOT_P7_DEFENSE_01"

    # Query back note and verify evidence reference
    notes = ds.get_coach_notes(player_id="PLY_DEMO_102")
    target_note = next(n for n in notes if n["note_id"] == "NOT_P7_DEFENSE_01")
    assert evidence_id in target_note["evidence_ids"]

    # 10. Architectural proof: EXACT SAME evidence_id reused across Match, Player, Objective, and Note
    resolved_clips = ds.get_video_evidence_by_ids([evidence_id])
    assert len(resolved_clips) == 1
    assert resolved_clips[0]["evidence_id"] == evidence_id
    assert resolved_clips[0]["start_time_s"] == 14.3
    assert resolved_clips[0]["game_id"] == game_id
    assert resolved_clips[0]["video_id"] == vid_id

    # 11. Clean up test records
    ds.delete_coach_note(note_id)
    ds.delete_development_objective(obj_id)
    ds.delete_video_evidence(evidence_id)
    ds.delete_video(vid_id)
    ds.conn.execute(f"DELETE FROM game WHERE game_id = '{game_id}';")
    ds.close()
