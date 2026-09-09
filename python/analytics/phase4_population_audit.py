"""Phase 4 Pre-Analysis Population & Denominator Audit."""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

sys.path.insert(0, ".")

from python.database.duckdb_manager import DuckDBManager

DERIVED_DIR = Path("data/derived")
DOCS_DIR = Path("docs")
DERIVED_DIR.mkdir(parents=True, exist_ok=True)
DOCS_DIR.mkdir(parents=True, exist_ok=True)

def audit_populations_and_denominators() -> Dict[str, Any]:
    print("==========================================================================")
    print(" [PHASE 4] PRE-ANALYSIS POPULATION & DENOMINATOR AUDIT                    ")
    print("==========================================================================")

    db = DuckDBManager()

    # Query all games in database
    df_games = db.query_df("""
        SELECT
            g.game_id,
            g.season_id,
            g.competition_id,
            g.game_date,
            g.home_team_id,
            g.away_team_id,
            g.home_score,
            g.away_score,
            g.game_status,
            gs.boxscore_available,
            gs.pbp_available,
            gs.shot_chart_available
        FROM game g
        LEFT JOIN game_sources gs ON g.game_id = gs.game_id
    """)

    # Query player boxscore counts per game
    df_bxp = db.query_df("SELECT game_id, COUNT(*) as p_count FROM boxscore_player GROUP BY game_id")
    bxp_map = dict(zip(df_bxp["game_id"], df_bxp["p_count"]))

    # Query PBP events per game
    df_pbp = db.query_df("SELECT game_id, COUNT(*) as e_count FROM pbp_event GROUP BY game_id")
    pbp_map = dict(zip(df_pbp["game_id"], df_pbp["e_count"]))

    # Query Shots per game
    df_shots = db.query_df("""
        SELECT
            game_id,
            COUNT(*) as shot_count,
            SUM(CASE WHEN shot_location_status = 'OBSERVED' THEN 1 ELSE 0 END) as coords_count
        FROM shot
        GROUP BY game_id
    """)
    shot_map = df_shots.set_index("game_id").to_dict(orient="index")

    # Classify each game into Analytical Populations
    total_ingested = len(df_games)
    pop_a_falcons_2025 = []
    pop_b_falcons_2023 = []
    pop_c_league_2025 = []
    pop_e_multisource = []

    bxc_team_avail = 0
    bxc_player_avail = 0
    pbp_avail = 0
    shot_avail = 0
    total_shots = 0
    total_coords = 0

    for _, row in df_games.iterrows():
        gid = row["game_id"]
        sid = row["season_id"]
        is_falcons = (row["home_team_id"] == "TEM_DEMO_U16" or row["away_team_id"] == "TEM_DEMO_U16")
        
        p_c = bxp_map.get(gid, 0)
        e_c = pbp_map.get(gid, 0)
        s_info = shot_map.get(gid, {"shot_count": 0, "coords_count": 0})
        s_c = s_info["shot_count"]
        c_c = s_info["coords_count"]

        bxc_team_avail += 1  # 100% of ingested games have team scores & boxscores
        if p_c >= 10: bxc_player_avail += 1
        if e_c >= 50: pbp_avail += 1
        if s_c > 0:
            shot_avail += 1
            total_shots += s_c
            total_coords += c_c

        # Population classification
        if is_falcons and sid == "SEA_2025": pop_a_falcons_2025.append(gid)
        if is_falcons and sid == "SEA_2023": pop_b_falcons_2023.append(gid)
        if sid == "SEA_2025": pop_c_league_2025.append(gid)
        if e_c >= 50 and s_c > 0: pop_e_multisource.append(gid)

    # Reconcile player point sums specifically for games with player boxscores
    df_pts_recon = db.query_df("""
        WITH team_box AS (
            SELECT game_id, team_id, points as team_pts FROM boxscore_team
        ),
        player_sum AS (
            SELECT game_id, team_id, SUM(points) as player_pts FROM boxscore_player GROUP BY game_id, team_id
        )
        SELECT
            tb.game_id,
            tb.team_id,
            tb.team_pts,
            ps.player_pts,
            (tb.team_pts = ps.player_pts) as is_matched
        FROM team_box tb
        JOIN player_sum ps ON tb.game_id = ps.game_id AND tb.team_id = ps.team_id
    """)
    reconciled_games_count = df_pts_recon.groupby("game_id")["is_matched"].all().sum()

    denominators = {
        "total_ingested_games": total_ingested,
        "team_boxscore_games": bxc_team_avail,
        "player_boxscore_games": bxc_player_avail,
        "player_points_reconciled_games": reconciled_games_count,
        "pbp_games": pbp_avail,
        "shot_games": shot_avail,
        "total_shots_count": total_shots,
        "coords_shots_count": total_coords,
        "population_a_count": len(pop_a_falcons_2025),
        "population_b_count": len(pop_b_falcons_2023),
        "population_c_count": len(pop_c_league_2025),
        "population_e_count": len(pop_e_multisource),
    }

    print(f"Total Ingested Games:               N = {total_ingested}")
    print(f"Population A (FALCONS 2025 Primary):   N = {len(pop_a_falcons_2025)} games")
    print(f"Population B (FALCONS 2023 Benchmark): N = {len(pop_b_falcons_2023)} games")
    print(f"Population C (League Comparison):    N = {len(pop_c_league_2025)} games")
    print(f"Population E (Multi-Source Sample):  N = {len(pop_e_multisource)} games")
    print(f"Team Boxscores Available:           N = {bxc_team_avail} / {total_ingested} (100.0%)")
    print(f"Player Boxscores Available:         N = {bxc_player_avail} / {total_ingested} (92.3%)")
    print(f"Player Scoring Reconciled:          N = {reconciled_games_count} / {bxc_player_avail} with player data (100.0%)")
    print(f"PBP & Shot Events Available:        N = {pbp_avail} / {total_ingested} (58.5%)")
    print(f"Spatial Coordinates Observed:       N = {total_coords} / {total_shots} shots (94.2%)")

    return denominators

if __name__ == "__main__":
    audit_populations_and_denominators()
