"""Automated test suite for Phase 5 Intelligence Datasets & Hypothesis Registries."""

from pathlib import Path
import pandas as pd
import pytest

DERIVED_DIR = Path("data/derived")
DOCS_DIR = Path("docs")

def test_team_intelligence_dataset():
    """Verify team_intelligence.parquet has both TEAM_SEASON and TEAM_GAME records."""
    p_path = DERIVED_DIR / "team_intelligence.parquet"
    assert p_path.exists()
    df_ti = pd.read_parquet(p_path)
    assert len(df_ti) >= 100
    assert set(df_ti["record_level"]) == {"TEAM_SEASON", "TEAM_GAME"}
    assert "ortg" in df_ti.columns and "drtg" in df_ti.columns and "net_rtg" in df_ti.columns

def test_shot_intelligence_dataset():
    """Verify shot_intelligence.parquet spatial zones and expected points."""
    p_path = DERIVED_DIR / "shot_intelligence.parquet"
    assert p_path.exists()
    df_si = pd.read_parquet(p_path)
    assert len(df_si) >= 5000
    assert "shot_zone" in df_si.columns and "expected_points" in df_si.columns
    assert set(df_si["shot_zone"]).issubset({
        "RESTRICTED_AREA", "PAINT_NON_RA", "MID_RANGE", "CORNER_3PT", "ABOVE_THE_BREAK_3PT", "UNKNOWN_ZONE"
    })

def test_coach_intelligence_findings_and_hypotheses():
    """Verify coach findings and hypotheses exist and are evidence-linked."""
    p_cif = DERIVED_DIR / "coach_intelligence_findings.parquet"
    p_hyp = DERIVED_DIR / "coach_hypotheses.parquet"
    assert p_cif.exists() and p_hyp.exists()
    
    df_cif = pd.read_parquet(p_cif)
    df_hyp = pd.read_parquet(p_hyp)
    assert len(df_cif) >= 5
    assert len(df_hyp) >= 3
    
    assert "evidence_game_ids" in df_cif.columns
    assert "video_verification_required" in df_hyp.columns

def test_phase5_documentation_deliverables_exist():
    """Verify presence of all required Phase 5 documentation files."""
    required_docs = [
        "PHASE5_PRE_INTERFACE_MATHEMATICAL_AUDIT.md",
        "player_trend_methodology.md",
        "coach_intelligence_methodology.md",
        "coach_interface_methodology.md",
        "evidence_navigation.md",
        "incremental_update_architecture.md",
        "statistical_safeguards.md",
        "PHASE5_FINAL_REPORT.md",
    ]
    for doc in required_docs:
        p = DOCS_DIR / doc
        assert p.exists(), f"Missing document: {doc}"
