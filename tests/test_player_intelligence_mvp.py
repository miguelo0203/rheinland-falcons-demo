"""Comprehensive Test Suite for Coach-Facing Player Intelligence MVP."""

import sys
from pathlib import Path
import pandas as pd
import pytest

sys.path.insert(0, ".")

from app.services.data_service import DataService
from app.components.court_plot import render_shot_chart
from app.components.radar_plot import render_percentile_radar
from app.components.trajectory_plot import render_trajectory_chart

@pytest.fixture(scope="module")
def ds():
    service = DataService()
    yield service
    service.close()

# -----------------------------------------------------------------------------
# 1. Player Coverage Tests
# -----------------------------------------------------------------------------
def test_01_falcons_player_list_coverage(ds):
    """Verifies that all FALCONS players are discoverable and sorted by minutes."""
    players = ds.get_falcons_player_list()
    assert len(players) >= 13, f"Expected >= 13 FALCONS players, got {len(players)}"
    assert players[0]["total_min"] >= players[-1]["total_min"]
    
def test_02_core_prospect_dossiers(ds):
    """Verifies dossier structure for core program prospects (Fall, Weber, Keller)."""
    core_pids = ['PLY_DEMO_104', 'PLY_DEMO_101', 'PLY_DEMO_102']
    for pid in core_pids:
        dossier = ds.get_player_dossier(pid)
        assert dossier, f"Dossier empty for {pid}"
        assert "bio" in dossier
        assert "stats" in dossier
        assert "percentiles" in dossier
        assert "stability" in dossier
        assert "findings" in dossier
        assert len(dossier["findings"]) >= 2

def test_03_small_sample_and_missing_biometrics(ds):
    """Verifies safe handling for players with small sample or missing biometrics."""
    # Test all FALCONS players
    players = ds.get_falcons_player_list()
    for p in players:
        dossier = ds.get_player_dossier(p["player_id"])
        assert dossier["bio"]["canonical_name"] == p["canonical_name"]
        # Ensure age_display and height_display never crash or equal NaN
        assert isinstance(dossier["bio"]["age_display"], str)
        assert isinstance(dossier["bio"]["height_display"], str)
        assert pd.notna(dossier["stats"]["pts_per_40"])
        assert dossier["stats"]["ts_pct"] is None or pd.notna(dossier["stats"]["ts_pct"])

# -----------------------------------------------------------------------------
# 2. Metric Correctness Tests
# -----------------------------------------------------------------------------
def test_04_rate_and_efficiency_metrics(ds):
    """Verifies TS%, eFG%, per-40 rates, and AST/TOV ratio calculations."""
    dossier = ds.get_player_dossier("PLY_DEMO_101") # Lukas Weber
    stats = dossier["stats"]
    
    # Mathematical checks
    expected_pts_40 = round(stats["total_pts"] * 40.0 / stats["total_min"], 1)
    assert stats["pts_per_40"] == expected_pts_40
    
    expected_ts_denom = 2 * (stats["total_fga"] + 0.44 * stats["total_fta"])
    expected_ts = round(stats["total_pts"] * 100.0 / expected_ts_denom, 1)
    assert stats["ts_pct"] == expected_ts
    
    expected_efg = round((stats["total_fgm"] + 0.5 * stats["total_fg3m"]) * 100.0 / stats["total_fga"], 1)
    assert stats["efg_pct"] == expected_efg
    
    expected_3par = round(stats["total_fg3a"] * 100.0 / stats["total_fga"], 1)
    assert stats["f3a_rate"] == expected_3par

def test_05_stability_tier_assignments(ds):
    """Verifies sample stability assignments for established vs emerging vs descriptive samples."""
    # Maximilian Becker (188 FGA, 426 min) -> ESTABLISHED_SIGNAL
    fall_dossier = ds.get_player_dossier("PLY_DEMO_104")
    assert fall_dossier["stability"]["scoring"] == "ESTABLISHED_SIGNAL"
    assert fall_dossier["stability"]["rebounding"] == "ESTABLISHED_SIGNAL"
    assert fall_dossier["stability"]["shooting_3p"] == "DESCRIPTIVE_ONLY" # only 5 3PA
    
    # Lukas Weber (47 3PA) -> EMERGING_SIGNAL
    gundel_dossier = ds.get_player_dossier("PLY_DEMO_101")
    assert gundel_dossier["stability"]["shooting_3p"] == "EMERGING_SIGNAL"
    
    # Mike Schulz (2 GP, 16 FGA) -> DESCRIPTIVE_ONLY
    tiefel_dossier = ds.get_player_dossier("PLY_DEMO_106")
    assert tiefel_dossier["stability"]["overall_sample"] == "DESCRIPTIVE_ONLY"

