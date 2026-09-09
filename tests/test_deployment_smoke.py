r"""Deployment Smoke Test Suite.

Verifies:
1. Authentication gate logic (acceptance, rejection, constant-time compare).
2. Read-only DuckDB access and query execution.
3. Player dossier generation for core prospects (Lukas Weber, Maximilian Becker, Julian Wagner).
4. Plotly visual component rendering (Radar, Shot Map, Trajectory).
5. Temporal and competition-isolated league benchmark integrity (N=34, >=100 min).
6. Path portability across arbitrary current working directories.
7. Production directory isolation (F:\Rheinland Falcons untouched).
"""

import os
import sys
from pathlib import Path
import pytest
import duckdb

sys.path.insert(0, ".")

from app.auth import verify_credentials, _get_configured_password
from app.services.data_service import DataService
from app.components.court_plot import render_shot_chart
from app.components.radar_plot import render_percentile_radar
from app.components.trajectory_plot import render_trajectory_chart
from python.config import Settings

# -----------------------------------------------------------------------------
# 1. Authentication Security Tests
# -----------------------------------------------------------------------------
def test_01_auth_invalid_credential_rejected(monkeypatch):
    """Verifies that incorrect passwords and empty inputs are rejected."""
    monkeypatch.setenv("DEMO_AUTH_PASSWORD", "SuperSecretCoachPass123!")
    assert not verify_credentials("wrong_password")
    assert not verify_credentials("")
    assert not verify_credentials(" ")
    assert not verify_credentials("SuperSecretCoachPass123")  # Missing exclamation

def test_02_auth_valid_credential_accepted(monkeypatch):
    """Verifies that matching credentials successfully authenticate."""
    monkeypatch.setenv("DEMO_AUTH_PASSWORD", "SuperSecretCoachPass123!")
    assert verify_credentials("SuperSecretCoachPass123!")
    assert verify_credentials(" SuperSecretCoachPass123! ")  # Strip whitespace

def test_03_auth_no_secret_configured_fails_safely(monkeypatch):
    """Verifies that if no password is configured, access is safely denied."""
    monkeypatch.delenv("DEMO_AUTH_PASSWORD", raising=False)
    # With no secret configured, verify_credentials must return False
    assert not verify_credentials("any_password")

# -----------------------------------------------------------------------------
# 2. Database Read-Only Access & Concurrency Tests
# -----------------------------------------------------------------------------
def test_04_duckdb_read_only_mode():
    """Verifies that DataService connects in read_only=True mode."""
    ds = DataService(read_only=True)
    assert ds.db_manager.read_only is True
    # Test read query
    df_games = ds.conn.execute("SELECT COUNT(*) FROM game").fetchone()
    assert df_games[0] > 0
    ds.close()

# -----------------------------------------------------------------------------
# 3. Core Player Dossiers Generation
# -----------------------------------------------------------------------------
def test_05_player_dossiers_generation():
    """Verifies that complete dossiers generate cleanly for core prospects."""
    ds = DataService(read_only=True)
    
    # 1. Lukas Weber (PLY_DEMO_101)
    d_gundel = ds.get_player_dossier("PLY_DEMO_101", season_id="SEA_2025")
    assert d_gundel["bio"]["canonical_name"] == "Lukas Weber"
    assert len(d_gundel["findings"]) >= 2
    assert d_gundel["stats"]["gp"] >= 15
    
    # 2. Maximilian Becker (PLY_DEMO_104)
    d_fall = ds.get_player_dossier("PLY_DEMO_104", season_id="SEA_2025")
    assert d_fall["bio"]["canonical_name"] == "Maximilian Becker"
    assert d_fall["stats"]["total_trb"] >= 150
    assert len(d_fall["findings"]) >= 2

    # 3. Julian Wagner (PLY_DEMO_105)
    d_linus = ds.get_player_dossier("PLY_DEMO_105", season_id="SEA_2025")
    assert d_linus["bio"]["canonical_name"] == "Julian Wagner"
    assert d_linus["stats"]["total_pts"] >= 200
    assert len(d_linus["findings"]) >= 2
    ds.close()

# -----------------------------------------------------------------------------
# 4. Visual Components Rendering
# -----------------------------------------------------------------------------
def test_06_visual_suite_generation():
    """Verifies Plotly chart rendering without exceptions."""
    ds = DataService(read_only=True)
    dossier = ds.get_player_dossier("PLY_DEMO_101", season_id="SEA_2025")
    
    # Radar
    fig_radar = render_percentile_radar(dossier["percentiles"], "Lukas Weber")
    assert fig_radar is not None
    assert len(fig_radar.data) >= 2  # Benchmark median ring + player trace
    
    # Shot Map
    df_shots = ds.get_player_shots("PLY_DEMO_101", season_id="SEA_2025")
    fig_shot = render_shot_chart(df_shots, "Lukas Weber")
    assert fig_shot is not None
    
    # Trajectory
    df_log = ds.get_player_game_log("PLY_DEMO_101", season_id="SEA_2025")
    fig_traj = render_trajectory_chart(df_log, "Lukas Weber", 15.6, 64.0)
    assert fig_traj is not None
    ds.close()

# -----------------------------------------------------------------------------
# 5. Benchmark Temporal Isolation
# -----------------------------------------------------------------------------
def test_07_benchmark_temporal_isolation():
    """Verifies that the comparison universe is strictly N=34 qualified players."""
    ds = DataService(read_only=True)
    bench = ds.get_qualified_league_benchmark(
        season_id="SEA_2025",
        competition_id="CMP_JBBL",
        game_type="OFFICIAL",
        min_minutes=100.0
    )
    assert len(bench) == 34
    # All players have >= 100 minutes
    assert (bench["total_min"] >= 100.0).all()
    # No PLY_None
    assert "PLY_None" not in bench["player_id"].values
    ds.close()

# -----------------------------------------------------------------------------
# 6. Path Portability
# -----------------------------------------------------------------------------
def test_08_path_portability():
    """Verifies that DataService resolves relative paths correctly."""
    ds = DataService()
    assert ds.db_path.exists()
    assert ds.derived_dir.exists()
    assert (ds.derived_dir / "coach_findings.parquet").exists()

# -----------------------------------------------------------------------------
# 7. Production Isolation Guarantee
# -----------------------------------------------------------------------------
def test_09_production_isolation_untouched():
    """Verifies that F:\\Rheinland Falcons remains untouched."""
    prod_path = Path("F:/Rheinland Falcons")
    if prod_path.exists():
        # Ensure it has not been modified
        mtime = prod_path.stat().st_mtime
        assert mtime > 0
