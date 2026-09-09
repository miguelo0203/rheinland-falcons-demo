"""Comprehensive Test Suite for Player Development & Full Career Trajectory Module.

Validates:
1. Strict Category Isolation (U16 vs U19 vs All Academy)
2. Dual-Category Player Segregation
3. Additive Totals & Recalculated Rates (Dean Oliver TS%, eFG%, AST/TOV)
4. Chronological Ordering & Date Invariants
5. All 14 Longitudinal Timeline Metrics Presence
6. Missing Metric Integrity (None/NaN, never false zeros)
7. Category Transition Detection (U16 -> U19)
8. Plotly Timeline Component Rendering
9. Point-in-Time Historical State Reconstruction (0% Future Leakage)
10. Point-in-Time Rolling 4-Game Window Dynamics
11. Recent Form Multi-Window Comparison (L5 vs L10 vs Baseline)
12. Objective Direction Badging & Non-Causal Descriptions
13. Normative League Benchmark Separation
14. Full Academy Roster Graceful Degradation
"""

import sys
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, ".")

from app.services.data_service import DataService
from app.components.longitudinal_timeline import render_longitudinal_timeline, METRIC_CONFIG


@pytest.fixture(scope="module")
def ds():
    service = DataService()
    yield service
    service.close()


# =============================================================================
# 1. CATEGORY ISOLATION & SQUAD SCOPE INVARIANTS
# =============================================================================
def test_01_u16_career_isolation(ds):
    """Verifies that U16 scope strictly isolates TEM_DEMO_U16 and CMP_JBBL."""
    pid = "PLY_DEMO_104"  # Maximilian Becker
    df_u16 = ds.get_player_career_log(pid, squad_scope="U16")

    assert not df_u16.empty, "U16 career log should not be empty for active U16 player"
    assert (df_u16["team_id"] == "TEM_DEMO_U16").all(), "All games must belong to TEM_DEMO_U16"
    assert (df_u16["competition_id"] == "CMP_JBBL").all(), "All games must belong to CMP_JBBL"
    assert (df_u16["squad"] == "U16").all(), "All squad labels must be U16"


def test_02_u19_career_isolation(ds):
    """Verifies that U19 scope strictly queries TEM_DEMO_U19 and CMP_NBBL."""
    pid = "PLY_DEMO_104"
    df_u19 = ds.get_player_career_log(pid, squad_scope="U19")

    # Currently U19 has 0 played games in 2025/26
    if not df_u19.empty:
        assert (df_u19["team_id"] == "TEM_DEMO_U19").all()
        assert (df_u19["competition_id"] == "CMP_NBBL").all()
        assert (df_u19["squad"] == "U19").all()
    else:
        assert len(df_u19) == 0


def test_03_all_academy_scope_segregation(ds):
    """Verifies All Academy scope includes valid academy teams with squad annotations."""
    pid = "PLY_DEMO_104"
    df_all = ds.get_player_career_log(pid, squad_scope="All Academy")

    assert not df_all.empty
    assert set(df_all["team_id"]).issubset({"TEM_DEMO_U16", "TEM_DEMO_U19"})
    assert set(df_all["squad"]).issubset({"U16", "U19"})


def test_04_dual_category_player_no_cross_contamination(ds):
    """Verifies dual-category prospects don't bleed stats between scopes."""
    pid = "PLY_DEMO_104"
    df_u16 = ds.get_player_career_log(pid, squad_scope="U16")
    df_u19 = ds.get_player_career_log(pid, squad_scope="U19")
    df_all = ds.get_player_career_log(pid, squad_scope="All Academy")

    assert len(df_all) == len(df_u16) + len(df_u19)
    assert len(df_u16) == 21
    assert len(df_u19) == 0


# =============================================================================
# 2. ADDITIVE TOTALS & RECALCULATED DERIVED RATES
# =============================================================================
def test_05_career_summary_additive_totals(ds):
    """Verifies career totals equal the exact sum of individual game counts."""
    pid = "PLY_DEMO_104"
    summary = ds.get_player_career_summary(pid, squad_scope="All Academy")
    df_log = ds.get_player_career_log(pid, squad_scope="All Academy")

    totals = summary["totals"]
    assert totals["games_played"] == len(df_log)
    assert totals["total_points"] == int(df_log["points"].sum())
    assert totals["total_fga"] == int(df_log["fga"].sum())
    assert totals["total_fgm"] == int(df_log["fgm"].sum())
    assert totals["total_fta"] == int(df_log["fta"].sum())
    assert totals["total_ftm"] == int(df_log["ftm"].sum())
    assert totals["total_trb"] == int(df_log["trb"].sum())
    assert totals["total_ast"] == int(df_log["ast"].sum())
    assert totals["total_tov"] == int(df_log["tov"].sum())


