"""Rheinland Falcons Intelligence — CLI Tool for Local Match Video Ingestion.

Usage examples:
    # 1. Inspect and ingest local video into a scrimmage match:
    python -m python.operations.ingest_local_video --file data/video/demo_tactical_match.mp4 --squad U16 --game-type SCRIMMAGE --opponent Wolves

    # 2. Ingest against an existing registered game:
    python -m python.operations.ingest_local_video --file data/video/my_game.mp4 --game-id GAM_U16_OFFICIAL_20251012_01

    # 3. Dry-run inspect only:
    python -m python.operations.ingest_local_video --file data/video/demo_tactical_match.mp4 --dry-run
"""

import argparse
import json
import sys
import uuid
from datetime import date
from pathlib import Path

# Ensure UTF-8 output on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from python.analytics.video_metadata import extract_video_metadata, format_seconds_to_timestamp
from python.database.video_evidence_repository import VideoEvidenceRepository


def main():
    parser = argparse.ArgumentParser(description="Ingest local match video into Rheinland Falcons Intelligence Platform.")
    parser.add_argument("--file", "-f", required=True, help="Path to video file (.mp4, .mov, etc.)")
    parser.add_argument("--game-id", "-g", default=None, help="Existing Game ID. If omitted, a match fixture is auto-created.")
    parser.add_argument("--squad", "-s", default="U16", choices=["U16", "U19"], help="Squad category (default: U16)")
    parser.add_argument("--game-type", "-t", default="SCRIMMAGE", choices=["OFFICIAL", "PRACTICE", "FRIENDLY", "SCRIMMAGE", "OTHER"], help="Match population scope")
    parser.add_argument("--opponent", "-o", default="Neckar Wolves", help="Opponent team name (default: Neckar Wolves)")
    parser.add_argument("--notes", "-n", default="Local video ingestion benchmark", help="Coach/analyst notes")
    parser.add_argument("--camera-angle", "-a", default="Tactical High", help="Camera perspective (e.g. Tactical High, Broadcast, Baseline)")
    parser.add_argument("--dry-run", action="store_true", help="Inspect and display metadata without modifying database")

    args = parser.parse_args()

    video_path = Path(args.file).resolve()
    if not video_path.exists():
        print(f"[ERROR] Video file does not exist: {video_path}")
        sys.exit(1)

    print("=" * 70)
    print("RHEINLAND FALCONS — LOCAL VIDEO INGESTION ENGINE")
    print("=" * 70)
    print(f"File Path: {video_path}")
    print(f"File Size: {video_path.stat().st_size / (1024 * 1024):.2f} MB")
    print("\n[1/3] Extracting Technical Metadata...")

    meta = extract_video_metadata(video_path)
    if not meta["is_valid"]:
        print(f"[ERROR] Video decoding failed: {meta.get('error_message')}")
        sys.exit(1)

    readiness = meta["readiness"]
    print(f"  Container:      {meta['container_format']} (Codec: {meta['codec']})")
    print(f"  Resolution:     {meta['resolution_display']} ({meta['aspect_ratio']})")
    print(f"  FPS:            {meta['fps']}")
    print(f"  Duration:       {meta['duration_display']} ({meta['duration_seconds']:.1f}s)")
    print(f"  Audio Present:  {meta['audio_present']}")
    print(f"  SHA-256:        {meta['checksum_sha256'][:16]}...")
    print(f"  Readiness:      {readiness['status']} ({readiness['badge']})")
    print(f"  Diagnosis:      {readiness['headline']}")
    for c in readiness.get("criteria", []):
        print(f"    - [{c['status']}] {c['name']}: {c['detail']}")

    if args.dry_run:
        print("\n[DRY RUN COMPLETE] No changes written to database.")
        sys.exit(0)

    print("\n[2/3] Registering Fixture & Population Isolation...")
    repo = VideoEvidenceRepository()

    game_id = args.game_id
    if not game_id:
        today_str = date.today().strftime("%Y%m%d")
        opp_clean = args.opponent.upper().replace(" ", "_")[:10]
        game_id = f"GAM_{args.squad}_{args.game_type}_{today_str}_{opp_clean}"
        home_tid = "TEM_DEMO_U16" if args.squad == "U16" else "TEM_DEMO_U19"
        away_tid = "TEM_DEMO_WOLVES_U16" if "NECKAR_WOLVES" in opp_clean else f"TEM_{opp_clean}"
        comp_id = "CMP_DEMO_U16" if args.game_type == "OFFICIAL" else "CMP_ACADEMY_PRAC"
        season_id = "SEA_DEMO_2025"

        repo.register_match_if_not_exists(
            game_id=game_id,
            home_team_id=home_tid,
            away_team_id=away_tid,
            game_date=str(date.today()),
            game_type=args.game_type,
            season_id=season_id,
            competition_id=comp_id,
            venue="Falcons Dome"
        )
        print(f"  Fixture registered: {game_id} (Type: {args.game_type}, Squad: {args.squad})")
    else:
        print(f"  Using specified game fixture: {game_id}")

    print("\n[3/3] Registering Video Entity in DuckDB...")
    video_id = f"VID_{uuid.uuid4().hex[:10].upper()}"
    repo.register_video({
        "video_id": video_id,
        "game_id": game_id,
        "file_path": str(video_path),
        "filename": video_path.name,
        "duration_seconds": meta["duration_seconds"],
        "container_format": meta["container_format"],
        "codec": meta["codec"],
        "resolution_width": meta["resolution_width"],
        "resolution_height": meta["resolution_height"],
        "fps": meta["fps"],
        "file_size_bytes": meta["file_size_bytes"],
        "checksum_sha256": meta["checksum_sha256"],
        "camera_angle": args.camera_angle,
        "analysis_focus": ["Defense", "Tactical review", "Individual player"],
        "notes": args.notes,
        "processing_status": meta["processing_status"],
        "readiness_status": meta["readiness_status"],
        "audio_present": meta["audio_present"],
        "created_by": "CLI Operator"
    })
    print(f"  Video ID created: {video_id}")
    print("=" * 70)
    print("SUCCESS: Match video successfully ingested and ready for analysis!")
    print(f"  Launch platform:  streamlit run app/main.py")
    print(f"  Navigate to:      Hub 7 (Video Analysis & Match Film)")
    print(f"  Select Match:     {game_id}")
    print(f"  Select Video:     {video_id}")
    print("=" * 70)


if __name__ == "__main__":
    main()
