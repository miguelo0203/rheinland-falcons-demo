"""Comprehensive Test Suite for Team Intelligence V1 (Lineup & Quintet Intelligence)."""

import pytest
import pandas as pd
import duckdb
from app.services.data_service import DataService
from python.analytics.team_intelligence_engine import (
    LineupReconstructionEngine,
    QuintetComplementarityEngine,
    LineupEvidenceTier
)
from python.analytics.pair_trio_engine import PairTrioEngine


@pytest.fixture
def ds():
    service = DataService()
    yield service
    service.close()


def test_01_observed_lineup_reconstruction_integrity(ds):
    """Verifies that PBP stint reconstruction accurately produces 5-man on-court lineups."""
    df_lineups = ds.get_observed_lineups(season_id="SEA_2025")
    assert not df_lineups.empty, "Observed lineups dataframe should not be empty."
    assert len(df_lineups) >= 100, f"Expected >= 100 observed lineups, got {len(df_lineups)}"
    
    # Top lineup should be core starting 5
    top_lineup = df_lineups.iloc[0]
    assert top_lineup['minutes'] >= 50.0, f"Top lineup minutes should be >= 50m, got {top_lineup['minutes']}"
    assert top_lineup['possessions'] >= 100.0, f"Top lineup possessions should be >= 100, got {top_lineup['possessions']}"
    assert top_lineup['evidence_tier'] == "STRONG_EVIDENCE"
    assert top_lineup['net_rtg'] > 0, "Core starting 5 should have positive Net Rating"


def test_02_mode_b_profile_based_quintet_no_fabrication(ds):
    """Verifies that unobserved player combinations receive Mode B without false minutes/NetRtg."""
    # Synthetic unobserved bench unit
    unobs_ids = ['PLY_140181742', 'PLY_140181689', 'PLY_59480', 'PLY_140181717', 'PLY_57140']
    res = ds.evaluate_progressive_quintet(unobs_ids, season_id="SEA_2025")
    
    assert res['is_observed'] is False, "Unobserved quintet must not be marked as observed."
    assert res['observed_record'] is None, "Unobserved quintet must have NO observed record."
    assert 'scores' in res, "Profile-based scores must be present."
    assert 0 <= res['scores']['overall_fit_index'] <= 100, "Fit index must be bounded [0, 100]."
    assert len(res['strengths']) > 0, "Strengths should be generated."
    assert len(res['risks_and_overlaps']) > 0, "Risks should be generated."


def test_03_progressive_1_to_5_addition_deltas(ds):
    """Verifies that incremental player additions calculate accurate change-by-addition deltas."""
    p1 = ['PLY_DEMO_104']
    p2 = ['PLY_DEMO_104', 'PLY_DEMO_101']
    
    res1 = ds.evaluate_progressive_quintet(p1, season_id="SEA_2025")
    res2 = ds.evaluate_progressive_quintet(p2, previous_player_ids=p1, season_id="SEA_2025")
    
    assert res1['count'] == 1
    assert res2['count'] == 2
    assert res2['addition_delta'] is not None
    assert res2['addition_delta']['added_player_id'] == 'PLY_DEMO_101'
    assert 'Lukas Weber' in res2['addition_delta']['added_player_name']
    assert res2['addition_delta']['delta_fit_index'] != 0.0


def test_04_pair_and_trio_chemistry_extraction(ds):
    """Verifies that 2-man pairs, 3-man trios, and 4-man quartets are correctly extracted with exact on-court stats."""
    df_pairs = ds.get_observed_pairs(season_id="SEA_2025")
    df_trios = ds.get_observed_trios(season_id="SEA_2025")
    df_quartets = ds.get_observed_quartets(season_id="SEA_2025")
    
    assert not df_pairs.empty, "Observed pairs dataframe should not be empty."
    assert not df_trios.empty, "Observed trios dataframe should not be empty."
    assert not df_quartets.empty, "Observed quartets dataframe should not be empty."
    assert len(df_pairs) >= 50, f"Expected >= 50 pairs, got {len(df_pairs)}"
    assert len(df_trios) >= 150, f"Expected >= 150 trios, got {len(df_trios)}"
    assert len(df_quartets) >= 200, f"Expected >= 200 quartets, got {len(df_quartets)}"
    
    # Check top pair and quartet
    top_pair = df_pairs.iloc[0]
    assert top_pair['minutes'] >= 200.0, "Top pair should have >= 200 minutes."
    assert top_pair['confidence_tier'] == "STRONG_EVIDENCE"

    top_quartet = df_quartets.iloc[0]
    assert top_quartet['minutes'] >= 50.0, "Top quartet should have >= 50 minutes."
    assert top_quartet['confidence_tier'] == "STRONG_EVIDENCE"


def test_05_hub2_streamlit_ui_rendering():
    """Verifies that Hub 2 renders all 5 tabs and quintet builder widgets cleanly in Streamlit."""
    from streamlit.testing.v1 import AppTest
    
    at = AppTest.from_file("app/main.py")
    at.run(timeout=25)
    if len(at.text_input) > 0 and len(at.button) > 0:
        at.text_input[0].input("demotool")
        at.button[0].click().run()
        
    nav_radio = [r for r in at.sidebar.radio if "Navigation" in r.label][0]
    nav_radio.set_value("2. 🏆 Team Intelligence & Performance Overview").run(timeout=25)
    
    assert len(at.exception) == 0, f"Exception on Hub 2: {[e.value for e in at.exception]}"
    assert len(at.tabs) >= 5, f"Expected >= 5 tabs in Hub 2, found {len(at.tabs)}"
