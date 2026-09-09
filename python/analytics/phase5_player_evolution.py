"""Phase 5 Player Intelligence & Longitudinal Evolution Engine."""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

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

def compute_trend_slope(y: List[float]) -> float:
    """Computes linear regression trend slope for chronological sequence."""
    n = len(y)
    if n < 2:
        return 0.0
    x = np.arange(n)
    y_arr = np.array(y, dtype=float)
    x_mean = np.mean(x)
    y_mean = np.mean(y_arr)
    denom = np.sum((x - x_mean) ** 2)
    if denom == 0:
        return 0.0
    slope = np.sum((x - x_mean) * (y_arr - y_mean)) / denom
    return round(float(slope), 3)

def classify_player_trend(points_history: List[float], ts_history: List[float], baseline_ppg: float) -> Tuple[str, float, str]:
    """Applies rule-based mathematical trend classification."""
    n = len(points_history)
    if n < 4:
        return "INSUFFICIENT_DATA", 0.0, f"Sample size N={n} < 4 required threshold"
    
    slope = compute_trend_slope(points_history)
    recent_4 = points_history[-4:]
    recent_avg = float(np.mean(recent_4))
    recent_std = float(np.std(recent_4))
    diff_vs_baseline = round(recent_avg - baseline_ppg, 2)
    volatility_ratio = recent_std / max(1.0, recent_avg)

    if volatility_ratio > 0.50 and abs(diff_vs_baseline) < 3.0:
        return "VOLATILE", slope, f"High variance (std={round(recent_std, 1)}, ratio={round(volatility_ratio, 2)})"
    elif slope > 0.5 and diff_vs_baseline >= 2.0:
        return "IMPROVING", slope, f"Positive scoring slope (+{slope}/game, diff={diff_vs_baseline:+0.1f} PPG)"
    elif slope < -0.5 and diff_vs_baseline <= -2.0:
        return "DECLINING", slope, f"Negative scoring slope ({slope}/game, diff={diff_vs_baseline:+0.1f} PPG)"
    elif abs(diff_vs_baseline) <= 1.5 and abs(slope) <= 0.5:
        return "STABLE", slope, f"Consistent production (diff={diff_vs_baseline:+0.1f} PPG, slope={slope:+0.2f})"
    else:
        return "VOLATILE", slope, f"Mixed performance trajectory (diff={diff_vs_baseline:+0.1f} PPG)"

