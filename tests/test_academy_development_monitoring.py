"""Comprehensive Test Suite for Academy Development Monitoring (Hub 6).

Validates:
1. Exact Deterministic Classification States (IMPROVING, STABLE, STAGNATING, DECLINING, INSUFFICIENT DATA)
2. Multi-Signal Confirmation & Rejection of Solitary Volatile Metrics
3. Possession-Volume Gating for On-Court Net Rating (>= 20 possessions required)
4. Minimum Sample Floor Enforcement (GP < 4 or min < 20 -> INSUFFICIENT DATA)
5. Conservative Stagnation Guardrails (>= 8 GP, >= 10 MPG, flat multi-window metrics)
6. Evidence Strength Tiering (STRONG, MODERATE, LIMITED, INSUFFICIENT)
7. Temporal Point-in-Time Integrity (as_of_date 0% Future Leakage)
8. Strict Category Isolation (U16 vs U19 vs All Academy)
9. Dual-Registered Player Segregation (No U16 stats leaked into U19)
10. Descriptive-Only All Academy Aggregation (No mixed normative percentiles)
11. Objective U16 -> U19 Screening Matrix (PASS / NOT MET / UNAVAILABLE, no composite scores)
12. High PPG Alone Rejection in Pipeline Screening
13. Dynamic Database Discovery (Zero hardcoded counts or benchmark values)
14. Missing-Data Honesty (None/Unavailable, never false zeros)
15. Performance SLA (< 1.0s warm load)
"""

import sys
import time
from pathlib import Path
from typing import Any, Dict, List
import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, ".")

from app.services.data_service import DataService
from python.analytics.academy_development_engine import (
    AcademyDevelopmentEngine,
    DevelopmentStatus,
    EvidenceStrength,
    ScreeningCriterionStatus,
    PlayerDevelopmentProfile,
    PipelineEvaluation,
    DevelopmentWindow,
    DevelopmentDeltas,
)


@pytest.fixture(scope="module")
def ds():
    service = DataService()
    yield service
    service.close()


# =============================================================================
# 1. DETERMINISTIC CLASSIFICATION & MULTI-SIGNAL EVALUATION
# =============================================================================

def test_01_classification_improving_multi_signal():
    """Verify IMPROVING requires multi-dimensional positive evidence (Path A or B)."""
    # 10 games chronologically:
    # Games 1-5 (Previous Window): Earlier dates (Oct 01-05), lower TS% and lower Net Rtg
    # Games 6-10 (Recent Window): Later dates (Oct 20-25), high TS% and high positive Net Rtg (Dual Tier 1)
    df_games = pd.DataFrame([
        {"game_id": f"G_{i}", "game_date": f"2025-10-{i:02d}", "minutes": 20.0, "seconds_played": 1200,
         "points": 10, "fga": 10, "fgm": 3, "fg2a": 6, "fg2m": 2, "fg3a": 4, "fg3m": 1, "fta": 2, "ftm": 1,
         "trb": 4, "ast": 2, "stl": 1, "blk": 0, "tov": 3, "stint_pts_for": 30, "stint_pts_against": 35, "stint_poss": 30.0}
        for i in range(1, 6)
    ] + [
        {"game_id": f"G_{i}", "game_date": f"2025-10-{20+i-6:02d}", "minutes": 25.0, "seconds_played": 1500,
         "points": 18, "fga": 10, "fgm": 6, "fg2a": 6, "fg2m": 4, "fg3a": 4, "fg3m": 2, "fta": 4, "ftm": 4,
         "trb": 6, "ast": 4, "stl": 2, "blk": 1, "tov": 2, "stint_pts_for": 45, "stint_pts_against": 30, "stint_poss": 30.0}
        for i in range(6, 11)
    ])

    prof = AcademyDevelopmentEngine.evaluate_player_development(
        df_player_games=df_games,
        player_id="PLY_TEST_1",
        canonical_name="Test Improving Player",
        team_id="TEM_DEMO_U16",
        squad="U16",
        season_id="SEA_2025"
    )

    assert prof.status == DevelopmentStatus.IMPROVING
    assert prof.evidence_strength in (EvidenceStrength.STRONG, EvidenceStrength.MODERATE)
    assert len(prof.primary_signals) > 0
    assert "True Shooting" in prof.primary_signals[0]


