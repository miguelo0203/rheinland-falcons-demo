"""Deterministic Synthetic Data Generator for all 7 Source Availability Permutations."""

import json
from pathlib import Path
from typing import Dict, Any, List

from python.config import Settings


def create_sample_boxscore(game_id: str, home_team: str, away_team: str) -> Dict[str, Any]:
    """Generate deterministic Boxscore JSON."""
    return {
        "game_id": game_id,
        "season_id": "SEA_2024_2025",
        "competition_id": "CMP_U16_REGIONAL",
        "game_date": "2025-01-18",
        "game_time": "14:00:00",
        "venue": "Falcons Arena, Rheinland",
        "periods_played": 4,
        "home_team": {
            "id": "TEM_DEMO_U16",
            "name": home_team,
            "points": 78,
            "stats": {
                "points": 78,
                "fgm": 30,
                "fga": 65,
                "fg2m": 22,
                "fg2a": 45,
                "fg3m": 8,
                "fg3a": 20,
                "ftm": 10,
                "fta": 14,
                "orb": 12,
                "drb": 24,
                "trb": 36,
                "ast": 18,
                "stl": 9,
                "blk": 4,
                "tov": 14,
                "pf": 16,
                "team_rebounds": 0,
                "team_turnovers": 0,
            },
            "players": [
                {
                    "name": "Lukas Schmidt",
                    "jersey_number": 7,
                    "seconds_played": 1800,
                    "points": 24,
                    "fgm": 9,
                    "fga": 18,
                    "fg2m": 6,
                    "fg2a": 11,
                    "fg3m": 3,
                    "fg3a": 7,
                    "ftm": 3,
                    "fta": 4,
                    "orb": 3,
                    "drb": 5,
                    "trb": 8,
                    "ast": 5,
                    "stl": 3,
                    "blk": 1,
                    "tov": 3,
                    "pf": 2,
                    "is_starter": True,
                },
                {
                    "name": "Felix Weber",
                    "jersey_number": 10,
                    "seconds_played": 1600,
                    "points": 18,
                    "fgm": 7,
                    "fga": 14,
                    "fg2m": 5,
                    "fg2a": 9,
                    "fg3m": 2,
                    "fg3a": 5,
                    "ftm": 2,
                    "fta": 2,
                    "orb": 2,
                    "drb": 4,
                    "trb": 6,
                    "ast": 7,
                    "stl": 2,
                    "blk": 0,
                    "tov": 4,
                    "pf": 3,
                    "is_starter": True,
                },
                {
                    "name": "Jonas Meyer",
                    "jersey_number": 14,
                    "seconds_played": 1400,
                    "points": 16,
                    "fgm": 6,
                    "fga": 12,
                    "fg2m": 5,
                    "fg2a": 9,
                    "fg3m": 1,
                    "fg3a": 3,
                    "ftm": 3,
                    "fta": 4,
                    "orb": 4,
                    "drb": 7,
                    "trb": 11,
                    "ast": 2,
                    "stl": 1,
                    "blk": 2,
                    "tov": 2,
                    "pf": 4,
                    "is_starter": True,
                },
                {
                    "name": "Tim Becker",
                    "jersey_number": 21,
                    "seconds_played": 1200,
                    "points": 20,
                    "fgm": 8,
                    "fga": 21,
                    "fg2m": 6,
                    "fg2a": 16,
                    "fg3m": 2,
                    "fg3a": 5,
                    "ftm": 2,
                    "fta": 4,
                    "orb": 3,
                    "drb": 8,
                    "trb": 11,
                    "ast": 4,
                    "stl": 3,
                    "blk": 1,
                    "tov": 5,
                    "pf": 4,
                    "is_starter": True,
                },
            ],
        },
        "away_team": {
            "id": "TEM_DEMO_WOLVES_U16",
            "name": away_team,
            "points": 72,
            "stats": {
                "points": 72,
                "fgm": 28,
                "fga": 62,
                "fg2m": 22,
                "fg2a": 46,
                "fg3m": 6,
                "fg3a": 16,
                "ftm": 10,
                "fta": 16,
                "orb": 10,
                "drb": 22,
                "trb": 32,
                "ast": 14,
                "stl": 7,
                "blk": 3,
                "tov": 16,
                "pf": 18,
                "team_rebounds": 0,
                "team_turnovers": 0,
            },
            "players": [
                {
                    "name": "Maximilian Bauer",
                    "jersey_number": 4,
                    "seconds_played": 1700,
                    "points": 32,
                    "fgm": 12,
                    "fga": 24,
                    "fg2m": 9,
                    "fg2a": 17,
                    "fg3m": 3,
                    "fg3a": 7,
                    "ftm": 5,
                    "fta": 7,
                    "orb": 2,
                    "drb": 4,
                    "trb": 6,
                    "ast": 4,
                    "stl": 2,
                    "blk": 0,
                    "tov": 5,
                    "pf": 3,
                    "is_starter": True,
                },
                {
                    "name": "David Koch",
                    "jersey_number": 9,
                    "seconds_played": 1500,
                    "points": 22,
                    "fgm": 9,
                    "fga": 20,
                    "fg2m": 7,
                    "fg2a": 15,
                    "fg3m": 2,
                    "fg3a": 5,
                    "ftm": 2,
                    "fta": 4,
                    "orb": 3,
                    "drb": 6,
                    "trb": 9,
                    "ast": 6,
                    "stl": 3,
                    "blk": 1,
                    "tov": 4,
                    "pf": 4,
                    "is_starter": True,
                },
                {
                    "name": "Julian Fischer",
                    "jersey_number": 15,
                    "seconds_played": 1600,
                    "points": 18,
                    "fgm": 7,
                    "fga": 18,
                    "fg2m": 6,
                    "fg2a": 14,
                    "fg3m": 1,
                    "fg3a": 4,
                    "ftm": 3,
                    "fta": 5,
                    "orb": 5,
                    "drb": 12,
                    "trb": 17,
                    "ast": 4,
                    "stl": 2,
                    "blk": 2,
                    "tov": 7,
                    "pf": 5,
                    "is_starter": True,
                },
            ],
        },
    }


