"""Comprehensive Test Suite for Universal Evidence & Statistical Interpretation Engine v2.

Verifies:
- Test A: Makes vs. Attempts distinction (40/80 vs 40/200 3PT)
- Test B: High efficiency on emerging sample (23/47 3PT -> EMERGING_SIGNAL)
- Test C: High scoring + high volume recognition
- Test D: High scoring + high efficiency recognition
- Test E: Assists contextualization (APG + AST/40 + AST/TOV)
- Test F: Rebounds contextualization (RPG + REB/40 + minutes)
- Test G: Net Rating responsible team attribution
- Test H: ORTG / DRTG contextualization and limitations
- Test I: Percentile vs. Stability separation (100th %ile + EMERGING_SIGNAL)
- Test J: Missing context handling without fabrication
- Test K: Determinism of structured output
- Test L: Complete evidence hierarchy verification
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, ".")

from python.analytics.evidence_engine import (
    EvidenceInterpretationEngine,
    StabilityEvaluator,
    StabilityTier,
    METRIC_RELATIONSHIPS,
    StructuredEvidenceInterpretation
)

@pytest.fixture
def engine():
    return EvidenceInterpretationEngine()

@pytest.fixture
def base_benchmark_meta():
    return {
        "season_id": "SEA_2025",
        "competition_id": "CMP_JBBL",
        "game_type": "OFFICIAL",
        "min_minutes": 100.0,
        "as_of_date": None,
        "qualified_pop_size": 34
    }

# -----------------------------------------------------------------------------
# Test A: Makes vs Attempts Distinction
# -----------------------------------------------------------------------------
def test_a_makes_vs_attempts_distinction(engine, base_benchmark_meta):
    """Verifies that identical makes (40 3PM) across different attempt volumes (80 vs 200) yield opposite interpretations."""
    # Player 1: 40/80 (50.0% 3P, high conversion, moderate volume)
    p1_stats = {
        "total_fg3m": 40, "total_fg3a": 80, "total_fga": 160,
        "fg3_pct": 50.0, "f3a_rate": 50.0, "gp": 15, "total_min": 350
    }
    p1_pcts = {"fg3_pct": 100.0, "qualified_pop_size": 34}
    p1_meds = {"fg3_pct": 25.0}
    res1 = engine.interpret_perimeter_shooting(p1_stats, p1_pcts, p1_meds, base_benchmark_meta)

    # Player 2: 40/200 (20.0% 3P, low conversion, high volume/diet)
    p2_stats = {
        "total_fg3m": 40, "total_fg3a": 200, "total_fga": 250,
        "fg3_pct": 20.0, "f3a_rate": 80.0, "gp": 15, "total_min": 350
    }
    p2_pcts = {"fg3_pct": 30.0, "qualified_pop_size": 34}
    p2_meds = {"fg3_pct": 25.0}
    res2 = engine.interpret_perimeter_shooting(p2_stats, p2_pcts, p2_meds, base_benchmark_meta)

    assert "conversion" in res1.interpretation.lower() or "weapon" in res1.interpretation.lower()
    assert "attempt volume" in res2.interpretation.lower() or "volume-driven" in res2.interpretation.lower()
    assert res1.stability_tier == StabilityTier.USABLE_SIGNAL.value
    assert res2.stability_tier == StabilityTier.ESTABLISHED_SIGNAL.value
    assert res1.efficiency_context["fg3_pct"] == 50.0
    assert res2.efficiency_context["fg3_pct"] == 20.0

# -----------------------------------------------------------------------------
# Test B: High Efficiency on Emerging Sample
# -----------------------------------------------------------------------------
def test_b_high_efficiency_emerging_sample(engine, base_benchmark_meta):
    """Verifies that 23/47 3P (48.9%) is classified as emerging signal, not established shooter."""
    stats = {
        "total_fg3m": 23, "total_fg3a": 47, "total_fga": 215,
        "fg3_pct": 48.9, "f3a_rate": 21.9, "gp": 19, "total_min": 474.9
    }
    pcts = {"fg3_pct": 100.0, "qualified_pop_size": 34}
    meds = {"fg3_pct": 25.0}
    res = engine.interpret_perimeter_shooting(stats, pcts, meds, base_benchmark_meta)

    assert res.stability_tier == StabilityTier.EMERGING_SIGNAL.value
    assert "emerging" in res.interpretation.lower()
    assert "47 attempts" in res.interpretation or "47" in res.interpretation
    assert any("stabilization threshold" in lim.lower() or "limited" in lim.lower() for lim in res.limitations)

# -----------------------------------------------------------------------------
# Test C: High Scoring + High Volume
# -----------------------------------------------------------------------------
def test_c_high_scoring_high_volume(engine, base_benchmark_meta):
    """Verifies that high scoring with low efficiency is explicitly identified as volume-driven."""
    stats = {
        "total_pts": 350, "pts_per_40": 26.0, "ppg": 17.5, "total_min": 538.0,
        "total_fga": 320, "total_fta": 60, "ts_pct": 39.5, "gp": 20
    }
    pcts = {"pts_per_40": 90.0, "ts_pct": 25.0, "qualified_pop_size": 34}
    meds = {"pts_per_40": 16.9, "ts_pct": 49.1}
    res = engine.interpret_scoring(stats, pcts, meds, base_benchmark_meta)

    assert "volume-driven" in res.interpretation.lower() or "shot volume" in res.interpretation.lower()
    assert res.stability_tier == StabilityTier.ESTABLISHED_SIGNAL.value

# -----------------------------------------------------------------------------
# Test D: High Scoring + High Efficiency
# -----------------------------------------------------------------------------
def test_d_high_scoring_high_efficiency(engine, base_benchmark_meta):
    """Verifies that high scoring with high TS% recognizes both dimensions."""
    stats = {
        "total_pts": 297, "pts_per_40": 25.0, "ppg": 15.6, "total_min": 474.9,
        "total_fga": 215, "total_fta": 47, "ts_pct": 64.0, "gp": 19
    }
    pcts = {"pts_per_40": 85.3, "ts_pct": 94.1, "qualified_pop_size": 34}
    meds = {"pts_per_40": 16.9, "ts_pct": 49.1}
    res = engine.interpret_scoring(stats, pcts, meds, base_benchmark_meta)

    assert "above-average" in res.interpretation.lower() or "high" in res.interpretation.lower()
    assert "efficiency" in res.interpretation.lower()
    assert res.efficiency_context["ts_pct"] == 64.0

# -----------------------------------------------------------------------------
# Test E: Assists Contextualization (APG + AST/40 + AST/TOV)
# -----------------------------------------------------------------------------
def test_e_assists_contextualization(engine, base_benchmark_meta):
    """Verifies that assist totals are paired with rate metrics and turnover control."""
    stats = {
        "total_ast": 57, "total_tov": 56, "apg": 3.0, "ast_per_40": 4.8,
        "ast_to_tov": 1.02, "total_min": 474.9, "mpg": 25.0, "gp": 19
    }
    pcts = {"ast_per_40": 79.4, "ast_to_tov": 70.6, "qualified_pop_size": 34}
    meds = {"ast_per_40": 3.5, "ast_to_tov": 0.8}
    res = engine.interpret_playmaking(stats, pcts, meds, base_benchmark_meta)

    assert "4.8 ast/40" in res.headline.lower()
    assert "1.02" in res.headline or "1.02" in res.interpretation
    assert "79th percentile" in res.interpretation or "79" in res.context["text"]
    assert len(res.film_questions) > 0

# -----------------------------------------------------------------------------
# Test F: Rebounds Contextualization (RPG + REB/40 + Minutes)
# -----------------------------------------------------------------------------
def test_f_rebounds_contextualization(engine, base_benchmark_meta):
    """Verifies that rebound interpretation incorporates per-minute rates and glass splits."""
    stats = {
        "total_trb": 221, "total_orb": 85, "total_drb": 136, "rpg": 10.5,
        "reb_per_40": 20.7, "total_min": 426.1, "mpg": 20.3, "gp": 21
    }
    pcts = {"reb_per_40": 100.0, "qualified_pop_size": 34}
    meds = {"reb_per_40": 8.4}
    res = engine.interpret_rebounding(stats, pcts, meds, base_benchmark_meta)

    assert "20.7 reb/40" in res.headline.lower()
    assert "10.5 rpg" in res.headline.lower()
    assert "offensive (85)" in res.interpretation or "85" in res.observation["text"]
    assert res.stability_tier == StabilityTier.ESTABLISHED_SIGNAL.value

# -----------------------------------------------------------------------------
# Test G: Net Rating Responsible Team Attribution
# -----------------------------------------------------------------------------
def test_g_net_rating_responsible_attribution(engine):
    """Verifies that net rating describes team performance during exposure, not isolated individual quality."""
    res = engine.interpret_net_rating(net_rtg=+14.2, minutes=180.0, possessions=320.0)

    assert "team outscored opponents" in res.interpretation.lower()
    assert "not be interpreted as an isolated measure" in res.interpretation.lower()
    assert any("lineup effects" in lim.lower() for lim in res.limitations)
    assert res.stability_tier == StabilityTier.EMERGING_SIGNAL.value

# -----------------------------------------------------------------------------
# Test H: ORTG and DRTG Contextual Limitations
# -----------------------------------------------------------------------------
def test_h_ortg_drtg_contextual_limitations(engine):
    """Verifies that ORTG and DRTG explicitly present offensive/defensive team limitations."""
    res_off = engine.interpret_offensive_rating(ortg=112.5, minutes=220.0, possessions=410.0, usage_pct=16.0)
    assert "primary-creator usage" in res_off.interpretation.lower() or "low-usage" in res_off.interpretation.lower()
    assert any("spacing" in lim.lower() for lim in res_off.limitations)

    res_def = engine.interpret_defensive_rating(drtg=92.0, minutes=220.0, possessions=410.0)
    assert "not be treated as a standalone individual defensive grade" in res_def.interpretation.lower()
    assert any("spatial tracking" in lim.lower() for lim in res_def.limitations)

# -----------------------------------------------------------------------------
# Test I: Percentile vs Stability Separation
# -----------------------------------------------------------------------------
def test_i_percentile_vs_stability_separation(engine, base_benchmark_meta):
    """Verifies that high percentile (100th) + small sample (EMERGING_SIGNAL) is a valid, distinct state."""
    stats = {
        "total_fg3m": 12, "total_fg3a": 25, "total_fga": 80,
        "fg3_pct": 48.0, "f3a_rate": 31.2, "gp": 8, "total_min": 120.0
    }
    pcts = {"fg3_pct": 100.0, "qualified_pop_size": 34}
    meds = {"fg3_pct": 25.0}
    res = engine.interpret_perimeter_shooting(stats, pcts, meds, base_benchmark_meta)

    # Must be 100th percentile BUT emerging signal
    assert res.context["percentile"] == 100.0
    assert res.stability_tier == StabilityTier.EMERGING_SIGNAL.value
    assert "emerging" in res.interpretation.lower()

# -----------------------------------------------------------------------------
# Test J: Missing Context Handling Without Fabrication
# -----------------------------------------------------------------------------
def test_j_missing_context_handling_without_fabrication(engine, base_benchmark_meta):
    """Verifies that when tracking metrics (usage, shot quality) are absent, they are acknowledged in limitations, not fabricated."""
    stats = {
        "total_pts": 100, "pts_per_40": 15.0, "ppg": 10.0, "total_min": 266.0,
        "total_fga": 90, "total_fta": 25, "ts_pct": 49.5, "gp": 10
    }
    pcts = {"pts_per_40": 50.0, "ts_pct": 50.0, "qualified_pop_size": 34}
    meds = {"pts_per_40": 16.9, "ts_pct": 49.1}
    res = engine.interpret_scoring(stats, pcts, meds, base_benchmark_meta)

    # Verify no fake usage value exists in observation
    assert "usage_pct" not in res.observation
    assert any("usage rate is estimated" in lim.lower() for lim in res.limitations)

# -----------------------------------------------------------------------------
# Test K: Determinism
# -----------------------------------------------------------------------------
def test_k_engine_determinism(engine, base_benchmark_meta):
    """Verifies that identical input data produces mathematically identical structured interpretations."""
    stats = {
        "total_pts": 254, "pts_per_40": 23.8, "ppg": 12.1, "total_min": 426.1,
        "total_fga": 188, "total_fta": 43, "ts_pct": 60.0, "gp": 21
    }
    pcts = {"pts_per_40": 82.4, "ts_pct": 85.3, "qualified_pop_size": 34}
    meds = {"pts_per_40": 16.9, "ts_pct": 49.1}

    res1 = engine.interpret_scoring(stats, pcts, meds, base_benchmark_meta)
    res2 = engine.interpret_scoring(stats, pcts, meds, base_benchmark_meta)

    assert res1.headline == res2.headline
    assert res1.interpretation == res2.interpretation
    assert res1.stability_tier == res2.stability_tier
    assert res1.limitations == res2.limitations
    assert res1.film_questions == res2.film_questions

# -----------------------------------------------------------------------------
# Test L: Complete Evidence Hierarchy
# -----------------------------------------------------------------------------
def test_l_complete_evidence_hierarchy(engine, base_benchmark_meta):
    """Verifies that every generated interpretation satisfies the complete evidence schema."""
    stats = {
        "total_pts": 297, "pts_per_40": 25.0, "ppg": 15.6, "total_min": 474.9,
        "total_fga": 215, "total_fta": 47, "ts_pct": 64.0, "gp": 19,
        "total_fg3m": 23, "total_fg3a": 47, "fg3_pct": 48.9, "f3a_rate": 21.9,
        "total_trb": 99, "total_orb": 25, "total_drb": 74, "rpg": 5.2, "reb_per_40": 8.3,
        "total_ast": 57, "total_tov": 56, "apg": 3.0, "ast_per_40": 4.8, "ast_to_tov": 1.02
    }
    pcts = {
        "pts_per_40": 85.3, "ts_pct": 94.1, "fg3_pct": 100.0,
        "reb_per_40": 50.0, "ast_per_40": 79.4, "ast_to_tov": 70.6,
        "qualified_pop_size": 34
    }
    meds = {
        "pts_per_40": 16.9, "ts_pct": 49.1, "fg3_pct": 25.0,
        "reb_per_40": 8.4, "ast_per_40": 3.5, "ast_to_tov": 0.8
    }

    findings = engine.generate_player_dossier_findings(stats, pcts, meds, base_benchmark_meta)
    assert len(findings) >= 3

    for f in findings:
        assert "category" in f
        assert "headline" in f
        assert "observation" in f
        assert "context" in f
        assert "volume_note" in f
        assert "interpretation" in f
        assert "stability_tier" in f
        assert "film_question" in f
        assert f["stability_tier"] in [tier.value for tier in StabilityTier]
        assert len(f["observation"]) > 10
        assert len(f["context"]) > 10
        assert len(f["interpretation"]) > 10
        assert len(f["film_question"]) > 10