def test_02_solitary_signal_rejection_for_improving():
    """Verify that a solitary metric change (e.g. only minutes, or only low-volume rating) is rejected."""
    # Player whose minutes increase, but efficiency and scoring are flat/dropping
    df_games = pd.DataFrame([
        # First 5 games (lower minutes, higher efficiency)
        {"game_id": f"G_{i}", "game_date": f"2025-10-{i:02d}", "minutes": 15.0, "seconds_played": 900,
         "points": 10, "fga": 6, "fgm": 4, "fg2a": 4, "fg2m": 3, "fg3a": 2, "fg3m": 1, "fta": 2, "ftm": 2,
         "trb": 3, "ast": 2, "stl": 1, "blk": 0, "tov": 1, "stint_pts_for": 20, "stint_pts_against": 20, "stint_poss": 25.0}
        for i in range(1, 6)
    ] + [
        # Last 5 games (higher minutes, but depressed efficiency and negative rating)
        {"game_id": f"G_{i}", "game_date": f"2025-11-{i:02d}", "minutes": 25.0, "seconds_played": 1500,
         "points": 10, "fga": 10, "fgm": 3, "fg2a": 6, "fg2m": 2, "fg3a": 4, "fg3m": 1, "fta": 2, "ftm": 1,
         "trb": 4, "ast": 2, "stl": 1, "blk": 0, "tov": 3, "stint_pts_for": 25, "stint_pts_against": 35, "stint_poss": 25.0}
        for i in range(6, 11)
    ])

    prof = AcademyDevelopmentEngine.evaluate_player_development(
        df_player_games=df_games,
        player_id="PLY_TEST_2",
        canonical_name="Test Role Expansion Only",
        team_id="TEM_DEMO_U16",
        squad="U16",
        season_id="SEA_2025"
    )

    # Role increased (+10 MPG), but TS dropped by ~25 pp -> CANNOT be IMPROVING
    assert prof.status != DevelopmentStatus.IMPROVING


def test_03_classification_declining():
    """Verify DECLINING triggers on robust efficiency collapse and impact drop."""
    df_games = pd.DataFrame([
        # Previous 5 games: High efficiency and solid impact
        {"game_id": f"G_{i}", "game_date": f"2025-10-{i:02d}", "minutes": 24.0, "seconds_played": 1440,
         "points": 18, "fga": 12, "fgm": 8, "fg2a": 8, "fg2m": 6, "fg3a": 4, "fg3m": 2, "fta": 4, "ftm": 3,
         "trb": 5, "ast": 3, "stl": 2, "blk": 1, "tov": 2, "stint_pts_for": 40, "stint_pts_against": 30, "stint_poss": 30.0}
        for i in range(1, 6)
    ] + [
        # Recent 5 games: Severe efficiency drop and negative rating
        {"game_id": f"G_{i}", "game_date": f"2025-11-{i:02d}", "minutes": 20.0, "seconds_played": 1200,
         "points": 6, "fga": 10, "fgm": 2, "fg2a": 6, "fg2m": 1, "fg3a": 4, "fg3m": 1, "fta": 2, "ftm": 1,
         "trb": 3, "ast": 1, "stl": 0, "blk": 0, "tov": 4, "stint_pts_for": 20, "stint_pts_against": 40, "stint_poss": 30.0}
        for i in range(6, 11)
    ])

    prof = AcademyDevelopmentEngine.evaluate_player_development(
        df_player_games=df_games,
        player_id="PLY_TEST_3",
        canonical_name="Test Declining Player",
        team_id="TEM_DEMO_U16",
        squad="U16",
        season_id="SEA_2025"
    )

    assert prof.status == DevelopmentStatus.DECLINING
    assert prof.status_badge == "🔴 DECLINING"


