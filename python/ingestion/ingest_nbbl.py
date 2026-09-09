"""Master Ingestion Script for Rheinland Falcons U19 / NBBL.

Ingests:
1. CMP_NBBL competition and TEM_DEMO_U19 team canonical records.
2. All 33 harvested NBBL 2023 matches (18 Rheinland matches + 15 benchmark matches).
3. Active 2025 NBBL roster declarations for TEM_DEMO_U19.
4. Refreshes analytical views and updates derived Parquets.
"""

import json
import os
import sys
import time
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from python.database.duckdb_manager import DuckDBManager
from python.database.analytics_views import create_analytics_views
from python.ingestion.jbbl_adapter import JBBLAdapter
from python.ingestion.provenance import ProvenanceTracker, generate_id
from python.ingestion.entity_resolver import EntityResolver
from python.ingestion.conflict_detector import ConflictDetector
from python.validation.engine import ValidationEngine
from python.models.canonical import Competition, Season, Team, Player, PlayerTeam
from python.operations.game_registry import build_game_registry
from python.analytics.phase5_team_intelligence import build_team_intelligence
from python.analytics.phase5_player_evolution import build_player_intelligence_and_evolution
from python.analytics.phase5_shot_intelligence import build_shot_intelligence
from python.analytics.phase5_coach_findings import build_coach_intelligence_findings

RAW_NBBL_DIR = PROJECT_ROOT / "data" / "raw" / "nbbl"