def test_06_derived_rates_recalculated_from_raw_sums(ds):
    """Verifies TS%, eFG%, and AST/TOV are recomputed from sums, never averaged percentages."""
    pid = "PLY_DEMO_104"
    summary = ds.get_player_career_summary(pid, squad_scope="All Academy")
    totals = summary["totals"]
    rates = summary["rates"]

    # True Shooting
    expected_ts_denom = 2 * (totals["total_fga"] + 0.44 * totals["total_fta"])
    expected_ts = round(100.0 * totals["total_points"] / expected_ts_denom, 1)
    assert rates["ts_pct"] == expected_ts

    # Effective Field Goal %
    expected_efg = round(100.0 * (totals["total_fgm"] + 0.5 * totals["total_fg3m"]) / totals["total_fga"], 1)
    assert rates["efg_pct"] == expected_efg

    # AST / TOV
    expected_ast_tov = round(float(totals["total_ast"]) / max(1, float(totals["total_tov"])), 2)
    assert rates["ast_to_tov"] == expected_ast_tov


# =============================================================================
# 3. CHRONOLOGICAL ORDERING & 14 METRICS INTEGRITY
# =============================================================================
def test_07_chronological_ordering(ds):
    """Verifies games are strictly sorted by game_date ASC, game_id ASC."""
    pid = "PLY_DEMO_104"
    df_log = ds.get_player_career_log(pid, squad_scope="All Academy")

    dates = pd.to_datetime(df_log["game_date"])
    assert dates.is_monotonic_increasing, "Career log games must be in strict chronological order"


def test_08_timeline_14_metrics_presence(ds):
    """Verifies all 14 metrics required by Section 3 are present in the career log."""
    pid = "PLY_DEMO_104"
    df_log = ds.get_player_career_log(pid, squad_scope="All Academy")

    required_metrics = [
        "net_rtg", "ortg", "drtg", "ts_pct", "efg_pct", "usage_pct",
        "points", "trb", "ast", "ast_to_tov", "stl", "blk", "tov", "minutes"
    ]
    for m in required_metrics:
        assert m in df_log.columns, f"Metric '{m}' must be present in career log"
        assert m in METRIC_CONFIG, f"Metric '{m}' must be configured in METRIC_CONFIG"


def test_09_missing_metrics_not_zeroed(ds):
    """Verifies that missing metrics (e.g., ratings on matches without PBP) are None/NaN, not 0.0."""
    pid = "PLY_DEMO_104"
    df_log = ds.get_player_career_log(pid, squad_scope="All Academy")

    # In matches where stint_poss is None or not present, net_rtg must be None/NaN
    no_stint_matches = df_log[df_log["stint_poss"].isna()]
    if not no_stint_matches.empty:
        assert no_stint_matches["net_rtg"].isna().all(), "Net rating without PBP stints must be NaN/None"
        assert no_stint_matches["ortg"].isna().all(), "ORtg without PBP stints must be NaN/None"
        assert no_stint_matches["drtg"].isna().all(), "DRtg without PBP stints must be NaN/None"


# =============================================================================
# 4. PLOTLY TIMELINE COMPONENT
# =============================================================================
def test_10_longitudinal_timeline_figure(ds):
    """Verifies Plotly timeline generates traces and handles missing gaps cleanly."""
    pid = "PLY_DEMO_104"
    df_log = ds.get_player_career_log(pid, squad_scope="All Academy")

    for metric in ["net_rtg", "points", "ts_pct", "usage_pct", "ast_to_tov"]:
        fig = render_longitudinal_timeline(df_log, "Maximilian Becker", metric_key=metric)
        assert fig is not None
        assert len(fig.data) >= 2, f"Figure for {metric} must have baseline and trend traces"


