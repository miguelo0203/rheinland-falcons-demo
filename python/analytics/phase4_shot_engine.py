"""Phase 4 Shot Spatial Distribution & Zone Analysis Engine."""

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
from python.models.enums import ObservationStatus

DERIVED_DIR = Path("data/derived")
DOCS_DIR = Path("docs")
DERIVED_DIR.mkdir(parents=True, exist_ok=True)
DOCS_DIR.mkdir(parents=True, exist_ok=True)

def classify_shot_zone(x: float, y: float, shot_type: str, status: str) -> str:
    """Classifies shot into tactical zone based on standard FIBA half-court geometry."""
    if status != "OBSERVED" or pd.isna(x) or pd.isna(y):
        return "UNKNOWN_ZONE"
    
    # Distance from basket (assuming basket centered at x=140, y=25 on standard 280x200 grid)
    dx = x - 140.0
    dy = y - 25.0
    dist = np.sqrt(dx**2 + dy**2)
    
    if shot_type == "3PT":
        # Straight corner line extends up to y=50 where it meets the 6.75m arc
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

def run_shot_engine():
    print("==========================================================================")
    print(" [PHASE 4] EXECUTING SHOT SPATIAL & ZONE ANALYSIS ENGINE                  ")
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

    # Classify Zone for each shot
    df_shots["shot_zone"] = df_shots.apply(
        lambda r: classify_shot_zone(r["x_coord"], r["y_coord"], r["shot_type"], r["shot_location_status"]),
        axis=1
    )

    p_shots = DERIVED_DIR / "shot_analysis.parquet"
    df_shots.to_parquet(p_shots, index=False)
    print(f"Exported '{p_shots.name}': {len(df_shots)} discrete shot analysis records.")

    # Zone summary statistics
    zone_summary = df_shots.groupby(["team_name", "shot_zone"]).agg(
        total_shots=("shot_id", "count"),
        made_shots=("is_made", lambda x: (x == True).sum()),
        total_points=("points", "sum")
    ).reset_index()
    zone_summary["fg_pct"] = round(zone_summary["made_shots"] * 100.0 / zone_summary["total_shots"], 1)

    return df_shots, zone_summary

if __name__ == "__main__":
    run_shot_engine()