def ingest_nbbl():
    print("==========================================================================")
    print("      STARTING NBBL (U19) INGESTION & ACADEMY EXPANSION PIPELINE         ")
    print("==========================================================================")
    t0 = time.time()

    db = DuckDBManager()
    db.initialize_schema()

    # 1. Register NBBL Competition
    print("\n--- 1. Registering Competition & Base Entities ---")
    comp_nbbl = Competition(
        competition_id="CMP_NBBL",
        name="Nachwuchs-Basketball-Bundesliga (NBBL U19)",
        gender="MALE",
        age_category="U19",
        country="DE",
        governing_body="DBB / BBL",
    )
    db.insert_records("competition", [comp_nbbl.model_dump()], pk_col="competition_id")
    print("  Registered competition: CMP_NBBL")

    # 2. Register TEM_DEMO_U19 (Rheinland Falcons U19)
    team_rheinland_u19 = Team(
        team_id="TEM_DEMO_U19",
        canonical_name="Rheinland Falcons Basketball",
        short_name="Rheinland",
        club_name="HMC",
        age_category="U19",
    )
    db.insert_records("team", [team_rheinland_u19.model_dump()], pk_col="team_id")
    print("  Registered team: TEM_DEMO_U19 (Rheinland Falcons U19)")

    # 3. Setup Adapters & Validation Engine
    resolver = EntityResolver()
    prov_tracker = ProvenanceTracker()
    conflict_detector = ConflictDetector()
    validator = ValidationEngine(conflict_detector=conflict_detector)
    adapter = JBBLAdapter(entity_resolver=resolver, provenance_tracker=prov_tracker)

    # 4. Ingest 2023 NBBL Matches
    nbbl_2023_dir = RAW_NBBL_DIR / "2023"
    game_folders = sorted([d for d in nbbl_2023_dir.iterdir() if d.is_dir()], key=lambda d: d.name) if nbbl_2023_dir.exists() else []
    print(f"\n--- 2. Ingesting {len(game_folders)} NBBL 2023 Raw Matches ---")

    ingested_count = 0
    passed_val_count = 0

    for idx, g_dir in enumerate(game_folders, 1):
        gid = g_dir.name
        header_f = g_dir / "raw_game_header.json"
        stream_files = list(g_dir.glob("raw_socket_stream*"))
        if not header_f.exists() or not stream_files:
            print(f"  [{idx:2d}/{len(game_folders):2d}] Game {gid}: Missing raw files. Skipping.")
            continue

        stream_f = stream_files[0]
        try:
            raw_data = adapter.extract(g_dir)
            payload = adapter.normalize(
                raw_data=raw_data,
                file_path=stream_f,
                game_id=f"GAM_{gid}",
                season_id="SEA_2023",
                competition_id="CMP_NBBL",
            )

            # Validate Game
            val_out = validator.validate_game(
                game_id=f"GAM_{gid}",
                game=payload.games[0] if payload.games else None,
                boxscore_teams=payload.boxscore_teams,
                boxscore_players=payload.boxscore_players,
                pbp_events=payload.pbp_events,
                shots=payload.shots,
                boxscore_path=str(stream_f.as_posix()),
                pbp_path=str(stream_f.as_posix()),
            )

            game_src = val_out["game_sources"]
            val_logs = val_out["validation_logs"]

            if "PASS" in game_src.validation_status.value:
                passed_val_count += 1

            # Insert normalized payload and validation
            db.insert_normalized_payload(payload)
            db.insert_validation_logs(val_logs)
            db.upsert_game_sources(
                game_id=f"GAM_{gid}",
                boxscore_available=bool(payload.boxscore_players),
                pbp_available=bool(payload.pbp_events),
                video_available=False,
                shot_chart_available=bool(payload.shots),
                boxscore_path=str(stream_f.as_posix()),
                pbp_path=str(stream_f.as_posix()),
                val_status=game_src.validation_status,
                comp_tier=game_src.completeness_score,
                qual_tier=game_src.overall_quality,
            )

            ingested_count += 1
            print(f"  [{idx:2d}/{len(game_folders):2d}] Game {gid}: Ingested {len(payload.boxscore_players)} players -> [{game_src.validation_status.value}]")

        except Exception as e:
            print(f"  [{idx:2d}/{len(game_folders):2d}] Game {gid}: ERROR during normalization: {e}")

    # 5. Ingest 2025 NBBL Active Roster
    print("\n--- 3. Ingesting 2025 NBBL Active Roster for TEM_DEMO_U19 ---")
    roster_2025_file = RAW_NBBL_DIR / "2025" / "team_1083.json"
    if roster_2025_file.exists():
        try:
            team_1083_data = json.loads(roster_2025_file.read_text(encoding="utf-8"))
            roster_list = team_1083_data.get("roster", [])
            print(f"  Loaded {len(roster_list)} player declarations from team_1083.json.")

            players_to_insert = []
            pt_to_insert = []
            now_dt = datetime.now(timezone.utc)

            for p_raw in roster_list:
                master_pid = p_raw.get("playerId")
                if not master_pid:
                    continue
                c_pid = f"PLY_{master_pid}"
                full_name = f"{p_raw.get('firstName', '')} {p_raw.get('lastName', '')}".strip()
                dob = date.fromisoformat(p_raw["birthDate"]) if p_raw.get("birthDate") else None
                height_cm = round(p_raw["height"] * 100.0, 1) if p_raw.get("height") else None
                nats = ",".join(p_raw.get("nationalities", [])) if p_raw.get("nationalities") else None

                players_to_insert.append({
                    "player_id": c_pid,
                    "canonical_name": full_name,
                    "first_name": p_raw.get("firstName"),
                    "last_name": p_raw.get("lastName"),
                    "birth_date": dob,
                    "height_cm": height_cm,
                    "listed_position": p_raw.get("position"),
                    "nationality": nats,
                    "created_at": now_dt,
                })

                pt_to_insert.append({
                    "player_team_id": generate_id("PLT"),
                    "player_id": c_pid,
                    "team_id": "TEM_DEMO_U19",
                    "season_id": "SEA_2025",
                    "jersey_number": str(p_raw.get("NUM", "")),
                    "is_active": True,
                })

            p_count = db.insert_records("player", players_to_insert, pk_col="player_id")
            pt_count = db.insert_records("player_team", pt_to_insert, pk_col="player_team_id")
            print(f"  Processed {len(players_to_insert)} players ({p_count} newly inserted into player, {pt_count} into player_team).")
        except Exception as e:
            print(f"  Error processing 2025 roster: {e}")

    # 6. Recreate Analytical Views
    print("\n--- 4. Refreshing DuckDB Analytical Views ---")
    create_analytics_views(db)

    # 7. Recompute Derived Intelligence Parquets
    print("\n--- 5. Recomputing Derived Intelligence Parquets ---")
    try:
        build_game_registry()
        build_team_intelligence()
        build_player_intelligence_and_evolution()
        build_shot_intelligence()
        build_coach_intelligence_findings()
    except Exception as e:
        print(f"  Warning during Parquet recomputation: {e}")

    elapsed = round(time.time() - t0, 2)
    print("\n==========================================================================")
    print(f" NBBL INGESTION COMPLETE IN {elapsed}s: {ingested_count} matches ingested ({passed_val_count} passed validation)")
    print("==========================================================================")


if __name__ == "__main__":
    ingest_nbbl()