def build_player_intelligence_and_evolution():
    print("==========================================================================")
    print(" [PHASE 5] BUILDING PLAYER INTELLIGENCE & EVOLUTION LAYER                ")
    print("==========================================================================")

    db = DuckDBManager()

    # 1. Load Player Game Data
    query = """
    SELECT
        bp.player_id,
        p.canonical_name,
        bp.team_id,
        t.canonical_name AS team_name,
        bp.game_id,
        g.game_date,
        g.season_id,
        bp.jersey_number,
        bp.seconds_played,
        ROUND(bp.seconds_played / 60.0, 2) AS minutes,
        ROUND(bp.seconds_played / (40.0 * 60.0), 3) AS playing_time_share,
        bp.is_dnp,
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
        ROUND((bp.fgm + 0.5 * bp.fg3m) * 100.0 / NULLIF(bp.fga, 0), 1) AS efg_pct,
        ROUND(bp.points * 100.0 / NULLIF(2 * (bp.fga + 0.44 * bp.fta), 0), 1) AS ts_pct,
        bp.orb,
        bp.drb,
        bp.trb,
        bp.ast,
        bp.tov,
        ROUND(bp.ast / NULLIF(bp.tov, 0), 2) AS ast_to_ratio,
        bp.stl,
        bp.blk,
        bp.pf,
        ROUND(bp.points * 40.0 / NULLIF(bp.seconds_played / 60.0, 0), 1) AS pts_per_40,
        ROUND(bp.trb * 40.0 / NULLIF(bp.seconds_played / 60.0, 0), 1) AS reb_per_40,
        ROUND(bp.ast * 40.0 / NULLIF(bp.seconds_played / 60.0, 0), 1) AS ast_per_40,
        CASE WHEN g.home_team_id = bp.team_id THEN TRUE ELSE FALSE END AS is_home,
        CASE WHEN g.home_team_id = bp.team_id THEN ta.canonical_name ELSE th.canonical_name END AS opponent_name,
        CASE WHEN g.home_team_id = bp.team_id THEN g.home_score ELSE g.away_score END AS team_score,
        CASE WHEN g.home_team_id = bp.team_id THEN g.away_score ELSE g.home_score END AS opp_score,
        CASE WHEN (CASE WHEN g.home_team_id = bp.team_id THEN g.home_score ELSE g.away_score END) >
                  (CASE WHEN g.home_team_id = bp.team_id THEN g.away_score ELSE g.home_score END) THEN 'WIN'
             ELSE 'LOSS' END AS outcome
    FROM boxscore_player bp
    JOIN player p ON bp.player_id = p.player_id
    JOIN team t ON bp.team_id = t.team_id
    JOIN game g ON bp.game_id = g.game_id
    JOIN team th ON g.home_team_id = th.team_id
    JOIN team ta ON g.away_team_id = ta.team_id
    ORDER BY bp.player_id, g.game_date ASC
    """
    df_raw = db.query_df(query)

    # Starters Join
    df_starters = db.query_df("SELECT DISTINCT game_id, team_id, player_ids FROM lineup_stint WHERE period = 1")
    starter_set = set()
    for _, s_row in df_starters.iterrows():
        gid = s_row["game_id"]
        p_ids_str = s_row["player_ids"]
        try:
            p_list = json.loads(p_ids_str) if isinstance(p_ids_str, str) else p_ids_str
            if isinstance(p_list, list):
                for pid in p_list: starter_set.add((pid, gid))
        except Exception:
            pass

    df_raw["is_starter"] = df_raw.apply(lambda r: (r["player_id"], r["game_id"]) in starter_set, axis=1)

    # 2. Build Player Intelligence (Season Aggregations)
    pi_records = []
    for (pid, sid), p_group in df_raw[df_raw["is_dnp"] == False].groupby(["player_id", "season_id"]):
        p_name = p_group["canonical_name"].iloc[0]
        t_id = p_group["team_id"].iloc[0]
        t_name = p_group["team_name"].iloc[0]
        gp = len(p_group)
        tot_pts = int(p_group["points"].sum())
        tot_fga = int(p_group["fga"].sum())
        tot_fta = int(p_group["fta"].sum())
        tot_fgm = int(p_group["fgm"].sum())
        tot_fg3m = int(p_group["fg3m"].sum())
        tot_fg3a = int(p_group["fg3a"].sum())
        tot_reb = int(p_group["trb"].sum())
        tot_ast = int(p_group["ast"].sum())
        tot_tov = int(p_group["tov"].sum())
        tot_sec = float(p_group["seconds_played"].sum())

        mpg = round(tot_sec / (60.0 * gp), 1)
        ppg = round(tot_pts / gp, 1)
        rpg = round(tot_reb / gp, 1)
        apg = round(tot_ast / gp, 1)
        topg = round(tot_tov / gp, 1)
        
        pts_per_40 = round(tot_pts * 40.0 / max(1.0, tot_sec / 60.0), 1)
        reb_per_40 = round(tot_reb * 40.0 / max(1.0, tot_sec / 60.0), 1)
        ast_per_40 = round(tot_ast * 40.0 / max(1.0, tot_sec / 60.0), 1)

        ts_denom = 2 * (tot_fga + 0.44 * tot_fta)
        ts_pct = round(tot_pts * 100.0 / ts_denom, 1) if ts_denom > 0 else None
        fg_pct = round(tot_fgm * 100.0 / max(1, tot_fga), 1) if tot_fga > 0 else None
        fg3_pct = round(tot_fg3m * 100.0 / max(1, tot_fg3a), 1) if tot_fg3a > 0 else None

        starter_count = p_group["is_starter"].sum()
        starter_rate = round(starter_count * 100.0 / gp, 1)
        primary_role = "STARTER" if starter_rate >= 50.0 else "ROTATION"

        # Trend Classification
        pts_hist = p_group["points"].tolist()
        ts_hist = [x for x in p_group["ts_pct"] if pd.notna(x)]
        trend_class, trend_slope, trend_reason = classify_player_trend(pts_hist, ts_hist, ppg)

        pi_records.append({
            "player_id": pid,
            "canonical_name": p_name,
            "team_id": t_id,
            "team_name": t_name,
            "season_id": sid,
            "games_played": gp,
            "starter_games": int(starter_count),
            "starter_rate_pct": starter_rate,
            "primary_role": primary_role,
            "mpg": mpg,
            "ppg": ppg,
            "rpg": rpg,
            "apg": apg,
            "topg": topg,
            "pts_per_40": pts_per_40,
            "reb_per_40": reb_per_40,
            "ast_per_40": ast_per_40,
            "fg_pct": fg_pct,
            "fg3_pct": fg3_pct,
            "ts_pct": ts_pct,
            "trend_classification": trend_class,
            "trend_slope": trend_slope,
            "trend_reason": trend_reason,
            "uncertainty_status": "HIGH" if gp < 4 else ("MEDIUM" if gp < 8 else "LOW"),
        })

    df_pi = pd.DataFrame(pi_records)
    p_pi = DERIVED_DIR / "player_intelligence.parquet"
    df_pi.to_parquet(p_pi, index=False)
    print(f"Exported '{p_pi.name}': {len(df_pi)} player intelligence season profiles.")

    # 3. Build Player Longitudinal Evolution & Rolling/Weekly Timeline
    evolution_records = []
    for (pid, sid), p_group in df_raw[df_raw["is_dnp"] == False].groupby(["player_id", "season_id"]):
        p_group = p_group.sort_values("game_date").reset_index(drop=True)
        baseline_ppg = round(p_group["points"].mean(), 2)
        baseline_ts = round(p_group["ts_pct"].mean(), 2)

        pts_cum = []
        ts_cum = []

        for i, row in p_group.iterrows():
            pts_cum.append(row["points"])
            if pd.notna(row["ts_pct"]): ts_cum.append(row["ts_pct"])

            # Season Phase Assignment
            if i < 6: phase = "EARLY_SEASON"
            elif i < 16: phase = "MID_SEASON"
            else: phase = "LATE_SEASON_PLAYOFFS"

            # Rolling Windows
            w3 = p_group.iloc[max(0, i-2):i+1]
            w4 = p_group.iloc[max(0, i-3):i+1]
            w5 = p_group.iloc[max(0, i-4):i+1]

            r3_ppg = round(w3["points"].mean(), 1)
            r4_ppg = round(w4["points"].mean(), 1)
            r5_ppg = round(w5["points"].mean(), 1)
            r4_ts = round(w4["ts_pct"].mean(), 1)

            # Game to Game Delta
            prev_pts = p_group.iloc[i-1]["points"] if i > 0 else row["points"]
            prev_ts = p_group.iloc[i-1]["ts_pct"] if i > 0 else row["ts_pct"]
            prev_min = p_group.iloc[i-1]["minutes"] if i > 0 else row["minutes"]

            delta_pts_game = row["points"] - prev_pts
            delta_ts_game = round(row["ts_pct"] - prev_ts, 1) if (pd.notna(row["ts_pct"]) and pd.notna(prev_ts)) else 0.0
            delta_min_game = round(row["minutes"] - prev_min, 1)

            # Trajectory Classification
            trend_class, trend_slope, trend_reason = classify_player_trend(pts_cum, ts_cum, baseline_ppg)

            evolution_records.append({
                "player_id": pid,
                "canonical_name": row["canonical_name"],
                "team_id": row["team_id"],
                "season_id": sid,
                "game_id": row["game_id"],
                "game_date": str(row["game_date"]),
                "game_number": i + 1,
                "season_phase": phase,
                "opponent_name": row["opponent_name"],
                "is_home": row["is_home"],
                "outcome": row["outcome"],
                "is_starter": row["is_starter"],
                "minutes": row["minutes"],
                "points": row["points"],
                "fgm": row["fgm"],
                "fga": row["fga"],
                "fg_pct": row["fg_pct"],
                "fg3m": row["fg3m"],
                "fg3a": row["fg3a"],
                "fg3_pct": row["fg3_pct"],
                "ftm": row["ftm"],
                "fta": row["fta"],
                "ft_pct": row["ft_pct"],
                "ts_pct": row["ts_pct"],
                "efg_pct": row["efg_pct"],
                "trb": row["trb"],
                "ast": row["ast"],
                "tov": row["tov"],
                "stl": row["stl"],
                "blk": row["blk"],
                "pts_per_40": row["pts_per_40"],
                "reb_per_40": row["reb_per_40"],
                "ast_per_40": row["ast_per_40"],
                # Deltas
                "delta_pts_vs_prev_game": delta_pts_game,
                "delta_ts_vs_prev_game": delta_ts_game,
                "delta_min_vs_prev_game": delta_min_game,
                # Rolling Windows
                "rolling_3_ppg": r3_ppg,
                "rolling_4_ppg": r4_ppg,
                "rolling_5_ppg": r5_ppg,
                "rolling_4_ts": r4_ts,
                "season_baseline_ppg": baseline_ppg,
                "delta_rolling_4_vs_baseline_ppg": round(r4_ppg - baseline_ppg, 2),
                "trend_classification": trend_class,
                "trend_slope": trend_slope,
                "sample_size_flag": "STABLE_SAMPLE" if (i+1) >= 5 else ("INTERMEDIATE_SAMPLE" if (i+1) >= 3 else "SHORT_SAMPLE"),
            })

    df_pe = pd.DataFrame(evolution_records)
    p_pe = DERIVED_DIR / "player_evolution.parquet"
    df_pe.to_parquet(p_pe, index=False)
    print(f"Exported '{p_pe.name}': {len(df_pe)} player evolution trajectory records.")

    # Generate player trend methodology doc
    generate_player_trend_methodology_doc()

    return df_pi, df_pe

