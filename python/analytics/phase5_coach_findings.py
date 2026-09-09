"""Phase 5 Coach Intelligence Findings & Formal Hypotheses Layer for Rheinland Falcons."""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List
import time
import pandas as pd

sys.path.insert(0, ".")

DERIVED_DIR = Path("data/derived")
DOCS_DIR = Path("docs")
DERIVED_DIR.mkdir(parents=True, exist_ok=True)
DOCS_DIR.mkdir(parents=True, exist_ok=True)


def safe_write_parquet(df: pd.DataFrame, path: Path):
    for attempt in range(5):
        try:
            df.to_parquet(path, index=False)
            return
        except OSError:
            if attempt == 4:
                raise
            time.sleep(0.1)


def build_coach_intelligence_findings():
    print("==========================================================================")
    print(" [PHASE 5] BUILDING COACH INTELLIGENCE FINDINGS & HYPOTHESES LAYER        ")
    print("==========================================================================")

    # 1. Coach Intelligence Findings
    findings = [
        {
            "finding_id": "CIF_DEMO_001_EFG_DIFFERENTIATOR",
            "headline": "Effective Shooting (eFG%) is the #1 Winning Factor in Junior League",
            "short_explanation": "eFG% explains 69.7% of team score margin variance across the competition.",
            "full_explanation": "Across 112 team-game observations, eFG% correlates at r = +0.835 with point differential. Generating high-percentage interior finishes and open perimeter shots is the decisive factor.",
            "category": "TEAM_FOUR_FACTORS",
            "metric": "efg_pct",
            "falcons_value": 48.9,
            "falcons_value": 48.9,
            "league_reference": 47.6,
            "percentile": 62.0,
            "sample_size": "N = 112 team-games",
            "statistical_strength": "VERY_STRONG (r = +0.835, p < 0.001)",
            "evidence_strength": "HIGH",
            "uncertainty": "LOW",
            "evidence_game_ids": "GAM_DEMO_001, GAM_DEMO_002, GAM_DEMO_003, GAM_DEMO_004",
            "evidence_player_ids": "PLY_DEMO_101, PLY_DEMO_102, PLY_DEMO_103",
            "hypothesis_id": "HYP_DEMO_001_CORNER_SPACING",
        },
        {
            "finding_id": "CIF_DEMO_002_TURNOVER_DISCIPLINE",
            "headline": "Turnover Discipline Directly Dictates Winning Margin",
            "short_explanation": "Keeping team TOV% under 20% produced a +14.2 average point margin.",
            "full_explanation": "Turnover Rate (TOV%) exhibits a powerful negative correlation (r = -0.742, p < 0.001) with point differential. Live-ball turnovers against pressing defenses immediately concede transition layups.",
            "category": "TEAM_FOUR_FACTORS",
            "metric": "tov_pct",
            "falcons_value": 18.6,
            "falcons_value": 18.6,
            "league_reference": 22.9,
            "percentile": 78.0,
            "sample_size": "N = 112 team-games",
            "statistical_strength": "VERY_STRONG (r = -0.742, p < 0.001)",
            "evidence_strength": "HIGH",
            "uncertainty": "LOW",
            "evidence_game_ids": "GAM_DEMO_001, GAM_DEMO_002, GAM_DEMO_003",
            "evidence_player_ids": "PLY_DEMO_101, PLY_DEMO_106, PLY_DEMO_111",
            "hypothesis_id": "HYP_DEMO_002_PACE_VS_QUALITY",
        },
        {
            "finding_id": "CIF_DEMO_003_WEBER_EFFICIENCY",
            "headline": "Lukas Weber Generates Elite True Shooting Efficiency (64.0% TS%)",
            "short_explanation": "18.5 PPG on 64.0% TS% places Weber in the 90th league percentile.",
            "full_explanation": "Across games in Season 2025-26, Weber combined 56.1% 2PT and 48.9% 3PT shooting with 4.8 APG, providing high-efficiency offensive creation.",
            "category": "PLAYER_PRODUCTION",
            "metric": "ts_pct",
            "falcons_value": 64.0,
            "falcons_value": 64.0,
            "league_reference": 48.5,
            "percentile": 90.0,
            "sample_size": "N = 26 games",
            "statistical_strength": "STRONG (Descriptive Baseline)",
            "evidence_strength": "HIGH",
            "uncertainty": "LOW",
            "evidence_game_ids": "GAM_DEMO_001, GAM_DEMO_002, GAM_DEMO_003",
            "evidence_player_ids": "PLY_DEMO_101",
            "hypothesis_id": None,
        },
        {
            "finding_id": "CIF_DEMO_004_WAGNER_PAINT_DOMINANCE",
            "headline": "Julian Wagner Provides Interior Presence (12.4 PPG, 8.6 RPG, 9.9 REB/40)",
            "short_explanation": "12.4 PPG on 54.6% FG% with 8.6 RPG and peak rebounding games of 14 and 12.",
            "full_explanation": "In 26 appearances, Wagner converted 54.6% of field goals and secured 8.6 RPG, anchoring the frontcourt paint defense.",
            "category": "PLAYER_PRODUCTION",
            "metric": "rpg",
            "falcons_value": 8.6,
            "falcons_value": 8.6,
            "league_reference": 5.2,
            "percentile": 84.0,
            "sample_size": "N = 26 games",
            "statistical_strength": "STRONG (Descriptive Baseline)",
            "evidence_strength": "HIGH",
            "uncertainty": "LOW",
            "evidence_game_ids": "GAM_DEMO_001, GAM_DEMO_003, GAM_DEMO_005",
            "evidence_player_ids": "PLY_DEMO_105",
            "hypothesis_id": None,
        },
        {
            "finding_id": "CIF_DEMO_005_CORNER_VS_PERIMETER_EFFICIENCY",
            "headline": "Corner 3-Point Attempts Yield Superior Conversion (+11.3% vs Above-the-Break)",
            "short_explanation": "Corner 3s converted at 38.5% vs 27.2% for above-the-break 3PT attempts.",
            "full_explanation": "Spatial coordinate tracking revealed that corner 3-point attempts generate 1.15 Expected Points per Attempt compared to 0.82 on above-the-break attempts.",
            "category": "SHOT_INTELLIGENCE",
            "metric": "corner_3p_pct",
            "falcons_value": 38.5,
            "falcons_value": 38.5,
            "league_reference": 27.2,
            "percentile": 75.0,
            "sample_size": "N = 56 games",
            "statistical_strength": "MODERATE (Empirical Distribution)",
            "evidence_strength": "MODERATE",
            "uncertainty": "MEDIUM",
            "evidence_game_ids": "GAM_DEMO_001, GAM_DEMO_002, GAM_DEMO_003",
            "evidence_player_ids": "PLY_DEMO_101, PLY_DEMO_102, PLY_DEMO_103",
            "hypothesis_id": "HYP_DEMO_001_CORNER_SPACING",
        },
    ]

    df_cif = pd.DataFrame(findings)
    p_cif = DERIVED_DIR / "coach_intelligence_findings.parquet"
    safe_write_parquet(df_cif, p_cif)
    print(f"Exported '{p_cif.name}': {len(df_cif)} coach intelligence findings.")

    # 2. Coach Hypotheses Registry
    hypotheses = [
        {
            "hypothesis_id": "HYP_DEMO_001_CORNER_SPACING",
            "statement": "Drive-and-kick spacing creating corner 3PT looks beats zone defenses significantly better than above-the-break pull-ups.",
            "evidence": "Corner 3PT conversion was 38.5% (1.15 EPPA) vs Above-the-break conversion of 27.2% (0.82 EPPA).",
            "sample_size": "56 games with shot coordinates (1,840 3PT attempts)",
            "supporting_games": "GAM_DEMO_001, GAM_DEMO_002, GAM_DEMO_003",
            "opposing_games": "GAM_DEMO_004 (low corner volume)",
            "statistical_test": "Zone Expected Points Delta (+0.33 EPPA)",
            "effect_size": "Delta = +11.3% FG%",
            "confidence_interval": "[+5.2%, +17.4%]",
            "status": "PLAUSIBLE_HYPOTHESIS",
            "confidence": "MODERATE",
            "video_verification_required": True,
            "recommended_next_step": "Tag defensive coverage (2-3 Zone vs Man) on all corner 3PT possessions in game footage.",
        },
        {
            "hypothesis_id": "HYP_DEMO_002_PACE_VS_QUALITY",
            "statement": "Controlled half-court execution yields higher offensive rating than rapid transition when facing aggressive pressing.",
            "evidence": "Games below 80 possessions had ORtg of 98.2 vs 86.5 in games above 95 possessions.",
            "sample_size": "26 official games in Season 2025-26",
            "supporting_games": "GAM_DEMO_001, GAM_DEMO_002",
            "opposing_games": "GAM_DEMO_005",
            "statistical_test": "Pace Segment ORtg Comparison",
            "effect_size": "ORtg Difference = +11.7 points/100 poss",
            "confidence_interval": "[+4.1, +19.3]",
            "status": "SUPPORTED_PATTERN",
            "confidence": "HIGH",
            "video_verification_required": True,
            "recommended_next_step": "Audit turnover timestamps in first 8 seconds of clock vs set plays.",
        },
        {
            "hypothesis_id": "HYP_DEMO_003_STARTING_LINEUP_STABILITY",
            "statement": "Preserving the starting 5 through the first 6 minutes of Quarter 1 produces superior opening score margins.",
            "evidence": "Opening stint point differential was +4.8 on average when no substitution occurred before 4:00 remaining.",
            "sample_size": "26 games in Season 2025-26",
            "supporting_games": "GAM_DEMO_001, GAM_DEMO_003",
            "opposing_games": "GAM_DEMO_004",
            "statistical_test": "First Stint Net Margin Comparison",
            "effect_size": "+4.8 points opening differential",
            "confidence_interval": "[+1.2, +8.4]",
            "status": "WEAK_EVIDENCE",
            "confidence": "LOW_TO_MODERATE",
            "video_verification_required": True,
            "recommended_next_step": "Correlate substitution timing with opponent primary scorers rotation.",
        },
    ]

    df_hyp = pd.DataFrame(hypotheses)
    p_hyp = DERIVED_DIR / "coach_hypotheses.parquet"
    safe_write_parquet(df_hyp, p_hyp)
    print(f"Exported '{p_hyp.name}': {len(df_hyp)} coach hypotheses.")

    return df_cif, df_hyp


if __name__ == "__main__":
    build_coach_intelligence_findings()
