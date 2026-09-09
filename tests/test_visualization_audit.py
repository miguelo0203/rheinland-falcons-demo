"""Automated Test Suite for Full Visualization & Data Presentation Audit."""

import pytest
import pandas as pd
from app.services.data_service import DataService
from app.components.ui import (
    render_player_identity,
    render_kpi_card,
    render_evidence_card,
    render_film_card,
    render_provenance_card,
    clean_html
)
from app.components.trajectory_plot import render_trajectory_chart
from app.components.radar_plot import render_percentile_radar
from app.components.court_plot import render_shot_chart

@pytest.fixture(scope="module")
def ds():
    service = DataService()
    yield service
    service.close()

def test_01_player_dossier_identity_resolution(ds):
    """Asserts that all FALCONS players resolve with valid name and canonical_name (no Unknown Player)."""
    players = ds.get_falcons_player_list(season_id="SEA_2025")
    assert len(players) > 0
    
    for p in players:
        pid = p["player_id"]
        cname = p["canonical_name"]
        dossier = ds.get_player_dossier(pid, season_id="SEA_2025")
        
        assert dossier, f"Dossier should not be empty for {pid}"
        bio = dossier.get("bio", {})
        assert bio.get("name") == cname, f"Expected {cname}, got {bio.get('name')}"
        assert bio.get("canonical_name") == cname, f"Expected {cname}, got {bio.get('canonical_name')}"
        assert "Unknown Player" not in bio.get("name"), f"Player {pid} resolved to Unknown Player"

def test_02_kpi_card_and_biometrics_rendering(ds):
    """Asserts that KPI cards and biometrics render cleanly without NaN or raw missing values."""
    players = ds.get_falcons_player_list(season_id="SEA_2025")
    sample_pid = players[0]["player_id"]
    dossier = ds.get_player_dossier(sample_pid, season_id="SEA_2025")
    
    bio = dossier.get("bio", {})
    stats = dossier.get("stats", {})
    pcts = dossier.get("percentiles", {})
    stabs = dossier.get("stability", {})
    
    kpi_html = render_kpi_card(
        label="SCORING",
        value=f"{stats.get('pts_per_40', 0):.1f} PTS/40",
        percentile_text=f"{pcts.get('pts_per_40', 50):.0f}th percentile",
        stability_tier=stabs.get("scoring", "EMERGING_SIGNAL"),
        volume_text=f"{stats.get('total_pts', 0):.0f} PTS · {stats.get('total_min', 0):.0f} MIN"
    )
    
    assert "nan" not in kpi_html.lower()
    assert "none" not in kpi_html.lower()
    assert "SCORING" in kpi_html

def test_03_trajectory_chart_no_artificial_truncation(ds):
    """Asserts that opponent names in the trajectory chart are not cut off at 10 characters."""
    df_log = pd.DataFrame([
        {
            "game_date": "2023-10-08",
            "opponent_name": "Bavaria Hawks",
            "points": 18.0,
            "ts_pct": 55.4
        }
    ])
    fig = render_trajectory_chart(df_log, "Test Player", 15.0, 50.0)
    assert fig is not None
    assert fig.layout.autosize is True
    
    # Check trace x-labels
    bar_trace = fig.data[0]
    label = bar_trace.x[0]
    assert "Bavaria Hawks" in label
    assert "Porsche BB" not in label or "Bavaria Hawks" in label

def test_04_radar_plot_responsiveness():
    """Asserts that 6-axis radar plot is responsive and has autosize enabled."""
    pcts = {
        'pts_per_40': 85.0,
        'ts_pct': 70.0,
        'reb_per_40': 60.0,
        'ast_per_40': 90.0,
        'ast_to_tov': 75.0,
        'def_disruption': 80.0
    }
    fig = render_percentile_radar(pcts, "Maximilian Becker")
    assert fig is not None
    assert fig.layout.autosize is True
    assert "Maximilian Becker" in fig.layout.title.text

def test_05_court_shot_chart_responsiveness(ds):
    """Asserts that FIBA shot chart maintains responsive layout with autosize."""
    df_shots = ds.get_player_shots("PLY_DEMO_104", season_id="SEA_2025")
    fig = render_shot_chart(df_shots, "Shot Map Test")
    assert fig is not None
    assert fig.layout.autosize is True
    assert fig.layout.yaxis.scaleanchor == "x"

def test_06_shot_zone_diet_aggregation(ds):
    """Asserts that shot zones breakdown calculates cleanly without NaN."""
    players = ds.get_falcons_player_list(season_id="SEA_2025")
    for p in players:
        df_zones = ds.get_player_shot_zones(p["player_id"], season_id="SEA_2025")
        if not df_zones.empty:
            assert "tactical_zone" in df_zones.columns
            assert "attempts" in df_zones.columns
            assert "fg_pct" in df_zones.columns
            assert not df_zones["fg_pct"].isna().any()
            assert not df_zones["frequency_pct"].isna().any()

def test_07_player_game_log_cleanliness(ds):
    """Asserts that match-by-match game log contains formatted columns and valid dates."""
    players = ds.get_falcons_player_list(season_id="SEA_2025")
    for p in players:
        df_log = ds.get_player_game_log(p["player_id"], season_id="SEA_2025")
        if not df_log.empty:
            assert "game_date" in df_log.columns
            assert "opponent_name" in df_log.columns
            assert "result" in df_log.columns
            assert "final_score" in df_log.columns
