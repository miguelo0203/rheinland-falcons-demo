"""Phase 4 Longitudinal Player Performance, Weekly Monitoring & Role Evolution Engine."""

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
DOCS_DIR = Path("docs")
DERIVED_DIR.mkdir(parents=True, exist_ok=True)
DOCS_DIR.mkdir(parents=True, exist_ok=True)

def run_player_evolution_engine():
    print("==========================================================================")
    print(" [PHASE 4] EXECUTING LONGITUDINAL PLAYER ENGINE & ROLE ANALYSIS           ")
    print("==========================================================================")

    db = DuckDBManager()

    # 1. Load Player-Game Data
    query = """
    SELECT
        bp.player_id,
        p.canonical_name,
        bp.team_id,
        t.canonical_name AS team_name,
        bp.game_id,
        g.game_date,
        g.season_id,
        g.venue,
        bp.jersey_number,
        bp.seconds_played,
        ROUND(bp.seconds_played / 60.0, 2) AS minutes,
        ROUND(bp.seconds_played / (40.0 * 60.0), 3) AS playing_time_share,
        bp.is_dnp,
        -- Scoring
        bp.points,
        bp.fgm,
        bp.fga,
        ROUND(bp.fgm * 100.0 / NULLIF(bp.fga, 0), 1) AS fg_pct,
        bp.fg2m,
        bp.fg2a,
        ROUND(bp.fg2m * 100.0 / NULLIF(bp.fg2a, 0), 1) AS fg2_pct,
        bp.fg3m,
        bp.fg3a,
        ROUND(bp.fg3m * 100.0 / NULLIF(bp.fg3a, 0), 1) AS fg3_pct,
        bp.ftm,
        bp.fta,
        ROUND(bp.ftm * 100.0 / NULLIF(bp.fta, 0), 1) AS ft_pct,
        -- Advanced Efficiency
        ROUND((bp.fgm + 0.5 * bp.fg3m) * 100.0 / NULLIF(bp.fga, 0), 1) AS efg_pct,
        ROUND(bp.points * 100.0 / NULLIF(2 * (bp.fga + 0.44 * bp.fta), 0), 1) AS ts_pct,
        -- Rebounds & Creation
        bp.orb,
        bp.drb,
        bp.trb,
        bp.ast,
        bp.tov,
        ROUND(bp.ast / NULLIF(bp.tov, 0), 2) AS ast_to_ratio,
        bp.stl,
        bp.blk,
        bp.pf,
        -- Rate Normalization (Per-40 minutes)
        ROUND(bp.points * 40.0 / NULLIF(bp.seconds_played / 60.0, 0), 1) AS pts_per_40,
        ROUND(bp.trb * 40.0 / NULLIF(bp.seconds_played / 60.0, 0), 1) AS reb_per_40,
        ROUND(bp.ast * 40.0 / NULLIF(bp.seconds_played / 60.0, 0), 1) AS ast_per_40,
        -- Match Context
        CASE WHEN g.home_team_id = bp.team_id THEN TRUE ELSE FALSE END AS is_home,
        CASE WHEN g.home_team_id = bp.team_id THEN g.away_team_id ELSE g.home_team_id END AS opponent_id,
        CASE WHEN g.home_team_id = bp.team_id THEN ta.canonical_name ELSE th.canonical_name END AS opponent_name,
        CASE WHEN g.home_team_id = bp.team_id THEN g.home_score ELSE g.away_score END AS team_score,
        CASE WHEN g.home_team_id = bp.team_id THEN g.away_score ELSE g.home_score END AS opp_score,
        CASE WHEN (CASE WHEN g.home_team_id = bp.team_id THEN g.home_score ELSE g.away_score END) >
                  (CASE WHEN g.home_team_id = bp.team_id THEN g.away_score ELSE g.home_score END) THEN 'WIN'
             ELSE 'LOSS' END AS outcome,
        (CASE WHEN g.home_team_id = bp.team_id THEN g.home_score ELSE g.away_score END) -
        (CASE WHEN g.home_team_id = bp.team_id THEN g.away_score ELSE g.home_score END) AS score_margin
    FROM boxscore_player bp
    JOIN player p ON bp.player_id = p.player_id
    JOIN team t ON bp.team_id = t.team_id
    JOIN game g ON bp.game_id = g.game_id
    JOIN team th ON g.home_team_id = th.team_id
    JOIN team ta ON g.away_team_id = ta.team_id
    ORDER BY bp.player_id, g.game_date ASC
    """
    df_pga = db.query_df(query)

    # Starter status join
    df_starters = db.query_df("SELECT DISTINCT game_id, team_id, player_ids FROM lineup_stint WHERE period = 1")
    starter_set = set()
    for _, s_row in df_starters.iterrows():
        gid = s_row["game_id"]
        p_ids_str = s_row["player_ids"]
        try:
            p_list = json.loads(p_ids_str) if isinstance(p_ids_str, str) else p_ids_str
            if isinstance(p_list, list):
                for pid in p_list:
                    starter_set.add((pid, gid))
        except Exception:
            pass

    df_pga["is_starter"] = df_pga.apply(lambda r: (r["player_id"], r["game_id"]) in starter_set, axis=1)

    p_pga = DERIVED_DIR / "player_game_analysis.parquet"
    df_pga.to_parquet(p_pga, index=False)
    print(f"Exported '{p_pga.name}': {len(df_pga)} player-game analysis records.")

    # 2. Rolling Performance Windows (3-game, 4-game, and 5-game windows)
    rolling_records = []
    for (pid, sid), p_group in df_pga[df_pga["is_dnp"] == False].groupby(["player_id", "season_id"]):
        p_group = p_group.sort_values("game_date").reset_index(drop=True)
        baseline_ppg = round(p_group["points"].mean(), 2)
        baseline_ts = round(p_group["ts_pct"].mean(), 2)
        baseline_min = round(p_group["minutes"].mean(), 2)

        for i, row in p_group.iterrows():
            w3 = p_group.iloc[max(0, i-2):i+1]
            w4 = p_group.iloc[max(0, i-3):i+1]
            w5 = p_group.iloc[max(0, i-4):i+1]

            r3_ppg = round(w3["points"].mean(), 1)
            r3_ts = round(w3["ts_pct"].mean(), 1)
            r4_ppg = round(w4["points"].mean(), 1)
            r4_ts = round(w4["ts_pct"].mean(), 1)
            r5_ppg = round(w5["points"].mean(), 1)
            r5_ts = round(w5["ts_pct"].mean(), 1)
            r5_min = round(w5["minutes"].mean(), 1)

            # Role Change Detection (Observed vs Interpreted)
            observed_role_change = "NO_CHANGE"
            interpreted_role_change = "STABLE_ROLE"
            
            if i >= 3:
                prev_w = p_group.iloc[max(0, i-6):max(0, i-3)]
                if len(prev_w) >= 3:
                    prev_min = prev_w["minutes"].mean()
                    prev_starters = prev_w["is_starter"].sum()
                    curr_starters = w4["is_starter"].sum()

                    if (r4_ppg > prev_w["points"].mean() + 4.0) and (w4["minutes"].mean() > prev_min + 5.0):
                        observed_role_change = f"MINUTES_INCREASE (+{round(w4['minutes'].mean() - prev_min, 1)}m)"
                        interpreted_role_change = "EXPANDED_OFFENSIVE_USAGE"
                    elif (w4["minutes"].mean() < prev_min - 5.0):
                        observed_role_change = f"MINUTES_DECREASE ({round(w4['minutes'].mean() - prev_min, 1)}m)"
                        interpreted_role_change = "REDUCED_ROTATION_SHARE"
                    elif curr_starters >= 3 and prev_starters <= 1:
                        observed_role_change = "PROMOTED_TO_STARTING_FIVE"
                        interpreted_role_change = "STARTING_ROLE_ACQUISITION"

            # Trend Classification
            if len(w4) < 4:
                trend_cat = "INSUFFICIENT_EVIDENCE"
            elif r4_ppg > baseline_ppg + 3.0 and r4_ts >= baseline_ts:
                trend_cat = "POSITIVE_TREND"
            elif r4_ppg < baseline_ppg - 3.0:
                trend_cat = "NEGATIVE_TREND"
            elif abs(r4_ppg - baseline_ppg) <= 1.5:
                trend_cat = "STABLE"
            else:
                trend_cat = "OBSERVED_CHANGE"

            sample_flag = "STABLE_SAMPLE" if len(w5) >= 5 else ("INTERMEDIATE_SAMPLE" if len(w3) >= 3 else "SHORT_SAMPLE")

            rolling_records.append({
                "player_id": pid,
                "canonical_name": row["canonical_name"],
                "team_id": row["team_id"],
                "season_id": sid,
                "game_id": row["game_id"],
                "game_date": str(row["game_date"]),
                "game_index_in_season": i + 1,
                "game_points": row["points"],
                "game_ts_pct": row["ts_pct"],
                "game_minutes": row["minutes"],
                "is_starter": row["is_starter"],
                "rolling_3_ppg": r3_ppg,
                "rolling_3_ts_pct": r3_ts,
                "rolling_4_ppg": r4_ppg,
                "rolling_4_ts_pct": r4_ts,
                "rolling_5_ppg": r5_ppg,
                "rolling_5_ts_pct": r5_ts,
                "season_baseline_ppg": baseline_ppg,
                "season_baseline_ts_pct": baseline_ts,
                "season_baseline_minutes": baseline_min,
                "delta_rolling_4_vs_baseline_ppg": round(r4_ppg - baseline_ppg, 2),
                "trend_classification": trend_cat,
                "observed_role_change": observed_role_change,
                "interpreted_role_change": interpreted_role_change,
                "sample_size_flag": sample_flag,
            })

    df_pra = pd.DataFrame(rolling_records)
    p_pra = DERIVED_DIR / "player_rolling_analysis.parquet"
    df_pra.to_parquet(p_pra, index=False)
    print(f"Exported '{p_pra.name}': {len(df_pra)} player rolling analysis records.")

    # 3. Weekly Player Aggregations
    df_pga["game_date_dt"] = pd.to_datetime(df_pga["game_date"])
    df_pga["calendar_year"] = df_pga["game_date_dt"].dt.isocalendar().year
    df_pga["week_number"] = df_pga["game_date_dt"].dt.isocalendar().week

    weekly_records = []
    for (pid, sid, yr, wk), w_group in df_pga[df_pga["is_dnp"] == False].groupby(["player_id", "season_id", "calendar_year", "week_number"]):
        p_name = w_group["canonical_name"].iloc[0]
        tid = w_group["team_id"].iloc[0]
        wk_start = w_group["game_date"].min()
        gp = len(w_group)
        tot_min = round(w_group["minutes"].sum(), 1)
        mpg = round(w_group["minutes"].mean(), 1)
        ppg = round(w_group["points"].mean(), 1)
        rpg = round(w_group["trb"].mean(), 1)
        apg = round(w_group["ast"].mean(), 1)
        topg = round(w_group["tov"].mean(), 1)
        spg = round(w_group["stl"].mean(), 1)
        bpg = round(w_group["blk"].mean(), 1)

        tot_fgm = w_group["fgm"].sum()
        tot_fga = w_group["fga"].sum()
        fg_pct = round(tot_fgm * 100.0 / max(1, tot_fga), 1) if tot_fga > 0 else None

        tot_fg3m = w_group["fg3m"].sum()
        tot_fg3a = w_group["fg3a"].sum()
        fg3_pct = round(tot_fg3m * 100.0 / max(1, tot_fg3a), 1) if tot_fg3a > 0 else None

        tot_pts = w_group["points"].sum()
        tot_fta = w_group["fta"].sum()
        ts_denom = 2 * (tot_fga + 0.44 * tot_fta)
        ts_pct = round(tot_pts * 100.0 / ts_denom, 1) if ts_denom > 0 else None

        starter_rate = round(w_group["is_starter"].sum() * 100.0 / gp, 1)

        weekly_records.append({
            "player_id": pid,
            "canonical_name": p_name,
            "team_id": tid,
            "season_id": sid,
            "calendar_year": int(yr),
            "week_number": int(wk),
            "week_start_date": str(wk_start),
            "games_played": gp,
            "total_minutes": tot_min,
            "mpg": mpg,
            "ppg": ppg,
            "rpg": rpg,
            "apg": apg,
            "topg": topg,
            "spg": spg,
            "bpg": bpg,
            "fg_pct": fg_pct,
            "fg3_pct": fg3_pct,
            "ts_pct": ts_pct,
            "starter_rate_pct": starter_rate,
        })

    df_pwa = pd.DataFrame(weekly_records).sort_values(["player_id", "season_id", "calendar_year", "week_number"]).reset_index(drop=True)
    df_pwa["prev_week_ppg"] = df_pwa.groupby(["player_id", "season_id"])["ppg"].shift(1)
    df_pwa["delta_ppg_prev_week"] = round(df_pwa["ppg"] - df_pwa["prev_week_ppg"], 2)

    p_pwa = DERIVED_DIR / "player_weekly_analysis.parquet"
    df_pwa.to_parquet(p_pwa, index=False)
    print(f"Exported '{p_pwa.name}': {len(df_pwa)} weekly player performance analysis records.")

    return df_pga, df_pra, df_pwa

if __name__ == "__main__":
    run_player_evolution_engine()
