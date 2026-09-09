"""Automated test suite for Phase 4 Coach Summary, Evidence Trail & Hypothesis Registry."""

from pathlib import Path
import pandas as pd
import pytest

DERIVED_DIR = Path("data/derived")
DOCS_DIR = Path("docs")

def test_coach_findings_hierarchy():
    """Verify coach_findings.parquet exists and implements 3-level communication model."""
    df_fnd = pd.read_parquet(DERIVED_DIR / "coach_findings.parquet")
    assert len(df_fnd) >= 5
    
    expected_cols = [
        "finding_id", "title", "executive_summary", "explanation", "affected_entity",
        "metric_name", "raw_value", "league_median", "percentile_rank", "epistemic_class",
        "evidence_strength", "source_games", "source_table"
    ]
    for c in expected_cols:
        assert c in df_fnd.columns, f"Missing column {c} in coach_findings"

def test_finding_evidence_traceability():
    """Verify finding_evidence.parquet connects findings to underlying tables and methods."""
    df_evi = pd.read_parquet(DERIVED_DIR / "finding_evidence.parquet")
    assert len(df_evi) >= 5
    
    expected_cols = [
        "finding_id", "claim", "population", "metric", "sample_size_N",
        "source_tables", "source_games", "statistical_method", "epistemic_class"
    ]
    for c in expected_cols:
        assert c in df_evi.columns, f"Missing column {c} in finding_evidence"

def test_hypotheses_registry():
    """Verify hypotheses.parquet exists and separates hypotheses from confirmed facts."""
    df_hyp = pd.read_parquet(DERIVED_DIR / "hypotheses.parquet")
    assert len(df_hyp) >= 3
    
    expected_cols = [
        "hypothesis_id", "hypothesis", "supporting_observations",
        "contradicting_observations", "evidence_strength", "status"
    ]
    for c in expected_cols:
        assert c in df_hyp.columns, f"Missing column {c} in hypotheses"

def test_documentation_deliverables_exist():
    """Verify all 6 Phase 4 documentation files exist."""
    assert (DOCS_DIR / "PHASE4_STATISTICAL_ANALYSIS.md").exists()
    assert (DOCS_DIR / "coach_reporting_methodology.md").exists()
    assert (DOCS_DIR / "evidence_traceability.md").exists()
    assert (DOCS_DIR / "statistical_results_methodology.md").exists()
    assert (DOCS_DIR / "player_evolution_methodology.md").exists()
    assert (DOCS_DIR / "phase4_data_quality_report.md").exists()