def create_sample_pbp(game_id: str, home_team: str, away_team: str) -> Dict[str, Any]:
    """Generate deterministic Play-by-Play event stream JSON."""
    return {
        "game_id": game_id,
        "events": [
            {
                "period": 1,
                "clock": "10:00",
                "clock_display": "10:00",
                "event_type": "PERIOD_START",
                "home_score": 0,
                "away_score": 0,
                "description": "Period 1 begins",
            },
            {
                "period": 1,
                "clock": "09:45",
                "clock_display": "09:45",
                "event_type": "SHOT",
                "event_subtype": "2PT_JUMP",
                "team": home_team,
                "player": "Lukas Schmidt",
                "jersey_number": 7,
                "points": 2,
                "is_home": True,
                "home_score": 2,
                "away_score": 0,
                "x": 5.2,
                "y": 4.1,
                "distance_m": 4.5,
                "description": "Lukas Schmidt made 2pt jump shot",
            },
            {
                "period": 1,
                "clock": "09:20",
                "clock_display": "09:20",
                "event_type": "SHOT",
                "event_subtype": "3PT_JUMP",
                "team": away_team,
                "player": "Maximilian Bauer",
                "jersey_number": 4,
                "points": 3,
                "is_home": False,
                "home_score": 2,
                "away_score": 3,
                "x": 7.1,
                "y": 1.2,
                "distance_m": 6.75,
                "description": "Maximilian Bauer made 3pt shot",
            },
            {
                "period": 4,
                "clock": "00:05",
                "clock_display": "00:05",
                "event_type": "SHOT",
                "event_subtype": "2PT_LAYUP",
                "team": home_team,
                "player": "Felix Weber",
                "jersey_number": 10,
                "points": 2,
                "is_home": True,
                "home_score": 78,
                "away_score": 72,
                "x": 1.1,
                "y": 0.5,
                "distance_m": 1.2,
                "description": "Felix Weber driving layup",
            },
            {
                "period": 4,
                "clock": "00:00",
                "clock_display": "00:00",
                "event_type": "PERIOD_END",
                "home_score": 78,
                "away_score": 72,
                "description": "End of 4th Period",
            },
        ],
    }


