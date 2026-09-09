"""Unit tests for Ingestion Adapters in Sandbox."""

import json
from pathlib import Path
import pytest

from python.ingestion.boxscore_adapter import BoxscoreAdapter
from python.ingestion.pbp_adapter import PBPAdapter, parse_clock_to_seconds
from python.ingestion.video_adapter import VideoAdapter
from python.models.enums import ObservationStatus, EventType, ShotType


def test_clock_parser():
    """Test clock string conversion to remaining seconds."""
    assert parse_clock_to_seconds("10:00") == 600.0
    assert parse_clock_to_seconds("09:30") == 570.0
    assert parse_clock_to_seconds("00:05.5") == 5.5
    assert parse_clock_to_seconds("00:00") == 0.0


def test_boxscore_adapter(synthetic_manifest, entity_resolver, provenance_tracker):
    """Test BoxscoreAdapter extraction and normalization."""
    adapter = BoxscoreAdapter(entity_resolver=entity_resolver, provenance_tracker=provenance_tracker)
    box_path = synthetic_manifest["GAME_001_ALL"]["boxscore"]

    assert adapter.detect(box_path) is True
    raw_data = adapter.extract(box_path)
    assert "home_team" in raw_data

    payload = adapter.normalize(raw_data, box_path, game_id="GAM_TEST_001")
    assert len(payload.games) == 1
    assert len(payload.boxscore_teams) == 2
    assert len(payload.boxscore_players) > 0
    assert payload.provenance.source_file_path == box_path.as_posix()

    # Check non-fabrication & observation status
    for p in payload.boxscore_players:
        assert p.observation_status == ObservationStatus.OBSERVED
        assert p.points >= 0


def test_pbp_adapter(synthetic_manifest, entity_resolver, provenance_tracker):
    """Test PBPAdapter event extraction, scoring, and shot identification."""
    adapter = PBPAdapter(entity_resolver=entity_resolver, provenance_tracker=provenance_tracker)
    pbp_path = synthetic_manifest["GAME_001_ALL"]["pbp"]

    assert adapter.detect(pbp_path) is True
    raw_data = adapter.extract(pbp_path)
    assert "events" in raw_data

    payload = adapter.normalize(raw_data, pbp_path, game_id="GAM_TEST_001")
    assert len(payload.pbp_events) > 0
    assert len(payload.shots) > 0

    first_shot = payload.shots[0]
    assert first_shot.shot_type in [ShotType.TWO_POINT, ShotType.THREE_POINT]
    assert first_shot.x_coord is not None
    assert first_shot.shot_location_status == ObservationStatus.OBSERVED


def test_video_adapter(synthetic_manifest, entity_resolver, provenance_tracker):
    """Test VideoAdapter metadata extraction and sync anchor ingestion."""
    adapter = VideoAdapter(entity_resolver=entity_resolver, provenance_tracker=provenance_tracker)
    vid_path = synthetic_manifest["GAME_001_ALL"]["video"]

    assert adapter.detect(vid_path) is True
    raw_data = adapter.extract(vid_path)
    assert "duration_seconds" in raw_data

    payload = adapter.normalize(raw_data, vid_path, game_id="GAM_TEST_001")
    assert len(payload.videos) == 1
    assert len(payload.video_event_syncs) == 1
    assert payload.videos[0].duration_seconds == 5400.0
    assert payload.video_event_syncs[0].confidence_level == "EXACT"
