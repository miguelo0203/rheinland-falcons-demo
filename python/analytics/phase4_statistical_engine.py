"""Phase 4 Statistical Analysis & Four Factors Significance Engine."""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from scipy import stats

sys.path.insert(0, ".")

from python.database.duckdb_manager import DuckDBManager

DERIVED_DIR = Path("data/derived")
DOCS_DIR = Path("docs")
DERIVED_DIR.mkdir(parents=True, exist_ok=True)
DOCS_DIR.mkdir(parents=True, exist_ok=True)

def compute_bootstrap_ci(data_x: np.ndarray, data_y: np.ndarray, n_boot: int = 1000, ci: float = 0.95) -> Tuple[float, float]:
    """Calculates bootstrap confidence interval for Pearson correlation."""
    if len(data_x) < 10:
        return (np.nan, np.nan)
    boot_corrs = []
    n = len(data_x)
    rng = np.random.default_rng(42)
    for _ in range(n_boot):
        indices = rng.choice(n, size=n, replace=True)
        bx, by = data_x[indices], data_y[indices]
        if np.std(bx) > 0 and np.std(by) > 0:
            r = np.corrcoef(bx, by)[0, 1]
            if not np.isnan(r):
                boot_corrs.append(r)
    if not boot_corrs:
        return (np.nan, np.nan)
    alpha = (1.0 - ci) / 2.0
    return (float(np.percentile(boot_corrs, alpha * 100)), float(np.percentile(boot_corrs, (1.0 - alpha) * 100)))

def benjamini_hochberg_fdr(p_values: List[float], q: float = 0.05) -> List[bool]:
    """Applies Benjamini-Hochberg False Discovery Rate correction."""
    n = len(p_values)
    if n == 0:
        return []
    sorted_indices = np.argsort(p_values)
    sorted_p = np.array(p_values)[sorted_indices]
    
    thresholds = (np.arange(1, n + 1) / n) * q
    significant = sorted_p <= thresholds
    
    # Step-up procedure
    max_sig_idx = -1
    for i in range(n - 1, -1, -1):
        if significant[i]:
            max_sig_idx = i
            break
            
    is_sig_sorted = np.zeros(n, dtype=bool)
    if max_sig_idx >= 0:
        is_sig_sorted[:max_sig_idx + 1] = True
        
    # Reorder back
    orig_sig = np.zeros(n, dtype=bool)
    orig_sig[sorted_indices] = is_sig_sorted
    return orig_sig.tolist()

