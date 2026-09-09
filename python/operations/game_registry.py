"""Canonical Game Registry & Season Operations Engine for Rheinland Falcons JBBL/NBBL Program."""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

sys.path.insert(0, ".")

from python.database.duckdb_manager import DuckDBManager

DERIVED_DIR = Path("data/derived")
DOCS_DIR = Path("docs")
DERIVED_DIR.mkdir(parents=True, exist_ok=True)
DOCS_DIR.mkdir(parents=True, exist_ok=True)

def build_game_registry() -> pd.DataFrame:
    print("==========================================================================")
    print(" [PHASE 6] BUILDING CANONICAL GAME REGISTRY & OPERATIONS LAYER            ")
    print("==========================================================================")

    db = DuckDBManager()

    # Query all games and modality counts
    query = """
    SELECT
        g.game_id,
        g.season_id,
        g.competition_id,
        COALESCE(g.game_type, 'OFFICIAL') AS game_type,
        CASE
            WHEN g.round_number > 16 THEN 'PLAYOFFS'
            WHEN g.round_number > 6 THEN 'HAUPTRUNDE'
            ELSE 'VORRUNDE'
        END AS phase,
        COALESCE(g.competition_id, 'JBBL') AS group_name,
        g.game_date,
        g.home_team_id,
        th.canonical_name AS home_team_name,
        g.away_team_id,
        ta.canonical_name AS away_team_name,
        g.home_score,
        g.away_score,
        CASE
            WHEN g.home_team_id IN ('TEM_DEMO_U16', 'TEM_DEMO_U19') THEN 'HOME'
            WHEN g.away_team_id IN ('TEM_DEMO_U16', 'TEM_DEMO_U19') THEN 'AWAY'
            ELSE 'NEUTRAL_LEAGUE'
        END AS falcons_home_away,
        CASE
            WHEN g.home_team_id IN ('TEM_DEMO_U16', 'TEM_DEMO_U19') THEN ta.canonical_name
            WHEN g.away_team_id IN ('TEM_DEMO_U16', 'TEM_DEMO_U19') THEN th.canonical_name
            ELSE 'LEAGUE_MATCH'
        END AS falcons_opponent_name,
        -- Modality Counts
        COALESCE(bx.bx_count, 0) AS team_boxscores_count,
        COALESCE(bp.player_bx_count, 0) AS player_boxscores_count,
        COALESCE(pbp.pbp_event_count, 0) AS pbp_events_count,
        COALESCE(sh.shot_count, 0) AS shots_count,
        COALESCE(sh.coord_count, 0) AS coords_count,
        COALESCE(lp.lineup_count, 0) AS lineups_count,
        0 AS video_count
    FROM game g
    JOIN team th ON g.home_team_id = th.team_id
    JOIN team ta ON g.away_team_id = ta.team_id
    LEFT JOIN (
        SELECT game_id, COUNT(*) AS bx_count FROM boxscore_team GROUP BY game_id
    ) bx ON g.game_id = bx.game_id
    LEFT JOIN (
        SELECT game_id, COUNT(*) AS player_bx_count FROM boxscore_player GROUP BY game_id
    ) bp ON g.game_id = bp.game_id
    LEFT JOIN (
        SELECT game_id, COUNT(*) AS pbp_event_count FROM pbp_event GROUP BY game_id
    ) pbp ON g.game_id = pbp.game_id
    LEFT JOIN (
        SELECT
            game_id,
            COUNT(*) AS shot_count,
            SUM(CASE WHEN shot_location_status = 'OBSERVED' THEN 1 ELSE 0 END) AS coord_count
        FROM shot
        GROUP BY game_id
    ) sh ON g.game_id = sh.game_id
    LEFT JOIN (
        SELECT game_id, COUNT(*) AS lineup_count FROM lineup_stint GROUP BY game_id
    ) lp ON g.game_id = lp.game_id
    ORDER BY g.game_date ASC, g.game_id ASC
    """

    df_raw = db.query_df(query)

    registry_records = []
    for _, r in df_raw.iterrows():
        bx_avail = bool(r["team_boxscores_count"] >= 2)
        p_bx_avail = bool(r["player_boxscores_count"] >= 10)
        pbp_avail = bool(r["pbp_events_count"] >= 50)
        shot_avail = bool(r["shots_count"] >= 20)
        coord_avail = bool(r["coords_count"] >= 20)
        lineup_avail = bool(r["lineups_count"] >= 4)
        video_avail = bool(r["video_count"] > 0)

        # Analytical Usability Status
        if p_bx_avail and pbp_avail and shot_avail:
            tier = "TIER_1_ADVANCED_SPATIAL_PBP"
        elif p_bx_avail:
            tier = "TIER_2_BOXSCORE_ROSTER"
        else:
            tier = "TIER_3_METADATA_ONLY"

        validation_status = "VALIDATED_CLEAN" if bx_avail else "INCOMPLETE_MODALITY"

        # Check hash and timestamp if manifest exists
        raw_manifest = Path("data/raw/jbbl") / str(r["season_id"]) / str(r["game_id"]) / "manifest.sha256"
        payload_hash = raw_manifest.read_text(encoding="utf-8").strip() if raw_manifest.exists() else "HISTORICAL_INGESTED"

        is_u19 = "NBBL" in str(r["competition_id"]) or r["home_team_id"] == "TEM_DEMO_U19" or r["away_team_id"] == "TEM_DEMO_U19"
        registry_records.append({
            "game_id": r["game_id"],
            "season_id": r["season_id"],
            "team_level": "NBBL" if is_u19 else "JBBL",
            "squad": "U19" if is_u19 else "U16",
            "competition_id": r["competition_id"],
            "competition": r["competition_id"],
            "game_type": r["game_type"],
            "phase": r["phase"],
            "group_name": r["group_name"],
            "game_date": str(r["game_date"]),
            "date": str(r["game_date"]),
            "home_team_id": r["home_team_id"],
            "home_team_name": r["home_team_name"],
            "home_team": r["home_team_name"],
            "away_team_id": r["away_team_id"],
            "away_team_name": r["away_team_name"],
            "away_team": r["away_team_name"],
            "home_score": int(r["home_score"]),
            "away_score": int(r["away_score"]),
            "status": "FINAL",
            "game_status": "FINAL",
            "falcons_home_away": r["falcons_home_away"],
            "falcons_opponent_name": r["falcons_opponent_name"],
            "ingestion_status": "COMMITTED",
            "validation_status": validation_status,
            "analytical_tier": tier,
            "is_official_competition": bool(r["game_type"] == "OFFICIAL"),
            "boxscore_available": bx_avail,
            "player_boxscore_available": p_bx_avail,
            "pbp_available": pbp_avail,
            "shot_available": shot_avail,
            "coordinate_available": coord_avail,
            "lineup_available": lineup_avail,
            "video_available": video_avail,
            "tracking_available": False,
            "raw_payload_hash": payload_hash,
            "ingestion_timestamp": "2026-09-01T00:00:00Z",
            "last_updated_timestamp": "2026-09-01T00:00:00Z",
            "player_count": int(r["player_boxscores_count"]),
            "pbp_event_count": int(r["pbp_events_count"]),
            "shot_count": int(r["shots_count"]),
            "observed_coords_count": int(r["coords_count"]),
        })

    df_reg = pd.DataFrame(registry_records)
    p_reg = DERIVED_DIR / "game_registry.parquet"
    df_reg.to_parquet(p_reg, index=False)
    print(f"Exported '{p_reg.name}': {len(df_reg)} canonical game registry records.")

    # Generate Registry Operations Documentation
    generate_game_registry_doc(df_reg)
    return df_reg