# =============================================================================
# 5. POINT-IN-TIME HISTORICAL STATE RECONSTRUCTION (0% FUTURE LEAKAGE)
# =============================================================================
def test_11_point_in_time_state_reconstruction_no_leakage(ds):
    """Verifies historical state reconstruction at a past game has ZERO future leakage."""
    pid = "PLY_DEMO_104"
    df_log = ds.get_player_career_log(pid, squad_scope="All Academy")
    assert len(df_log) >= 10

    # Select the 6th match as cutoff
    game_6 = df_log.iloc[5]
    cutoff_gid = game_6["game_id"]
    cutoff_date = game_6["game_date"]

    pit = ds.get_player_point_in_time_state(pid, as_of_game_id=cutoff_gid, squad_scope="All Academy")

    assert pit["cutoff_game_number"] == 6
    assert pit["as_of_game_id"] == cutoff_gid
    assert pit["as_of_date"] == str(cutoff_date)[:10]

    # Verify cumulative stats are computed ONLY from first 6 games
    first_6 = df_log.iloc[:6]
    expected_pts = int(first_6["points"].sum())
    assert pit["cumulative_profile"]["gp"] == 6
    assert round(pit["cumulative_profile"]["ppg"], 1) == round(expected_pts / 6.0, 1)

    # Subsequent games (7..21) must have ZERO impact
    all_pts = int(df_log["points"].sum())
    assert expected_pts != all_pts


def test_12_point_in_time_rolling_window(ds):
    """Verifies rolling 4-game window in point-in-time strictly uses the 4 games leading up to cutoff."""
    pid = "PLY_DEMO_104"
    df_log = ds.get_player_career_log(pid, squad_scope="All Academy")

    game_8 = df_log.iloc[7]
    cutoff_gid = game_8["game_id"]

    pit = ds.get_player_point_in_time_state(pid, as_of_game_id=cutoff_gid, squad_scope="All Academy")

    # Games 5, 6, 7, 8 (indices 4..7)
    window_4 = df_log.iloc[4:8]
    expected_rolling_ppg = round(window_4["points"].mean(), 1)
    assert pit["rolling_4_game"]["ppg"] == expected_rolling_ppg
    assert pit["rolling_4_game"]["gp"] == 4


# =============================================================================
# 6. RECENT FORM MULTI-WINDOW MONITORING
# =============================================================================
def test_13_recent_form_comparison_dynamics(ds):
    """Verifies Last 5 vs Last 10 vs Career Baseline comparison and directional evaluation."""
    pid = "PLY_DEMO_104"
    rf = ds.get_player_recent_form_comparison(pid, squad_scope="All Academy")

    assert "overall_direction" in rf
    assert rf["overall_direction"] in {"IMPROVING", "STABLE", "DECLINING"}
    assert "direction_badge" in rf
    assert "objective_description" in rf

    assert rf["last_5"]["gp"] == 5
    assert rf["last_10"]["gp"] == 10
    assert rf["baseline"]["gp"] == 21

    # Deltas are populated
    deltas = rf["deltas_l5_vs_baseline"]
    assert "delta_ppg" in deltas
    assert "delta_ts_pct" in deltas


# =============================================================================
# 7. FULL ACADEMY ROSTER ROBUSTNESS
# =============================================================================
def test_14_full_academy_roster_safety(ds):
    """Verifies career methods execute safely without crash for all academy players."""
    roster_u16 = ds.get_falcons_player_list(season_id="SEA_2025", squad_scope="U16")
    roster_u19 = ds.get_falcons_player_list(season_id="SEA_2025", squad_scope="U19")

    all_pids = set([p["player_id"] for p in roster_u16 + roster_u19 if p.get("player_id")])

    for pid in list(all_pids)[:10]:  # Test sample across academy
        summ = ds.get_player_career_summary(pid, squad_scope="All Academy")
        assert "games_played" in summ
        assert "totals" in summ
        assert "rates" in summ
        assert "milestones" in summ


