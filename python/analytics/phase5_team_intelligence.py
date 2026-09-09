"""Phase 5 Team Intelligence Analytical Layer."""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

sys.path.insert(0, ".")

from python.database.duckdb_manager import DuckDBManager

DERIVED_DIR = Path("data/derived")
DERIVED_DIR.mkdir(parents=True, exist_ok=True)

def build_team_intelligence():
    print("==========================================================================")
    print(" [PHASE 5] BUILDING TEAM INTELLIGENCE LAYER                              ")
    print("==========================================================================")

    db = DuckDBManager()

    # Query Team Game Ratings
    df_team_games = db.query_df("""
        SELECT
            vt.game_id,
            g.season_id,
            g.game_date,
            vt.team_id,
            vt.team_name,
            vt.is_home,
            vt.points,
            vt.opp_points,
            vt.point_diff,
            vt.possessions,
            vt.efg_pct,
            vt.tov_pct,
            vt.orb_pct,
            vt.ftr,
            vt.ortg,
            vt.drtg,
            vt.net_rtg,
            CASE WHEN vt.points > vt.opp_points THEN 'WIN' ELSE 'LOSS' END AS outcome
        FROM view_team_game_ratings vt
        JOIN game g ON vt.game_id = g.game_id
        WHERE vt.possessions >= 40
        ORDER BY g.game_date ASC
    """)

    # Query Team Season Aggregations
    df_team_seasons = db.query_df("""
        SELECT
            vt.team_id,
            vt.team_name,
            g.season_id,
            COUNT(*) AS games_played,
            SUM(CASE WHEN vt.points > vt.opp_points THEN 1 ELSE 0 END) AS wins,
            SUM(CASE WHEN vt.points < vt.opp_points THEN 1 ELSE 0 END) AS losses,
            ROUND(SUM(CASE WHEN vt.points > vt.opp_points THEN 1.0 ELSE 0.0 END) / COUNT(*), 3) AS win_pct,
            ROUND(AVG(vt.points), 1) AS ppg,
            ROUND(AVG(vt.opp_points), 1) AS opp_ppg,
            ROUND(AVG(vt.point_diff), 1) AS avg_point_diff,
            ROUND(AVG(vt.possessions), 1) AS pace,
            ROUND(AVG(vt.ortg), 1) AS ortg,
            ROUND(AVG(vt.drtg), 1) AS drtg,
            ROUND(AVG(vt.net_rtg), 1) AS net_rtg,
            -- Weighted Four Factors
            ROUND((SUM(vt.fgm) + 0.5 * SUM(vt.fg3m)) * 100.0 / NULLIF(SUM(vt.fga), 0), 1) AS weighted_efg_pct,
            ROUND(SUM(vt.tov) * 100.0 / NULLIF(SUM(vt.fga) + 0.44 * SUM(vt.fta) + SUM(vt.tov), 0), 1) AS weighted_tov_pct,
            ROUND(SUM(vt.orb) * 100.0 / NULLIF(SUM(vt.orb) + SUM(vt.opp_drb), 0), 1) AS weighted_orb_pct,
            ROUND(SUM(vt.fta) / NULLIF(SUM(vt.fga), 0.0), 3) AS weighted_ftr
        FROM view_team_game_ratings vt
        JOIN game g ON vt.game_id = g.game_id
        GROUP BY vt.team_id, vt.team_name, g.season_id
        HAVING COUNT(*) >= 2
    """)

    # Combine into unified team intelligence dataset with analytical level flag
    records = []
    
    # Season Level
    for _, r in df_team_seasons.iterrows():
        records.append({
            "record_level": "TEAM_SEASON",
            "entity_id": r["team_id"],
            "team_name": r["team_name"],
            "season_id": r["season_id"],
            "game_id": None,
            "game_date": None,
            "is_home": None,
            "games_played": int(r["games_played"]),
            "wins": int(r["wins"]),
            "losses": int(r["losses"]),
            "win_pct": float(r["win_pct"]),
            "points": float(r["ppg"]),
            "opp_points": float(r["opp_ppg"]),
            "point_diff": float(r["avg_point_diff"]),
            "possessions": float(r["pace"]),
            "ortg": float(r["ortg"]),
            "drtg": float(r["drtg"]),
            "net_rtg": float(r["net_rtg"]),
            "efg_pct": float(r["weighted_efg_pct"]),
            "tov_pct": float(r["weighted_tov_pct"]),
            "orb_pct": float(r["weighted_orb_pct"]),
            "ftr": float(r["weighted_ftr"]),
            "outcome": None,
            "uncertainty_status": "LOW" if r["games_played"] >= 10 else "MEDIUM",
        })

    # Game Level
    for _, r in df_team_games.iterrows():
        records.append({
            "record_level": "TEAM_GAME",
            "entity_id": r["team_id"],
            "team_name": r["team_name"],
            "season_id": r["season_id"],
            "game_id": r["game_id"],
            "game_date": str(r["game_date"]),
            "is_home": bool(r["is_home"]),
            "games_played": 1,
            "wins": 1 if r["outcome"] == "WIN" else 0,
            "losses": 1 if r["outcome"] == "LOSS" else 0,
            "win_pct": 1.0 if r["outcome"] == "WIN" else 0.0,
            "points": float(r["points"]),
            "opp_points": float(r["opp_points"]),
            "point_diff": float(r["point_diff"]),
            "possessions": float(r["possessions"]),
            "ortg": float(r["ortg"]),
            "drtg": float(r["drtg"]),
            "net_rtg": float(r["net_rtg"]),
            "efg_pct": float(r["efg_pct"]),
            "tov_pct": float(r["tov_pct"]),
            "orb_pct": float(r["orb_pct"]),
            "ftr": float(r["ftr"]),
            "outcome": r["outcome"],
            "uncertainty_status": "EXACT_OBSERVATION",
        })

    df_ti = pd.DataFrame(records)
    p_ti = DERIVED_DIR / "team_intelligence.parquet"
    df_ti.to_parquet(p_ti, index=False)
    print(f"Exported '{p_ti.name}': {len(df_ti)} team intelligence records.")
    return df_ti

if __name__ == "__main__":
    build_team_intelligence()