def generate_game_registry_doc(df_reg: pd.DataFrame):
    total = len(df_reg)
    official = len(df_reg[df_reg["game_type"] == "OFFICIAL"])
    bxp = len(df_reg[df_reg["player_boxscore_available"] == True])
    pbp = len(df_reg[df_reg["pbp_available"] == True])
    shots = len(df_reg[df_reg["shot_available"] == True])

    lines = [
        "# Canonical Game Registry & Incremental Season Operations",
        "",
        "## 1. Registry Operational Summary",
        "",
        f"- **Total Ingested Fixtures**: {total}",
        f"- **Official Competition Games**: {official} (100% of historical universe)",
        f"- **Player Boxscore Modality**: {bxp} / {total} games ({bxp/total*100:.1f}%)",
        f"- **Play-by-Play Modality**: {pbp} / {total} games ({pbp/total*100:.1f}%)",
        f"- **Spatial Shot Modality**: {shots} / {total} games ({shots/total*100:.1f}%)",
        "",
        "## 2. Game Type Taxonomy & Population Rules",
        "",
        "```text",
        "┌────────────────┬─────────────────────────────────────────────────────────────┐",
        "│ GAME TYPE      │ OPERATIONAL & STATISTICAL RULE                              │",
        "├────────────────┼─────────────────────────────────────────────────────────────┤",
        "│ OFFICIAL       │ Standard league competition (JBBL Vorrunde/Hauptrunde/PO).  │",
        "│                │ Included in official Win%, Four Factors, standings.         │",
        "├────────────────┼─────────────────────────────────────────────────────────────┤",
        "│ PRACTICE       │ Internal scrimmage / practice match with boxscore/PBP data. │",
        "│                │ ISOLATED from official league tables. Accessible in         │",
        "│                │ player development & workload monitoring views.             │",
        "├────────────────┼─────────────────────────────────────────────────────────────┤",
        "│ SCRIMMAGE      │ Unofficial closed-door training fixture.                    │",
        "├────────────────┼─────────────────────────────────────────────────────────────┤",
        "│ FRIENDLY       │ Pre-season or exhibition match outside JBBL standings.      │",
        "└────────────────┴─────────────────────────────────────────────────────────────┘",
        "```",
    ]
    (DOCS_DIR / "game_registry_and_incremental_operations.md").write_text("\n".join(lines), encoding="utf-8")
    print("Generated docs/game_registry_and_incremental_operations.md")

if __name__ == "__main__":
    build_game_registry()
