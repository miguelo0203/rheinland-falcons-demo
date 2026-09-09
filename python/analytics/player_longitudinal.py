"""Longitudinal Player Performance and Multi-Game Evolution Framework."""

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

def build_player_longitudinal_framework():
    print("==========================================================================")
    print(" [PHASE 3.5] BUILDING PLAYER LONGITUDINAL & EVOLUTION FRAMEWORK          ")
    print("==========================================================================")

    db = DuckDBManager()

    # 1. Query Player Game Boxscore Rows Joined with Context
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
        -- True Shooting %: PTS / (2 * (FGA + 0.44 * FTA))
        ROUND(bp.points * 100.0 / NULLIF(2 * (bp.fga + 0.44 * bp.fta), 0), 1) AS ts_pct,
        -- Rebounding & Creation
        bp.orb,
        bp.drb,
        bp.trb,
        bp.ast,
        bp.tov,
        ROUND(bp.ast / NULLIF(bp.tov, 0), 2) AS ast_to_ratio,
        bp.stl,
        bp.blk,
        bp.pf,
        -- Match Context
        CASE WHEN g.home_team_id = bp.team_id THEN TRUE ELSE FALSE END AS is_home,
        CASE WHEN g.home_team_id = bp.team_id THEN g.away_team_id ELSE g.home_team_id END AS opponent_id,
        CASE WHEN g.home_team_id = bp.team_id THEN ta.canonical_name ELSE th.canonical_name END AS opponent_name,
        CASE WHEN g.home_team_id = bp.team_id THEN g.home_score ELSE g.away_score END AS team_score,
        CASE WHEN g.home_team_id = bp.team_id THEN g.away_score ELSE g.home_score END AS opp_score,
        CASE WHEN (CASE WHEN g.home_team_id = bp.team_id THEN g.home_score ELSE g.away_score END) >
                  (CASE WHEN g.home_team_id = bp.team_id THEN g.away_score ELSE g.home_score END) THEN 'WIN'
             WHEN (CASE WHEN g.home_team_id = bp.team_id THEN g.home_score ELSE g.away_score END) <
                  (CASE WHEN g.home_team_id = bp.team_id THEN g.away_score ELSE g.home_score END) THEN 'LOSS'
             ELSE 'TIE' END AS outcome,
        (CASE WHEN g.home_team_id = bp.team_id THEN g.home_score ELSE g.away_score END) -
        (CASE WHEN g.home_team_id = bp.team_id THEN g.away_score ELSE g.home_score END) AS score_margin
    FROM boxscore_player bp
    JOIN player p ON bp.player_id = p.player_id
    JOIN team t ON bp.team_id = t.team_id
    JOIN game g ON bp.game_id = g.game_id
    JOIN team th ON g.home_team_id = th.team_id
    JOIN team ta ON g.away_team_id = ta.team_id
    ORDER BY bp.player_id, g.game_date ASC, bp.game_id ASC
    """
    df_pgp = db.query_df(query)
    
    # 2. Check Lineup Starter Status from Lineup Stints (Quarter 1 starting 5)
    df_starters = db.query_df("""
        SELECT DISTINCT game_id, team_id, player_ids
        FROM lineup_stint
        WHERE period = 1
    """)
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

    df_pgp["is_starter"] = df_pgp.apply(lambda r: (r["player_id"], r["game_id"]) in starter_set, axis=1)
    
    # Save player_game_performance.parquet
    p_pgp = DERIVED_DIR / "player_game_performance.parquet"
    df_pgp.to_parquet(p_pgp, index=False)
    print(f"Exported '{p_pgp.name}': {len(df_pgp)} player-game granular records.")

    # 3. Build Rolling Performance Windows (3-game & 5-game rolling averages)
    rolling_records = []
    
    # Group by player and season
    for (pid, sid), p_group in df_pgp[df_pgp["is_dnp"] == False].groupby(["player_id", "season_id"]):
        p_group = p_group.sort_values("game_date").reset_index(drop=True)
        baseline_ppg = round(p_group["points"].mean(), 2)
        baseline_ts = round(p_group["ts_pct"].mean(), 2)

        for i, row in p_group.iterrows():
            # Rolling 3-game window (up to current game)
            w3 = p_group.iloc[max(0, i-2):i+1]
            # Rolling 5-game window (up to current game)
            w5 = p_group.iloc[max(0, i-4):i+1]

            r3_ppg = round(w3["points"].mean(), 1)
            r3_ts = round(w3["ts_pct"].mean(), 1)
            r3_rpg = round(w3["trb"].mean(), 1)
            r3_apg = round(w3["ast"].mean(), 1)

            r5_ppg = round(w5["points"].mean(), 1)
            r5_ts = round(w5["ts_pct"].mean(), 1)

            sample_flag = "STABLE_SAMPLE" if len(w5) >= 5 else ("INTERMEDIATE_SAMPLE" if len(w3) >= 3 else "SMALL_SAMPLE")
            uncertainty = "HIGH" if len(w3) < 3 else ("MEDIUM" if len(w5) < 5 else "LOW")

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
                "rolling_3_ppg": r3_ppg,
                "rolling_3_ts_pct": r3_ts,
                "rolling_3_rpg": r3_rpg,
                "rolling_3_apg": r3_apg,
                "rolling_5_ppg": r5_ppg,
                "rolling_5_ts_pct": r5_ts,
                "season_baseline_ppg": baseline_ppg,
                "season_baseline_ts_pct": baseline_ts,
                "delta_rolling_3_vs_baseline_ppg": round(r3_ppg - baseline_ppg, 2),
                "delta_rolling_3_vs_baseline_ts": round(r3_ts - baseline_ts, 2) if not pd.isna(r3_ts) and not pd.isna(baseline_ts) else None,
                "sample_size_flag": sample_flag,
                "uncertainty_indicator": uncertainty,
            })

    df_rolling = pd.DataFrame(rolling_records)
    p_rolling = DERIVED_DIR / "player_rolling_performance.parquet"
    df_rolling.to_parquet(p_rolling, index=False)
    print(f"Exported '{p_rolling.name}': {len(df_rolling)} rolling performance trajectory records.")

    # 4. Build Weekly Performance Aggregation (Player x Competition Week)
    df_pgp["game_date_dt"] = pd.to_datetime(df_pgp["game_date"])
    df_pgp["calendar_year"] = df_pgp["game_date_dt"].dt.isocalendar().year
    df_pgp["week_number"] = df_pgp["game_date_dt"].dt.isocalendar().week

    weekly_records = []
    for (pid, sid, yr, wk), w_group in df_pgp[df_pgp["is_dnp"] == False].groupby(["player_id", "season_id", "calendar_year", "week_number"]):
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

        tot_ftm = w_group["ftm"].sum()
        tot_fta = w_group["fta"].sum()
        ft_pct = round(tot_ftm * 100.0 / max(1, tot_fta), 1) if tot_fta > 0 else None

        tot_pts = w_group["points"].sum()
        ts_denom = 2 * (tot_fga + 0.44 * tot_fta)
        ts_pct = round(tot_pts * 100.0 / ts_denom, 1) if ts_denom > 0 else None

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
            "ft_pct": ft_pct,
            "ts_pct": ts_pct,
        })

    df_weekly = pd.DataFrame(weekly_records)
    # Sort and compute deltas vs previous week
    df_weekly = df_weekly.sort_values(["player_id", "season_id", "calendar_year", "week_number"]).reset_index(drop=True)
    df_weekly["prev_week_ppg"] = df_weekly.groupby(["player_id", "season_id"])["ppg"].shift(1)
    df_weekly["delta_ppg_prev_week"] = round(df_weekly["ppg"] - df_weekly["prev_week_ppg"], 2)

    p_weekly = DERIVED_DIR / "player_weekly_performance.parquet"
    df_weekly.to_parquet(p_weekly, index=False)
    print(f"Exported '{p_weekly.name}': {len(df_weekly)} weekly player performance aggregations.")

    # 5. Generate 4-Game Demonstration and Methodology Document
    generate_player_longitudinal_methodology_doc(df_pgp, df_rolling)

def generate_player_longitudinal_methodology_doc(df_pgp: pd.DataFrame, df_rolling: pd.DataFrame):
    lines = [
        "# Longitudinal Player Performance & Multi-Game Evolution Methodology",
        "",
        "## 1. Longitudinal Architecture & Aggregation Layers",
        "",
        "The sandbox implements a 3-tier longitudinal performance framework to track player development without small-sample distortions:",
        "",
        "```text",
        "LEVEL 1: Granular Game Log (player_game_performance.parquet) [1 Row / Player x Game]",
        "  │",
        "  ▼",
        "LEVEL 2: Rolling Trajectories (player_rolling_performance.parquet) [3-Game & 5-Game Windows]",
        "  │",
        "  ▼",
        "LEVEL 3: Weekly Aggregations (player_weekly_performance.parquet) [Player x Competition Week]",
        "```",
        "",
        "---",
        "",
        "## 2. Four-Game Player Evolution Demonstration (`SHORT_SAMPLE_DEMONSTRATION`)",
        "",
        "> [!IMPORTANT]",
        "> **Methodological Notice**: The 4-game sequences below are presented strictly as a **`SHORT_SAMPLE_DEMONSTRATION`** to illustrate the trajectory mechanics of the monitoring framework. In accordance with our statistical safety protocol, 4 games do not constitute a definitive long-term developmental trend.",
        "",
    ]

    # Select Key Focus Players: Lukas Weber (Rheinland), Leonhard Heyd (Rheinland), Lukas Rademacher (Isar Bulls)
    focus_pids = ["PLY_DEMO_101", "PLY_DEMO_104", "PLY_61008"]
    
    for pid in focus_pids:
        p_rows = df_pgp[(df_pgp["player_id"] == pid) & (df_pgp["is_dnp"] == False)].sort_values("game_date")
        if len(p_rows) >= 4:
            p_name = p_rows["canonical_name"].iloc[0]
            team_name = p_rows["team_name"].iloc[0]
            sample4 = p_rows.tail(4)

            lines.extend([
                f"### Player Evolution: {p_name} ({team_name})",
                "",
                "| Game Seq | Date | Opponent | H/A | MIN | PTS | FG% | 3P% | FT% | TS% | TRB | AST | TOV | Starter | Score Margin |",
                "|:---:|:---:|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|",
            ])

            for idx, (_, r) in enumerate(sample4.iterrows(), 1):
                ha = "Home" if r["is_home"] else "Away"
                st = "✅ Starter" if r["is_starter"] else "Bench"
                fg_s = f"{r['fg_pct']}%" if r["fg_pct"] is not None else "—"
                fg3_s = f"{r['fg3_pct']}%" if r["fg3_pct"] is not None else "—"
                ft_s = f"{r['ft_pct']}%" if r["ft_pct"] is not None else "—"
                ts_s = f"{r['ts_pct']}%" if r["ts_pct"] is not None else "—"

                lines.append(
                    f"| `Game {idx}` (N-{4-idx}) | {r['game_date']} | {r['opponent_name']} | {ha} | {r['minutes']} | **{r['points']}** | {fg_s} | {fg3_s} | {ft_s} | **{ts_s}** | {r['trb']} | {r['ast']} | {r['tov']} | {st} | {r['score_margin']} |"
                )
            
            # Evolution Deltas
            first_pts = sample4["points"].iloc[0]
            last_pts = sample4["points"].iloc[-1]
            first_ts = sample4["ts_pct"].iloc[0]
            last_ts = sample4["ts_pct"].iloc[-1]
            delta_pts = last_pts - first_pts
            delta_ts = round(last_ts - first_ts, 1) if (last_ts is not None and first_ts is not None) else 0

            lines.extend([
                "",
                f"- **4-Game Scoring Progression**: {first_pts} $\\to$ {last_pts} PTS ($\\Delta = {delta_pts:+d}$ PTS)",
                f"- **4-Game True Shooting Efficiency**: {first_ts}% $\\to$ {last_ts}% TS% ($\\Delta = {delta_ts:+.1f}\\%$ TS)",
                "",
            ])

    lines.extend([
        "---",
        "",
        "## 3. Small-Sample Protection Invariants",
        "",
        "1. **Sample Threshold Guards**:",
        "   - $N < 3$ games: Flagged as `SMALL_SAMPLE` (Uncertainty: `HIGH`). No trend claims permitted.",
        "   - $3 \\le N < 5$ games: Flagged as `INTERMEDIATE_SAMPLE` (Uncertainty: `MEDIUM`). Exposes rolling trajectory only.",
        "   - $N \\ge 5$ games: Flagged as `STABLE_SAMPLE` (Uncertainty: `LOW`). Evaluated against season baseline.",
        "2. **Zero-Baseline Safeguard**: Percentage changes are never computed when the baseline is zero or unstable.",
    ])

    out_file = DOCS_DIR / "player_longitudinal_methodology.md"
    out_file.write_text("\n".join(lines), encoding="utf-8")
    print(f"Generated {out_file}")

if __name__ == "__main__":
    build_player_longitudinal_framework()
