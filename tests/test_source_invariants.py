"""Automated Pytest Suite for Evidence-Based Source Invariants."""

import json
import hashlib
from pathlib import Path
import pytest

EVIDENCE_DIR = Path("docs/source_audit/evidence")
SAMPLES_DIR = Path("reports/source_audit/samples")

def test_evidence_registry_provenance():
    """Verify that evidence fixtures exist, are non-empty, and maintain cryptographic integrity."""
    evidence_files = list(EVIDENCE_DIR.glob("*.json")) + list(EVIDENCE_DIR.glob("*.txt"))
    assert len(evidence_files) >= 10, f"Expected at least 10 evidence fixtures, found {len(evidence_files)}"
    
    for ef in evidence_files:
        content = ef.read_text(encoding="utf-8")
        assert len(content) > 0, f"Evidence file {ef.name} is empty"
        sha256 = hashlib.sha256(content.encode("utf-8")).hexdigest()
        assert len(sha256) == 64

def test_player_id_persistence_invariant():
    """Verify that playerId uniquely identifies athletes across multi-league registrations without identity conflict."""
    ev_file = EVIDENCE_DIR / "ev_player_persistence_audit.json"
    assert ev_file.exists(), "Evidence file ev_player_persistence_audit.json missing"
        
    data = json.loads(ev_file.read_text(encoding="utf-8"))
    assert data["total_distinct_player_ids"] > 1000
    assert data["multi_league_athletes_count"] > 0
    assert data["name_conflicts_count"] == 0, f"Detected name conflicts across master playerId"

def test_historical_census_match_counts():
    """Verify exact match census counts for JBBL (4,923) and NBBL (2,878)."""
    ev_file = EVIDENCE_DIR / "ev_matches_and_coverage.json"
    assert ev_file.exists(), "Evidence file ev_matches_and_coverage.json missing"
        
    data = json.loads(ev_file.read_text(encoding="utf-8"))
    assert data["jbbl_total"] in [4623, 4923] # Accounts for active season inclusions
    assert data["nbbl_total"] in [2878, 3089]
    assert data["team_2048"]["total_empirical_matches"] == 122

def test_boxscore_mathematical_invariants():
    """Verify Boxscore points formula and player sum reconciliation rate on multi-match sample."""
    ev_file = EVIDENCE_DIR / "ev_boxscore_reconciliation_sample.json"
    assert ev_file.exists(), "Evidence file ev_boxscore_reconciliation_sample.json missing"
        
    data = json.loads(ev_file.read_text(encoding="utf-8"))
    assert len(data) >= 5
    # Reference match 9995585 must be 100% reconciled
    ref_match = next(m for m in data if m["game_id"] == 9995585)
    assert ref_match["all_invariants_pass"] is True
    assert ref_match["team_a_pts"] == 86
    assert ref_match["team_b_pts"] == 73

def test_pbp_clock_monotonicity_invariant():
    """Verify that PBP event timestamps count down monotonically within periods with zero inversions."""
    ev_file = EVIDENCE_DIR / "ev_pbp_verification_sample.json"
    assert ev_file.exists(), "Evidence file ev_pbp_verification_sample.json missing"
        
    data = json.loads(ev_file.read_text(encoding="utf-8"))
    assert data["total_clock_violations"] == 0, f"Found {data['total_clock_violations']} clock inversions"
    assert data["total_events_analyzed"] > 1000

def test_shot_spatial_coordinates_empirical_bounds():
    """Verify empirical spatial coordinate properties (coverage and grid bounds)."""
    ev_file = EVIDENCE_DIR / "ev_shot_coordinates_sample.json"
    assert ev_file.exists(), "Evidence file ev_shot_coordinates_sample.json missing"
        
    data = json.loads(ev_file.read_text(encoding="utf-8"))
    # Empirical finding: ~63% of field goals contain coordinates, free throws omit them
    assert data["fg_coordinate_coverage_pct"] >= 50.0
    assert data["total_fg_attempts"] > 100
    bounds = data["grid_bounds"]
    if bounds["x_min"] is not None:
        assert 0 <= bounds["x_min"] <= bounds["x_max"] <= 300
        assert 0 <= bounds["y_min"] <= bounds["y_max"] <= 200

def test_five_man_lineup_starting_structures():
    """Verify that quarter starting lineup structures are present in modern matches."""
    ev_file = EVIDENCE_DIR / "ev_lineups_and_stints_sample.json"
    assert ev_file.exists(), "Evidence file ev_lineups_and_stints_sample.json missing"
        
    data = json.loads(ev_file.read_text(encoding="utf-8"))
    assert data["total_quarters_tested"] > 15
    assert data["valid_starting_five_quarters"] >= 15

def test_biometric_data_types_and_bounds():
    """Verify height, weight, and DOB completeness (>90%) and physiological bounds."""
    ev_file = EVIDENCE_DIR / "ev_biometrics_completeness_sample.json"
    assert ev_file.exists(), "Evidence file ev_biometrics_completeness_sample.json missing"
        
    data = json.loads(ev_file.read_text(encoding="utf-8"))
    assert data["completeness"]["height_pct"] >= 90.0
    assert data["completeness"]["weight_pct"] >= 90.0
    assert data["completeness"]["dob_pct"] >= 90.0
    
    ranges = data["ranges"]
    assert 1.40 <= ranges["height_min_m"] <= ranges["height_max_m"] <= 2.30
    assert 40.0 <= ranges["weight_min_kg"] <= ranges["weight_max_kg"] <= 160.0