def test_04_conservative_stagnation_vs_stable():
    """Verify STAGNATING requires >= 8 GP, regular rotation (>= 10 MPG), and multi-window flat metrics."""
    # 1. 10 games, regular 20 MPG, flat metrics across both windows
    df_games_stagnating = pd.DataFrame([
        {"game_id": f"G_{i}", "game_date": f"2025-10-{i:02d}", "minutes": 20.0, "seconds_played": 1200,
         "points": 10, "fga": 8, "fgm": 4, "fg2a": 6, "fg2m": 3, "fg3a": 2, "fg3m": 1, "fta": 2, "ftm": 1,
         "trb": 4, "ast": 2, "stl": 1, "blk": 0, "tov": 2, "stint_pts_for": 30, "stint_pts_against": 30, "stint_poss": 25.0}
        for i in range(1, 11)
    ])

    prof_stag = AcademyDevelopmentEngine.evaluate_player_development(
        df_player_games=df_games_stagnating,
        player_id="PLY_TEST_4A",
        canonical_name="Test Stagnating Player",
        team_id="TEM_DEMO_U16",
        squad="U16",
        season_id="SEA_2025"
    )

    assert prof_stag.status == DevelopmentStatus.STAGNATING
    assert prof_stag.status_badge == "🟡 STAGNATING"

    # 2. Inconclusive / low playing time player (< 10 MPG) with same flat stats must fall back to STABLE
    df_games_bench = df_games_stagnating.copy()
    df_games_bench["minutes"] = 5.0
    df_games_bench["seconds_played"] = 300

    prof_stable = AcademyDevelopmentEngine.evaluate_player_development(
        df_player_games=df_games_bench,
        player_id="PLY_TEST_4B",
        canonical_name="Test Bench Stable Player",
        team_id="TEM_DEMO_U16",
        squad="U16",
        season_id="SEA_2025"
    )

    assert prof_stable.status == DevelopmentStatus.STABLE


# =============================================================================
# 2. POSSESSION GATING & MISSING DATA INTEGRITY
# =============================================================================

def test_05_possession_volume_gating_net_rating():
    """Verify Net Rating requires >= 20 reconstructable possessions in BOTH comparison windows."""
    # Recent window has only 8.0 possessions (< 20.0), even though Net Rating delta is massive
    df_games = pd.DataFrame([
        # Previous 5 games: 30 possessions each (150 total)
        {"game_id": f"G_{i}", "game_date": f"2025-10-{i:02d}", "minutes": 15.0, "seconds_played": 900,
         "points": 8, "fga": 6, "fgm": 3, "fg2a": 4, "fg2m": 2, "fg3a": 2, "fg3m": 1, "fta": 2, "ftm": 1,
         "trb": 3, "ast": 2, "stl": 1, "blk": 0, "tov": 1, "stint_pts_for": 20, "stint_pts_against": 20, "stint_poss": 30.0}
        for i in range(1, 6)
    ] + [
        # Recent 5 games: Very few stint possessions (total 8.0 poss across 5 games)
        {"game_id": f"G_{i}", "game_date": f"2025-11-{i:02d}", "minutes": 15.0, "seconds_played": 900,
         "points": 9, "fga": 6, "fgm": 3, "fg2a": 4, "fg2m": 2, "fg3a": 2, "fg3m": 1, "fta": 2, "ftm": 1,
         "trb": 3, "ast": 2, "stl": 1, "blk": 0, "tov": 1, "stint_pts_for": 15, "stint_pts_against": 5, "stint_poss": 1.6}
        for i in range(6, 11)
    ])

    prof = AcademyDevelopmentEngine.evaluate_player_development(
        df_player_games=df_games,
        player_id="PLY_TEST_5",
        canonical_name="Test Low Poss Net Rtg",
        team_id="TEM_DEMO_U16",
        squad="U16",
        season_id="SEA_2025"
    )

    deltas = prof.deltas
    assert deltas.net_rtg_eligible_for_classification is False
    # Despite high Net Rating difference, athlete cannot be classified as IMPROVING
    assert prof.status == DevelopmentStatus.STABLE
    # Verify low volume note in primary signals
    net_signals = [s for s in prof.primary_signals if "Net Rating" in s]
    assert len(net_signals) > 0
    assert "Low Volume" in net_signals[0] or "Excluded" in net_signals[0]


