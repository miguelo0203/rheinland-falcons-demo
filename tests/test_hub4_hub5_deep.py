"""Comprehensive automated tests for Hub 4 and Hub 5."""

import pytest
import pandas as pd
from app.services.data_service import DataService
from app.components.court_plot import render_shot_chart, render_shot_comparison_chart, create_court_shapes

@pytest.fixture
def data_service():
    return DataService()

# ==============================================================================
# HUB 4: SHOT LAB & SPATIAL TESTS
# ==============================================================================

def test_team_shots_loading(data_service):
    """Verifies team shot extraction and spatial coordinates for SEA_2025."""
    df_shots = data_service.get_team_shots("SEA_2025", is_falcons_only=True)
    assert not df_shots.empty, "Falcons shots should not be empty for SEA_2025"
    assert len(df_shots) >= 1000, f"Expected >=1000 Falcons shots, got {len(df_shots)}"
    
    required_cols = ["shot_id", "game_id", "game_date", "period", "shot_type", "is_made", "x_coord", "y_coord", "shot_zone"]
    for col in required_cols:
        assert col in df_shots.columns, f"Missing required column {col} in team shots"
        
    obs_count = (df_shots["shot_location_status"] == "OBSERVED").sum()
    assert obs_count >= 1000, f"Expected >=1000 observed coordinates, got {obs_count}"


def test_tactical_zone_classification(data_service):
    """Verifies that all 5 core tactical zones are populated with valid data."""
    df_shots = data_service.get_team_shots("SEA_2025", is_falcons_only=True)
    zones = set(df_shots["shot_zone"].unique())
    expected_zones = {"RESTRICTED_AREA", "PAINT_NON_RA", "MID_RANGE", "CORNER_3PT", "ABOVE_THE_BREAK_3PT"}
    assert expected_zones.issubset(zones), f"Expected zones {expected_zones}, got {zones}"


def test_court_plot_generation(data_service):
    """Verifies that Plotly court shot chart generates valid figures and shapes."""
    df_shots = data_service.get_team_shots("SEA_2025", is_falcons_only=True)
    fig = render_shot_chart(df_shots, title="Test Shot Chart")
    assert fig is not None
    assert len(fig.data) >= 2, "Expected at least 2 traces (makes and misses)"
    assert len(fig.layout.shapes) >= 6, "Expected FIBA court shapes"


def test_player_comparison_chart(data_service):
    """Verifies side-by-side Player A vs Player B comparison subplot generator."""
    df_shots = data_service.get_team_shots("SEA_2025", is_falcons_only=True)
    df_gundel = df_shots[df_shots["player_name"].str.contains("Weber", na=False)]
    df_ohr = df_shots[df_shots["player_name"].str.contains("Wagner", na=False)]
    
    fig = render_shot_comparison_chart(df_gundel, df_ohr, "Lukas Weber", "Julian Wagner")
    assert fig is not None
    assert len(fig.data) >= 2, "Expected traces in comparison chart"


def test_spatial_evolution(data_service):
    """Verifies game-by-game spatial evolution calculation."""
    df_evo = data_service.get_spatial_evolution("SEA_2025")
    assert not df_evo.empty, "Spatial evolution dataframe should not be empty"
    assert len(df_evo) >= 10, f"Expected >= 10 match observations, got {len(df_evo)}"
    
    for col in ["game_id", "game_date", "opponent_name", "result", "margin", "rim_freq", "total_3p_freq", "rim_fg_pct"]:
        assert col in df_evo.columns, f"Missing evolution column {col}"


# ==============================================================================
# HUB 5: EVIDENCE & TRACEABILITY TESTS
# ==============================================================================

def test_finding_traceability_matrix(data_service):
    """Verifies that finding traceability models exist with complete hierarchical metadata and game links."""
    trace_data = data_service.get_finding_traceability_data("SEA_2025")
    assert len(trace_data) == 5, f"Expected 5 structured findings, got {len(trace_data)}"
    
    for f in trace_data:
        assert "finding_id" in f
        assert "title" in f
        assert "epistemic_class" in f
        assert f["epistemic_class"] in {"DESCRIPTIVE", "ASSOCIATIONAL", "HYPOTHESIS"}
        assert "evidence_strength" in f
        assert "sample_size_N" in f
        assert "methodology" in f
        assert "game_evidence" in f
        assert len(f["game_evidence"]) >= 2, f"Expected at least 2 game evidence records for {f['finding_id']}"
        
        for gev in f["game_evidence"]:
            assert "game_id" in gev
            assert "game_date" in gev
            assert "opponent_name" in gev
            assert "result" in gev
            assert "margin" in gev
            assert "metric_value" in gev
            assert "contribution_note" in gev


def test_hypotheses_loading(data_service):
    """Verifies coach video review hypotheses with lifecycle status."""
    df_hyp = data_service.get_hypotheses()
    assert not df_hyp.empty, "Hypotheses should not be empty"
    assert len(df_hyp) >= 2, f"Expected >= 2 hypotheses, got {len(df_hyp)}"
    for col in ["hypothesis_id", "statement", "status", "recommended_next_step"]:
        assert col in df_hyp.columns, f"Missing hypothesis column {col}"


def test_data_quality_matrix(data_service):
    """Verifies data quality matrix and validation status coverage."""
    df_qual = data_service.get_game_data_quality()
    assert not df_qual.empty, "Data quality table should not be empty"
    assert "validation_status" in df_qual.columns
    statuses = set(df_qual["validation_status"].unique())
    assert {"PASS", "FAIL_WITH_ERRORS"}.issubset(statuses), f"Expected validation statuses, got {statuses}"