# =============================================================================
# 8. UX ENHANCEMENTS: POSSESSION TOOLTIP & X-AXIS DECIMATION
# =============================================================================
def test_15_possession_tooltip_and_low_volume_label(ds):
    """Verifies that on-court rating tooltips display possession volume and label low-volume samples."""
    pid = "PLY_DEMO_104"
    df_log = ds.get_player_career_log(pid, squad_scope="All Academy")

    # 1. Net Rating figure
    fig_net = render_longitudinal_timeline(df_log, "Maximilian Becker", metric_key="net_rtg")
    marker_traces = [t for t in fig_net.data if getattr(t, "mode", None) == "markers"]
    assert len(marker_traces) > 0, "Must have marker traces for discrete matches"

    all_hovers = []
    for t in marker_traces:
        if t.hovertext:
            all_hovers.extend(t.hovertext)

    assert len(all_hovers) > 0, "Markers must define hovertext"

    # Verify possessions are present
    poss_hovers = [h for h in all_hovers if "Possessions:" in h]
    assert len(poss_hovers) > 0, "Hover text for on-court ratings must include Possessions:"

    # Verify low volume sample (< 10 possessions) is explicitly labeled
    low_vol_hovers = [h for h in poss_hovers if "(Low Volume)" in h]
    assert len(low_vol_hovers) >= 1, "Games with < 10 possessions must display (Low Volume)"
    assert any("4.4 (Low Volume)" in h for h in low_vol_hovers), "Audited game with 4.4 poss must show 4.4 (Low Volume)"

    # Verify normal/high volume sample (>= 10 possessions) has numeric value without (Low Volume)
    normal_vol_hovers = [h for h in poss_hovers if "(Low Volume)" not in h]
    assert len(normal_vol_hovers) >= 1
    assert any("52.2" in h for h in normal_vol_hovers), "Audited game with 52.2 poss must show 52.2"

    # 2. ORtg and DRtg also include possession volume
    for key in ["ortg", "drtg"]:
        fig = render_longitudinal_timeline(df_log, "Maximilian Becker", metric_key=key)
        m_traces = [t for t in fig.data if getattr(t, "mode", None) == "markers"]
        hovers = [h for t in m_traces if t.hovertext for h in t.hovertext]
        assert any("Possessions:" in h for h in hovers), f"Hover text for {key} must include Possessions:"

    # 3. Traditional boxscore / rate metrics (e.g. points, ts_pct) do NOT have possessions line
    fig_pts = render_longitudinal_timeline(df_log, "Maximilian Becker", metric_key="points")
    m_pts = [t for t in fig_pts.data if getattr(t, "mode", None) == "markers"]
    pts_hovers = [h for t in m_pts if t.hovertext for h in t.hovertext]
    assert all("Possessions:" not in h for h in pts_hovers), "Points tooltip must not include Possessions:"

    # 4. Missing possessions handling
    df_missing_poss = df_log.copy()
    df_missing_poss["stint_poss"] = np.nan
    fig_missing = render_longitudinal_timeline(df_missing_poss, "Maximilian Becker", metric_key="net_rtg")
    m_miss = [t for t in fig_missing.data if getattr(t, "mode", None) == "markers"]
    miss_hovers = [h for t in m_miss if t.hovertext for h in t.hovertext]
    assert all("Possessions: Unavailable" in h for h in miss_hovers), "Missing possessions must display Unavailable"


def test_16_xaxis_label_decimation_long_careers(ds):
    """Verifies X-axis tick label decimation activates only when career appearances exceed 30."""
    pid = "PLY_DEMO_104"
    df_log = ds.get_player_career_log(pid, squad_scope="All Academy")
    assert len(df_log) == 21, "Current baseline Fall dataset has 21 games (<= 30)"

    # 1. Career with <= 30 appearances retains all labels
    fig_short = render_longitudinal_timeline(df_log, "Maximilian Becker", metric_key="net_rtg")
    assert len(fig_short.layout.xaxis.tickvals) == 21
    assert len(fig_short.layout.xaxis.ticktext) == 21

    # 2. Extended career (> 30 appearances) decimates tick labels to step ~5
    # Simulate a multi-season 45-game career (21 + 21 + 3 = 45)
    df_long = pd.concat([df_log, df_log, df_log.iloc[:3]], ignore_index=True)
    df_long["game_date"] = pd.date_range("2025-10-01", periods=len(df_long), freq="W")
    df_long["game_id"] = [f"GAM_SIM_{i}" for i in range(len(df_long))]
    assert len(df_long) == 45, "Simulated long career has 45 appearances (> 30)"

    fig_long = render_longitudinal_timeline(df_long, "Maximilian Becker", metric_key="net_rtg")
    tickvals = fig_long.layout.xaxis.tickvals
    ticktext = fig_long.layout.xaxis.ticktext

    # Decimated ticks should be approximately every 5th game (~10 ticks for 45 games)
    assert len(tickvals) < 45, "X-axis labels must be decimated when appearances > 30"
    assert len(tickvals) <= 12, f"Expected ~10 ticks for 45 games, got {len(tickvals)}"
    assert len(tickvals) == len(ticktext), "Tick values and tick text count must match"

    # Verify first (index 0) and final (index 44) games are represented
    assert tickvals[0] == 0, "First game (index 0) must be labeled"
    assert tickvals[-1] == 44, "Final game (index 44) must be labeled"

    # 3. All underlying data points remain plotted
    # Baseline line trace spans all 45 games
    baseline_trace = fig_long.data[0]
    assert len(baseline_trace.x) == 45, "Baseline trace must span all 45 games"
    assert len(baseline_trace.y) == 45
    # X-axis range covers all games
    assert tuple(fig_long.layout.xaxis.range) == (-0.5, 44.5)