def create_sample_video(game_id: str) -> Dict[str, Any]:
    """Generate deterministic video metadata JSON with sync anchors."""
    return {
        "video_id": f"VID_{game_id}",
        "game_id": game_id,
        "file_path": f"data/raw/video/{game_id.lower()}.mp4",
        "duration_seconds": 5400.0,  # 90 mins total broadcast
        "container_format": "mp4",
        "codec": "h264",
        "resolution_width": 1920,
        "resolution_height": 1080,
        "fps": 30.0,
        "file_size_bytes": 1048576000,
        "checksum_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "camera_angle": "TACTICAL_WIDE",
        "sync_tags": [
            {
                "event_id": None,
                "start_s": 120.0,
                "end_s": 135.0,
                "confidence": "EXACT",
                "method": "MANUAL",
                "verified_by": "coach_scout_01",
            }
        ],
    }


def generate_all_permutations() -> Dict[str, Dict[str, Path]]:
    """Generate synthetic test files for all 7 availability permutations."""
    Settings.ensure_directories()
    raw_box_dir = Settings.RAW_DIR / "boxscore"
    raw_pbp_dir = Settings.RAW_DIR / "pbp"
    raw_vid_dir = Settings.RAW_DIR / "video"

    home_team = "Rheinland Falcons U16"
    away_team = "Neckar Wolves U16"

    permutations = {
        "GAME_DEMO_001_ALL": {"box": True, "pbp": True, "vid": True},
        "GAME_DEMO_002_BOX_PBP": {"box": True, "pbp": True, "vid": False},
        "GAME_DEMO_003_BOX_VID": {"box": True, "pbp": False, "vid": True},
        "GAME_DEMO_004_PBP_VID": {"box": False, "pbp": True, "vid": True},
        "GAME_DEMO_005_BOX_ONLY": {"box": True, "pbp": False, "vid": False},
        "GAME_DEMO_006_PBP_ONLY": {"box": False, "pbp": True, "vid": False},
        "GAME_DEMO_007_VID_ONLY": {"box": False, "pbp": False, "vid": True},
    }

    manifest = {}

    for gid, sources in permutations.items():
        manifest[gid] = {}

        # Boxscore
        if sources["box"]:
            box_data = create_sample_boxscore(gid, home_team, away_team)
            box_file = raw_box_dir / f"{gid.lower()}_boxscore.json"
            box_file.write_text(json.dumps(box_data, indent=2), encoding="utf-8")
            manifest[gid]["boxscore"] = box_file
        else:
            manifest[gid]["boxscore"] = None

        # PBP
        if sources["pbp"]:
            pbp_data = create_sample_pbp(gid, home_team, away_team)
            pbp_file = raw_pbp_dir / f"{gid.lower()}_pbp.json"
            pbp_file.write_text(json.dumps(pbp_data, indent=2), encoding="utf-8")
            manifest[gid]["pbp"] = pbp_file
        else:
            manifest[gid]["pbp"] = None

        # Video
        if sources["vid"]:
            vid_data = create_sample_video(gid)
            vid_file = raw_vid_dir / f"{gid.lower()}_video.json"
            vid_file.write_text(json.dumps(vid_data, indent=2), encoding="utf-8")
            manifest[gid]["video"] = vid_file
        else:
            manifest[gid]["video"] = None

    return manifest


if __name__ == "__main__":
    manifest = generate_all_permutations()
    print(f"Generated synthetic test fixtures for {len(manifest)} permutations:")
    for gid, files in manifest.items():
        print(f"  - {gid}: box={bool(files['boxscore'])}, pbp={bool(files['pbp'])}, vid={bool(files['video'])}")
