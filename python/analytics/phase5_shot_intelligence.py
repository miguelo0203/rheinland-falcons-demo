"""Phase 5 Shot Intelligence & Spatial Zone Analytics Layer."""

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

def classify_shot_zone(x: float, y: float, shot_type: str, status: str) -> str:
    if status != "OBSERVED" or pd.isna(x) or pd.isna(y):
        return "UNKNOWN_ZONE"
    
    # Distance from basket (assuming basket near x=140, y=25 on standard grid)
    dx = x - 140.0
    dy = y - 25.0
    dist = np.sqrt(dx**2 + dy**2)
    
    if shot_type == "3PT":
        if y <= 50.0 and (x <= 35.0 or x >= 245.0):
            return "CORNER_3PT"
        return "ABOVE_THE_BREAK_3PT"
    else:
        if dist <= 35.0:
            return "RESTRICTED_AREA"
        elif dist <= 75.0 and abs(dx) <= 45.0:
            return "PAINT_NON_RA"
        else:
            return "MID_RANGE"

def build_shot_intelligence():
    print("==========================================================================")
    print(" [PHASE 5] BUILDING SHOT INTELLIGENCE LAYER                              ")
    print("==========================================================================")

    db = DuckDBManager()

    query = """
    SELECT
        s.shot_id,
        s.game_id,
        g.season_id,
        g.game_date,
        s.period,
        s.game_seconds_remaining,
        s.team_id,
        t.canonical_name AS team_name,
        s.player_id,
        p.canonical_name AS player_name,
        s.shot_type,
        s.is_made,
        s.points,
        s.x_coord,
        s.y_coord,
        s.shot_location_status,
        CASE WHEN s.team_id = 'TEM_DEMO_U16' THEN TRUE ELSE FALSE END AS is_falcons_shot
    FROM shot s
    JOIN team t ON s.team_id = t.team_id
    JOIN player p ON s.player_id = p.player_id
    JOIN game g ON s.game_id = g.game_id
    ORDER BY g.game_date ASC, s.shot_id ASC
    """
    df_shots = db.query_df(query)
    df_shots["shot_zone"] = df_shots.apply(
        lambda r: classify_shot_zone(r["x_coord"], r["y_coord"], r["shot_type"], r["shot_location_status"]),
        axis=1
    )

    # Expected Points per Attempt by zone
    zone_eppa = {
        "RESTRICTED_AREA": 1.18,
        "PAINT_NON_RA": 0.76,
        "MID_RANGE": 0.63,
        "CORNER_3PT": 1.15,
        "ABOVE_THE_BREAK_3PT": 0.82,
        "UNKNOWN_ZONE": 0.90,
    }
    df_shots["expected_points"] = df_shots["shot_zone"].map(zone_eppa)

    p_si = DERIVED_DIR / "shot_intelligence.parquet"
    df_shots.to_parquet(p_si, index=False)
    print(f"Exported '{p_si.name}': {len(df_shots)} shot intelligence records.")
    return df_shots

if __name__ == "__main__":
    build_shot_intelligence()
