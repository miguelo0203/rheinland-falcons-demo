"""End-to-End Integration Tests across all 7 Source Availability Permutations in Sandbox."""

import pytest
from pathlib import Path

from python.database.duckdb_manager import DuckDBManager
from python.ingestion.orchestrator import PipelineOrchestrator
from python.models.enums import ValidationStatus, CompletenessTier, QualityTier


def test_all_seven_permutations_end_to_end(synthetic_manifest):
    """Verify that all 7 source-availability permutations ingest cleanly without crashes."""
    # Use temporary isolated database
    db = DuckDBManager(in_memory=True)
    orchestrator = PipelineOrchestrator(db_manager=db)

    # 1. Full: Boxscore + PBP + Video
    p1 = orchestrator.ingest_game(
        game_id="GAM_DEMO_001_ALL",
        boxscore_file=synthetic_manifest["GAME_DEMO_001_ALL"]["boxscore"],
        pbp_file=synthetic_manifest["GAME_DEMO_001_ALL"]["pbp"],
        video_file=synthetic_manifest["GAME_DEMO_001_ALL"]["video"],
    )
    assert p1["sources"]["boxscore_available"] is True
    assert p1["sources"]["pbp_available"] is True
    assert p1["sources"]["video_available"] is True
    assert p1["validation_status"] in [ValidationStatus.PASS, ValidationStatus.PASS_WITH_WARNINGS]
    assert p1["completeness_score"] == CompletenessTier.COMPLETE
    assert p1["overall_quality"] == QualityTier.HIGH

    # 2. Boxscore + PBP
    p2 = orchestrator.ingest_game(
        game_id="GAM_DEMO_002_BOX_PBP",
        boxscore_file=synthetic_manifest["GAME_DEMO_002_BOX_PBP"]["boxscore"],
        pbp_file=synthetic_manifest["GAME_DEMO_002_BOX_PBP"]["pbp"],
    )
    assert p2["sources"]["boxscore_available"] is True
    assert p2["sources"]["pbp_available"] is True
    assert p2["sources"]["video_available"] is False
    assert p2["completeness_score"] == CompletenessTier.HIGH

    # 3. Boxscore + Video
    p3 = orchestrator.ingest_game(
        game_id="GAM_DEMO_003_BOX_VID",
        boxscore_file=synthetic_manifest["GAME_DEMO_003_BOX_VID"]["boxscore"],
        video_file=synthetic_manifest["GAME_DEMO_003_BOX_VID"]["video"],
    )
    assert p3["sources"]["boxscore_available"] is True
    assert p3["sources"]["pbp_available"] is False
    assert p3["sources"]["video_available"] is True

    # 4. PBP + Video
    p4 = orchestrator.ingest_game(
        game_id="GAM_DEMO_004_PBP_VID",
        pbp_file=synthetic_manifest["GAME_DEMO_004_PBP_VID"]["pbp"],
        video_file=synthetic_manifest["GAME_DEMO_004_PBP_VID"]["video"],
    )
    assert p4["sources"]["boxscore_available"] is False
    assert p4["sources"]["pbp_available"] is True
    assert p4["sources"]["video_available"] is True

    # 5. Boxscore Only
    p5 = orchestrator.ingest_game(
        game_id="GAM_DEMO_005_BOX_ONLY",
        boxscore_file=synthetic_manifest["GAME_DEMO_005_BOX_ONLY"]["boxscore"],
    )
    assert p5["sources"]["boxscore_available"] is True
    assert p5["sources"]["pbp_available"] is False
    assert p5["sources"]["video_available"] is False
    assert p5["completeness_score"] == CompletenessTier.PARTIAL

    # 6. PBP Only
    p6 = orchestrator.ingest_game(
        game_id="GAM_DEMO_006_PBP_ONLY",
        pbp_file=synthetic_manifest["GAME_DEMO_006_PBP_ONLY"]["pbp"],
    )
    assert p6["sources"]["boxscore_available"] is False
    assert p6["sources"]["pbp_available"] is True
    assert p6["sources"]["video_available"] is False

    # 7. Video Only (Simulates initial U16 game milestone where only video is provided)
    p7 = orchestrator.ingest_game(
        game_id="GAM_DEMO_007_VID_ONLY",
        video_file=synthetic_manifest["GAME_DEMO_007_VID_ONLY"]["video"],
    )
    assert p7["sources"]["boxscore_available"] is False
    assert p7["sources"]["pbp_available"] is False
    assert p7["sources"]["video_available"] is True
    assert p7["counts"]["videos"] == 1
    assert p7["counts"]["boxscore_players"] == 0
    assert p7["counts"]["pbp_events"] == 0

    # Query DuckDB to verify canonical tables and provenance lineage
    games_df = db.query_df("SELECT game_id, game_status FROM game")
    assert len(games_df) == 7

    sources_df = db.query_df("SELECT * FROM game_sources")
    assert len(sources_df) == 7

    prov_df = db.query_df("SELECT * FROM source_provenance")
    assert len(prov_df) > 0

    val_df = db.query_df("SELECT * FROM validation_log")
    assert len(val_df) > 0

    db.close()