def test_06_missing_pbp_and_sample_floor():
    """Verify missing PBP evaluates to None (never 0.0) and sample < 4 GP is strictly INSUFFICIENT DATA."""
    # 2-game sample
    df_small = pd.DataFrame([
        {"game_id": "G_1", "game_date": "2025-10-01", "minutes": 15.0, "seconds_played": 900,
         "points": 20, "fga": 10, "fgm": 8, "fg2a": 8, "fg2m": 6, "fg3a": 2, "fg3m": 2, "fta": 4, "ftm": 4,
         "trb": 5, "ast": 5, "stl": 3, "blk": 1, "tov": 1, "stint_poss": None, "stint_pts_for": None, "stint_pts_against": None},
        {"game_id": "G_2", "game_date": "2025-10-08", "minutes": 15.0, "seconds_played": 900,
         "points": 25, "fga": 12, "fgm": 10, "fg2a": 10, "fg2m": 8, "fg3a": 2, "fg3m": 2, "fta": 6, "ftm": 5,
         "trb": 6, "ast": 4, "stl": 2, "blk": 0, "tov": 2, "stint_poss": None, "stint_pts_for": None, "stint_pts_against": None}
    ])

    prof = AcademyDevelopmentEngine.evaluate_player_development(
        df_player_games=df_small,
        player_id="PLY_TEST_6",
        canonical_name="Test Small Sample",
        team_id="TEM_DEMO_U16",
        squad="U16",
        season_id="SEA_2025"
    )

    assert prof.status == DevelopmentStatus.INSUFFICIENT_DATA
    assert prof.status_badge == "⚪ INSUFFICIENT DATA"
    assert prof.evidence_strength == EvidenceStrength.INSUFFICIENT
    assert prof.baseline_window.net_rtg is None


# =============================================================================
# 3. TEMPORAL INTEGRITY & POINT-IN-TIME EVALUATION
# =============================================================================

def test_07_temporal_point_in_time_zero_leakage(ds):
    """Verify point-in-time evaluation with as_of_date strictly excludes future matches."""
    # Maximilian Becker has 21 matches across 2025/26 season.
    # Set as_of_date to mid-November 2025 (e.g. 2025-11-15)
    cutoff = "2025-11-15"
    mon_historical = ds.get_academy_development_monitor(season_id="SEA_2025", squad_scope="U16", as_of_date=cutoff)
    fall_hist = next((p for p in mon_historical if "Becker" in p["canonical_name"]), None)

    assert fall_hist is not None
    # Historical games must be strictly <= cutoff
    hist_gp = fall_hist["baseline_window"]["gp"]
    assert hist_gp < 21
    assert hist_gp > 0


# =============================================================================
# 4. CATEGORY ISOLATION & DUAL-REGISTRATION SEGREGATION
# =============================================================================

def test_08_category_isolation_u16_vs_u19(ds):
    """Verify U16 returns only U16 data, U19 returns only U19 data, and Fall's U16 games never leak to U19."""
    u16_mon = ds.get_academy_development_monitor(season_id="SEA_2025", squad_scope="U16")
    u19_mon = ds.get_academy_development_monitor(season_id="SEA_2025", squad_scope="U19")

    # All U16 profiles must have squad == 'U16' and team_id == 'TEM_DEMO_U16'
    for p in u16_mon:
        assert p["squad"] == "U16"
        assert p["team_id"] == "TEM_DEMO_U16"

    # All U19 profiles must have squad == 'U19' and team_id == 'TEM_DEMO_U19'
    for p in u19_mon:
        assert p["squad"] == "U19"
        assert p["team_id"] == "TEM_DEMO_U19"

    # In SEA_2025, U19 has 0 match boxscores currently.
    # Therefore, all U19 players must be INSUFFICIENT DATA with 0 matches.
    for p in u19_mon:
        assert p["status"] == "INSUFFICIENT DATA"
        assert p["baseline_window"]["gp"] == 0
        assert p["baseline_window"]["total_minutes"] == 0.0

    # Maximilian Becker is registered on both U16 and U19.
    # In U16, he has > 15 games. In U19, he MUST have 0 games.
    fall_u16 = next((p for p in u16_mon if "Becker" in p["canonical_name"]), None)
    fall_u19 = next((p for p in u19_mon if "Becker" in p["canonical_name"]), None)

    assert fall_u16 is not None
    assert fall_u16["baseline_window"]["gp"] >= 15

    assert fall_u19 is not None
    assert fall_u19["baseline_window"]["gp"] == 0
    assert fall_u19["status"] == "INSUFFICIENT DATA"