# -----------------------------------------------------------------------------
# 3. Context & Percentile Bounds Tests
# -----------------------------------------------------------------------------
def test_06_percentile_bounds_and_qualified_population(ds):
    """Verifies that all percentiles are strictly bounded in [0.0, 100.0] and population >= 30."""
    bench = ds.get_qualified_league_benchmark()
    assert len(bench) >= 30, f"Expected >= 30 qualified players, got {len(bench)}"
    
    players = ds.get_falcons_player_list()
    for p in players[:5]:
        dossier = ds.get_player_dossier(p["player_id"])
        for k, v in dossier["percentiles"].items():
            if k != "qualified_pop_size":
                assert 0.0 <= v <= 100.0, f"Percentile {k}={v} out of bounds for {p['canonical_name']}"

# -----------------------------------------------------------------------------
# 4. Shot Data & Spatial Coordinate Tests
# -----------------------------------------------------------------------------
def test_07_shot_data_and_coordinates(ds):
    """Verifies shot coordinate bounds and zone aggregations."""
    shots = ds.get_player_shots("PLY_DEMO_104") # Maximilian Becker
    assert len(shots) > 0
    valid_coords = shots.dropna(subset=["x_coord", "y_coord"])
    assert len(valid_coords) > 0
    assert valid_coords["x_coord"].min() >= 0.0
    assert valid_coords["x_coord"].max() <= 280.0
    assert valid_coords["y_coord"].min() >= 0.0
    assert valid_coords["y_coord"].max() <= 200.0
    
    zones = ds.get_player_shot_zones("PLY_DEMO_104")
    assert not zones.empty
    assert "Restricted Area (<= 1.5m)" in zones["tactical_zone"].values
    assert zones["frequency_pct"].sum() >= 99.0

# -----------------------------------------------------------------------------
# 5. Interpretation Engine Dynamic Synthesis Tests
# -----------------------------------------------------------------------------
def test_08_dynamic_findings_structure(ds):
    """Verifies format: Observation -> Context -> Volume -> Interpretation -> Film Q."""
    dossier = ds.get_player_dossier("PLY_DEMO_101")
    for f in dossier["findings"]:
        assert "category" in f
        assert "headline" in f
        assert "observation" in f
        assert "context" in f
        assert "volume_note" in f
        assert "interpretation" in f
        assert "stability_tier" in f
        assert "film_question" in f
        # Ensure no empty strings
        assert len(f["observation"]) > 10
        assert len(f["context"]) > 10
        assert len(f["interpretation"]) > 10

# -----------------------------------------------------------------------------
# 6. Plotly Component Rendering Tests
# -----------------------------------------------------------------------------
def test_09_plotly_components_render(ds):
    """Verifies that Plotly figures render without exceptions."""
    dossier = ds.get_player_dossier("PLY_DEMO_101")
    shots = ds.get_player_shots("PLY_DEMO_101")
    logs = ds.get_player_game_log("PLY_DEMO_101")
    
    # 1. Court chart
    fig_court = render_shot_chart(shots, title="Test Court")
    assert fig_court is not None
    assert len(fig_court.data) >= 1
    
    # 2. Radar chart
    fig_radar = render_percentile_radar(dossier["percentiles"], "Lukas Weber")
    assert fig_radar is not None
    assert len(fig_radar.data) == 2 # Benchmark circle + Player polygon
    
    # 3. Trajectory chart
    fig_traj = render_trajectory_chart(logs, "Lukas Weber", dossier["stats"]["ppg"], dossier["stats"]["ts_pct"])
    assert fig_traj is not None
    assert len(fig_traj.data) == 3 # Bars + Baseline + Rolling line
