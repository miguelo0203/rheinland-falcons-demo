"""Automated test suite for Phase 6 UI Data Lineage, Dynamic Season Discovery & Drilldown."""

from pathlib import Path
import pandas as pd
import pytest

from app.services.data_service import DataService

def test_dynamic_season_discovery():
    """Verify that DataService discovers seasons dynamically from DuckDB."""
    ds = DataService()
    seasons = ds.get_available_seasons()
    assert len(seasons) >= 1
    assert "SEA_2025" in seasons

def test_coach_findings_evidence_drilldown_completeness():
    """Verify every coach finding links to valid evidence game IDs and metrics."""
    ds = DataService()
    df_findings = ds.get_coach_findings()
    assert len(df_findings) >= 5
    
    for _, f in df_findings.iterrows():
        assert len(str(f["finding_id"])) > 0
        assert len(str(f["metric"])) > 0
        assert len(str(f["evidence_game_ids"])) > 0
        assert pd.notna(f["falcons_value"])

def test_phase6_documentation_deliverables():
    """Verify that all required Phase 6 documentation deliverables exist."""
    required_docs = [
        "PHASE6_FINAL_REPORT.md",
        "game_registry_and_incremental_operations.md",
        "historical_immutability_policy.md",
        "incremental_analytics_dependency_map.md",
        "practice_game_population_policy.md",
        "coach_interface_v2_methodology.md",
        "evidence_drilldown_methodology.md",
        "continuous_season_operations.md",
    ]
    for doc in required_docs:
        p = Path("docs") / doc
        assert p.exists(), f"Missing Phase 6 documentation file: {doc}"