def test_09_all_academy_purely_descriptive(ds):
    """Verify All Academy combines cohorts for reporting without merged normative benchmarks."""
    summary = ds.get_academy_development_summary(season_id="SEA_2025", squad_scope="All Academy")

    assert summary["total_players"] == summary["u16_breakdown"]["total"] + summary["u19_breakdown"]["total"]
    # U16 has active game evaluation
    assert summary["u16_breakdown"]["total"] > 0
    # U19 has registered roster
    assert summary["u19_breakdown"]["total"] > 0
    # Strict separation
    assert summary["u19_breakdown"]["insufficient_data"] == summary["u19_breakdown"]["total"]


# =============================================================================
# 5. U16 -> U19 PIPELINE SCREENING MATRIX
# =============================================================================

def test_10_u16_pipeline_screening_matrix(ds):
    """Verify pipeline evaluates all 5 explicit criteria (PASS/NOT MET/UNAVAILABLE) without composite ranking scores."""
    pipeline = ds.get_u16_to_u19_pipeline_candidates(season_id="SEA_2025")
    assert len(pipeline) > 0

    valid_statuses = {"PASS", "NOT MET", "UNAVAILABLE"}
    valid_qual_statuses = {"POTENTIAL U19 CANDIDATE", "CONDITIONAL CANDIDATE", "NOT CURRENTLY INDICATED"}

    for c in pipeline:
        assert c["sample_stability"]["status"] in valid_statuses
        assert c["trajectory"]["status"] in valid_statuses
        assert c["efficiency"]["status"] in valid_statuses
        assert c["role_capacity"]["status"] in valid_statuses
        assert c["on_court_impact"]["status"] in valid_statuses
        assert c["qualification_status"] in valid_qual_statuses
        # Must NOT contain arbitrary composite score
        assert "composite_score" not in c
        assert "development_score" not in c
        assert "ranking" not in c


def test_11_pipeline_high_ppg_alone_cannot_qualify():
    """Verify a player with high scoring volume alone cannot qualify as POTENTIAL U19 CANDIDATE if efficiency/sample fails."""
    # Synthetic player with 25 PPG but poor TS% and low games
    df_inefficient_scorer = pd.DataFrame([
        {"game_id": f"G_{i}", "game_date": f"2025-10-{i:02d}", "minutes": 25.0, "seconds_played": 1500,
         "points": 25, "fga": 25, "fgm": 8, "fg2a": 15, "fg2m": 6, "fg3a": 10, "fg3m": 2, "fta": 4, "ftm": 2,
         "trb": 3, "ast": 1, "stl": 1, "blk": 0, "tov": 4, "stint_pts_for": 20, "stint_pts_against": 30, "stint_poss": 25.0}
        for i in range(1, 6)
    ])

    prof = AcademyDevelopmentEngine.evaluate_player_development(
        df_player_games=df_inefficient_scorer,
        player_id="PLY_CHUCKER",
        canonical_name="Inefficient Chucker",
        team_id="TEM_DEMO_U16",
        squad="U16",
        season_id="SEA_2025"
    )

    eval_candidate = AcademyDevelopmentEngine.evaluate_u16_pipeline_candidate(prof, benchmark_ts_threshold=50.0)

    # Inefficient chucker has TS% ~ 46.7% (< 50%) and only 5 GP (< 10 GP)
    assert eval_candidate.criterion_sample_stability == ScreeningCriterionStatus.NOT_MET
    assert eval_candidate.criterion_efficiency == ScreeningCriterionStatus.NOT_MET
    assert eval_candidate.qualification_status == "NOT CURRENTLY INDICATED"