def run_statistical_engine():
    print("==========================================================================")
    print(" [PHASE 4] EXECUTING RIGOROUS STATISTICAL ENGINE & FOUR FACTORS ANALYSIS ")
    print("==========================================================================")

    db = DuckDBManager()

    # 1. Team-Game Granular Dataset (view_team_game_ratings)
    df_tga = db.query_df("""
        SELECT
            game_id,
            team_id,
            team_name,
            is_home,
            points,
            opp_points,
            point_diff,
            possessions,
            efg_pct,
            tov_pct,
            orb_pct,
            ftr,
            ortg,
            drtg,
            net_rtg,
            CASE WHEN points > opp_points THEN 'WIN' ELSE 'LOSS' END AS outcome
        FROM view_team_game_ratings
        WHERE possessions >= 40
    """)
    p_tga = DERIVED_DIR / "team_game_analysis.parquet"
    df_tga.to_parquet(p_tga, index=False)
    print(f"Exported '{p_tga.name}': {len(df_tga)} team-game analytical records.")

    # 2. Team-Season Aggregated Dataset
    df_tsa = db.query_df("""
        SELECT
            team_id,
            team_name,
            COUNT(*) AS games_played,
            SUM(CASE WHEN points > opp_points THEN 1 ELSE 0 END) AS wins,
            SUM(CASE WHEN points < opp_points THEN 1 ELSE 0 END) AS losses,
            ROUND(SUM(CASE WHEN points > opp_points THEN 1.0 ELSE 0.0 END) / COUNT(*), 3) AS win_pct,
            ROUND(AVG(points), 1) AS ppg,
            ROUND(AVG(opp_points), 1) AS opp_ppg,
            ROUND(AVG(point_diff), 1) AS avg_point_diff,
            ROUND(AVG(possessions), 1) AS pace,
            ROUND(AVG(ortg), 1) AS ortg,
            ROUND(AVG(drtg), 1) AS drtg,
            ROUND(AVG(net_rtg), 1) AS net_rtg,
            -- Weighted Four Factors from Sums
            ROUND((SUM(fgm) + 0.5 * SUM(fg3m)) * 100.0 / NULLIF(SUM(fga), 0), 1) AS weighted_efg_pct,
            ROUND(SUM(tov) * 100.0 / NULLIF(SUM(fga) + 0.44 * SUM(fta) + SUM(tov), 0), 1) AS weighted_tov_pct,
            ROUND(SUM(orb) * 100.0 / NULLIF(SUM(orb) + SUM(opp_drb), 0), 1) AS weighted_orb_pct,
            ROUND(SUM(fta) / NULLIF(SUM(fga), 0.0), 3) AS weighted_ftr
        FROM view_team_game_ratings
        GROUP BY team_id, team_name
        HAVING COUNT(*) >= 2
    """)
    p_tsa = DERIVED_DIR / "team_season_analysis.parquet"
    df_tsa.to_parquet(p_tsa, index=False)
    print(f"Exported '{p_tsa.name}': {len(df_tsa)} team-season analytical records.")

    # 3. Game-Level Four Factors Statistical Significance & FDR Correction
    factors = ["efg_pct", "tov_pct", "orb_pct", "ftr", "possessions"]
    analysis_records = []
    p_values_list = []

    y_net = df_tga["net_rtg"].values
    y_diff = df_tga["point_diff"].values
    n_sample = len(df_tga)

    for f in factors:
        x = df_tga[f].values
        
        # Pearson & Spearman
        r_pearson, p_pearson = stats.pearsonr(x, y_diff)
        r_spearman, p_spearman = stats.spearmanr(x, y_diff)
        
        # 95% Bootstrap Confidence Interval
        ci_lower, ci_upper = compute_bootstrap_ci(x, y_diff, n_boot=1000, ci=0.95)
        
        # Sensitivity: Outlier removal (trim top/bottom 5% point diffs)
        mask = (y_diff >= np.percentile(y_diff, 5)) & (y_diff <= np.percentile(y_diff, 95))
        r_trimmed, _ = stats.pearsonr(x[mask], y_diff[mask])
        
        is_sensitive = abs(r_pearson - r_trimmed) > 0.15
        
        # Effect size classification (Cohen's d approximation / R^2)
        r2 = round(float(r_pearson ** 2), 3)
        if abs(r_pearson) >= 0.70: imp = "VERY_HIGH"
        elif abs(r_pearson) >= 0.50: imp = "HIGH"
        elif abs(r_pearson) >= 0.30: imp = "MODERATE"
        else: imp = "LOW"

        p_values_list.append(p_pearson)

        analysis_records.append({
            "factor_name": f.upper(),
            "sample_size_N": n_sample,
            "pearson_r": round(float(r_pearson), 3),
            "p_value_raw": float(p_pearson),
            "spearman_rho": round(float(r_spearman), 3),
            "p_value_spearman": float(p_spearman),
            "r_squared": r2,
            "bootstrap_ci_95_lower": round(ci_lower, 3),
            "bootstrap_ci_95_upper": round(ci_upper, 3),
            "trimmed_outlier_r": round(float(r_trimmed), 3),
            "is_sensitive_to_outliers": is_sensitive,
            "empirical_importance": imp,
            "epistemic_classification": "ASSOCIATIONAL",
        })

    # Apply FDR correction
    fdr_sig = benjamini_hochberg_fdr(p_values_list, q=0.05)
    for idx, sig in enumerate(fdr_sig):
        analysis_records[idx]["fdr_significant_q05"] = sig

    df_lca = pd.DataFrame(analysis_records)
    p_lca = DERIVED_DIR / "league_context_analysis.parquet"
    df_lca.to_parquet(p_lca, index=False)
    print(f"Exported '{p_lca.name}': {len(df_lca)} statistical significance factor evaluations.")

    return df_tga, df_tsa, df_lca

if __name__ == "__main__":
    run_statistical_engine()