def generate_player_trend_methodology_doc():
    lines = [
        "# Player Trend Classification Methodology",
        "",
        "## 1. Mathematical Classification Framework",
        "",
        "To prevent interpreting random game-to-game noise as genuine player development, player trajectories are categorized strictly using deterministic thresholds:",
        "",
        "```text",
        "┌──────────────────────┬─────────────────────────────────────────────────────────────┐",
        "│ CLASSIFICATION       │ MATHEMATICAL RULE / THRESHOLD                               │",
        "├──────────────────────┼─────────────────────────────────────────────────────────────┤",
        "│ IMPROVING            │ N >= 4, Trend Slope beta > +0.50 PTS/game & diff >= +2.0 PPG│",
        "│ DECLINING            │ N >= 4, Trend Slope beta < -0.50 PTS/game & diff <= -2.0 PPG│",
        "│ STABLE               │ N >= 4, |beta| <= 0.50 & |Recent - Baseline| <= 1.5 PPG     │",
        "│ VOLATILE             │ N >= 4, StdDev / Mean > 0.50 or fluctuating trajectory      │",
        "│ INSUFFICIENT_DATA    │ N < 4 games played                                          │",
        "└──────────────────────┴─────────────────────────────────────────────────────────────┘",
        "```",
        "",
        "## 2. Longitudinal Season Phases",
        "",
        "- **`EARLY_SEASON`**: Games 1 to 6 (Vorrunde group stage).",
        "- **`MID_SEASON`**: Games 7 to 16 (Hauptrunde main round).",
        "- **`LATE_SEASON_PLAYOFFS`**: Games 17+ (National playoff elimination brackets).",
    ]
    (DOCS_DIR / "player_trend_methodology.md").write_text("\n".join(lines), encoding="utf-8")
    print("Generated docs/player_trend_methodology.md")

if __name__ == "__main__":
    build_player_intelligence_and_evolution()