# =============================================================================
# 6. DYNAMIC DATA DISCOVERY & PERFORMANCE SLA
# =============================================================================

def test_12_no_hardcoded_database_facts(ds):
    """Verify dynamic database derivation without hardcoded constants."""
    summary = ds.get_academy_development_summary(season_id="SEA_2025", squad_scope="All Academy")

    # Fetch live counts directly from DuckDB
    res_u16 = ds.conn.execute("SELECT COUNT(DISTINCT player_id) as c FROM player_team WHERE season_id = 'SEA_2025' AND team_id = 'TEM_DEMO_U16'").fetchone()[0]
    res_u19 = ds.conn.execute("SELECT COUNT(DISTINCT player_id) as c FROM player_team WHERE season_id = 'SEA_2025' AND team_id = 'TEM_DEMO_U19'").fetchone()[0]

    assert summary["u16_breakdown"]["total"] == res_u16
    assert summary["u19_breakdown"]["total"] == res_u19
    assert summary["total_players"] == (res_u16 + res_u19)


def test_13_performance_sla_batch_query(ds):
    """Verify warm-load execution completes well under the 1.0-second interactive target."""
    # Prime warm cache
    ds.get_academy_development_monitor(season_id="SEA_2025", squad_scope="U16")

    t0 = time.perf_counter()
    profiles = ds.get_academy_development_monitor(season_id="SEA_2025", squad_scope="U16")
    t_elapsed = time.perf_counter() - t0

    assert len(profiles) > 0
    assert t_elapsed < 1.0, f"Warm load took {t_elapsed:.3f}s (expected < 1.0s)"


def test_14_missing_data_honesty():
    """Verify zero division-by-zero errors and explicit None for missing boxscore/stint fields."""
    # Zero shot attempts (FGA=0, FTA=0), zero turnovers (TOV=0)
    df_empty_stats = pd.DataFrame([
        {"game_id": f"G_{i}", "game_date": f"2025-10-{i:02d}", "minutes": 10.0, "seconds_played": 600,
         "points": 0, "fga": 0, "fgm": 0, "fg2a": 0, "fg2m": 0, "fg3a": 0, "fg3m": 0, "fta": 0, "ftm": 0,
         "trb": 2, "ast": 0, "stl": 0, "blk": 0, "tov": 0, "stint_pts_for": None, "stint_pts_against": None, "stint_poss": None}
        for i in range(1, 6)
    ])

    prof = AcademyDevelopmentEngine.evaluate_player_development(
        df_player_games=df_empty_stats,
        player_id="PLY_DEFENDER",
        canonical_name="Zero Shot Player",
        team_id="TEM_DEMO_U16",
        squad="U16",
        season_id="SEA_2025"
    )

    base = prof.baseline_window
    assert base.ts_pct is None
    assert base.efg_pct is None
    assert base.ast_to_tov is None
    assert base.net_rtg is None
    assert prof.status == DevelopmentStatus.STABLE
    assert prof.evidence_strength in (EvidenceStrength.MODERATE, EvidenceStrength.LIMITED)


def test_15_structured_explanation_exposes_evidence_quality(ds):
    """Verify that every evaluated profile exposes evidence quality and structured why narrative."""
    profiles = ds.get_academy_development_monitor(season_id="SEA_2025", squad_scope="U16")
    for p in profiles:
        assert p["evidence_strength"] in ("STRONG EVIDENCE", "MODERATE EVIDENCE", "LIMITED EVIDENCE", "INSUFFICIENT EVIDENCE")
        assert len(p["why_narrative"]) > 10
        assert p["canonical_name"] in p["why_narrative"]

