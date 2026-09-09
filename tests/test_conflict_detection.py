"""Unit tests for Multi-Source Conflict Detection and Precedence Resolution in Sandbox."""

import pytest
from python.ingestion.conflict_detector import ConflictDetector


def test_conflict_detection_and_precedence():
    detector = ConflictDetector()

    # Boxscore reports 18 points, PBP reports 20 points
    conflict = detector.check_and_log_conflict(
        game_id="GAM_001",
        entity_table="boxscore_player",
        entity_id="PLY_LUKAS",
        field_name="points",
        source_a_type="BOXSCORE",
        source_a_val=18,
        source_b_type="PBP",
        source_b_val=20,
        category="player_statistics",
    )

    assert conflict is not None
    assert conflict.field_name == "points"
    assert conflict.source_a_value == "18"
    assert conflict.source_b_value == "20"
    assert conflict.resolution_policy == "SOURCE_PRECEDENCE_BOXSCORE"
    assert conflict.resolved_value == "18"
    assert len(detector.detected_conflicts) == 1


def test_no_conflict_when_equal():
    detector = ConflictDetector()
    conflict = detector.check_and_log_conflict(
        game_id="GAM_001",
        entity_table="game",
        entity_id="GAM_001",
        field_name="home_score",
        source_a_type="BOXSCORE",
        source_a_val=78,
        source_b_type="PBP",
        source_b_val=78,
        category="game_score",
    )
    assert conflict is None
    assert len(detector.detected_conflicts) == 0
