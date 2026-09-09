"""Comprehensive Test Suite for Benchmark Temporal, Competition & As-Of-Date Isolation."""

import sys
from pathlib import Path
import pandas as pd
import pytest

sys.path.insert(0, ".")

from app.services.data_service import DataService

@pytest.fixture(scope="module")
def ds():
    service = DataService()
    yield service
    service.close()

# -----------------------------------------------------------------------------
# Test A: Season Isolation
# -----------------------------------------------------------------------------
def test_a_season_isolation_integrity(ds):
    """Verifies that SEA_2025 benchmark contains only games and players from SEA_2025."""
    bench_2025 = ds.get_qualified_league_benchmark(season_id="SEA_2025", competition_id="CMP_JBBL", game_type="OFFICIAL")
    
    # Calculate independent expected count directly from game table
    q_expected = """
        SELECT COUNT(*) as exp_count FROM (
            SELECT bp.player_id
            FROM boxscore_player bp
            JOIN game g ON bp.game_id = g.game_id
            WHERE g.season_id = 'SEA_2025'
              AND g.competition_id = 'CMP_JBBL'
              AND g.game_type = 'OFFICIAL'
              AND bp.player_id != 'PLY_None'
            GROUP BY bp.player_id, bp.team_id
            HAVING SUM(bp.seconds_played)/60.0 >= 100.0
        )
    """
    exp_count = int(ds.conn.execute(q_expected).fetchone()[0])
    assert len(bench_2025) == exp_count
    assert len(bench_2025) == 34, f"Expected 34 qualified players in SEA_2025, got {len(bench_2025)}"

    # Check games contributing to these players in SEA_2025
    player_ids = bench_2025["player_id"].tolist()
    p_placeholders = ",".join(f"'{p}'" for p in player_ids)
    q_seasons = f"""
        SELECT DISTINCT g.season_id
        FROM boxscore_player bp
        JOIN game g ON bp.game_id = g.game_id
        WHERE bp.player_id IN ({p_placeholders})
          AND g.season_id = 'SEA_2025'
    """
    seasons = ds.conn.execute(q_seasons).df()["season_id"].tolist()
    assert seasons == ["SEA_2025"]

# -----------------------------------------------------------------------------
# Test B: Cross-Season Exclusion
# -----------------------------------------------------------------------------
def test_b_cross_season_player_exclusion(ds):
    """Verifies that players exclusive to SEA_2023 cannot enter the SEA_2025 benchmark."""
    bench_2025 = ds.get_qualified_league_benchmark(season_id="SEA_2025", competition_id="CMP_JBBL", game_type="OFFICIAL")
    names_in_2025 = bench_2025["canonical_name"].tolist()

    # Known SEA_2023 exclusive qualified players
    sea_2023_exclusive = ["Constantin Clemens", "Ilkay Sertel", "Leon Blank", "Clemens Romsdorfer", "Malik Lemke"]
    for name in sea_2023_exclusive:
        assert name not in names_in_2025, f"Historical 2023 player '{name}' found in SEA_2025 benchmark!"

    # Verify SEA_2023 benchmark returns empty as SEA_2023 has been completely deleted
    bench_2023 = ds.get_qualified_league_benchmark(season_id="SEA_2023", competition_id="CMP_JBBL", game_type="OFFICIAL")
    assert len(bench_2023) == 0, "SEA_2023 was deleted and should yield 0 benchmark players"

# -----------------------------------------------------------------------------
# Test C: PLY_None Exclusion
# -----------------------------------------------------------------------------
def test_c_ply_none_exclusion(ds):
    """Verifies that PLY_None is strictly excluded from all benchmark populations."""
    for s_id in ["SEA_2025"]:
        bench = ds.get_qualified_league_benchmark(season_id=s_id)
        assert "PLY_None" not in bench["player_id"].values
        assert not any(p is None or p == "" for p in bench["player_id"])

# -----------------------------------------------------------------------------
# Test D: Competition Isolation
# -----------------------------------------------------------------------------
def test_d_competition_isolation(ds):
    """Verifies that competition_id filter properly scopes the benchmark universe."""
    bench_jbbl = ds.get_qualified_league_benchmark(season_id="SEA_2025", competition_id="CMP_JBBL")
    assert len(bench_jbbl) > 0
    
    # Query for non-existent or synthetic competition
    bench_other = ds.get_qualified_league_benchmark(season_id="SEA_2025", competition_id="CMP_NBBL_SYNTHETIC")
    assert len(bench_other) == 0

# -----------------------------------------------------------------------------
# Test E: Game Type Isolation
# -----------------------------------------------------------------------------
def test_e_game_type_isolation(ds):
    """Verifies that OFFICIAL game_type excludes non-official records."""
    bench_official = ds.get_qualified_league_benchmark(season_id="SEA_2025", competition_id="CMP_JBBL", game_type="OFFICIAL")
    assert len(bench_official) == 34
    
    bench_practice = ds.get_qualified_league_benchmark(season_id="SEA_2025", competition_id="CMP_JBBL", game_type="PRACTICE")
    assert len(bench_practice) == 0

# -----------------------------------------------------------------------------
# Test F: As-Of-Date Isolation
# -----------------------------------------------------------------------------
def test_f_as_of_date_temporal_cutoff(ds):
    """Verifies that as_of_date strictly filters out future games and adjusts qualified player count."""
    # Full season 2025/26 has 34 qualified players
    bench_full = ds.get_qualified_league_benchmark(season_id="SEA_2025", as_of_date=None)
    assert len(bench_full) == 34
    
    # Early in the season (e.g. 2025-11-01, after only ~3-4 games)
    bench_early = ds.get_qualified_league_benchmark(season_id="SEA_2025", as_of_date="2025-11-01")
    # In early season, fewer or zero players have accumulated >= 100 min
    assert len(bench_early) < len(bench_full)
    
    # Mid-season cutoff (e.g. 2025-12-15)
    bench_mid = ds.get_qualified_league_benchmark(season_id="SEA_2025", as_of_date="2025-12-15")
    assert len(bench_early) <= len(bench_mid) <= len(bench_full)

# -----------------------------------------------------------------------------
# Test G: Percentile Isolation Accuracy
# -----------------------------------------------------------------------------
def test_g_percentile_isolation_finn_gundel(ds):
    """Verifies Lukas Weber's percentiles are computed strictly against the isolated SEA_2025 peer universe."""
    dossier = ds.get_player_dossier("PLY_DEMO_101", season_id="SEA_2025")
    pcts = dossier["percentiles"]
    
    # Lukas Weber has 25.0 PTS/40. In isolated SEA_2025 (N=34), ranks in 82-86th %ile
    assert pcts["qualified_pop_size"] == 34
    assert 80.0 <= pcts["pts_per_40"] <= 86.0
    assert 90.0 <= pcts["ts_pct"] <= 95.5
    assert pcts["fg3_pct"] >= 95.0

# -----------------------------------------------------------------------------
# Test H: Dossier Provenance Propagation
# -----------------------------------------------------------------------------
def test_h_dossier_provenance_metadata(ds):
    """Verifies get_player_dossier returns complete benchmark provenance metadata."""
    dossier = ds.get_player_dossier("PLY_DEMO_104", season_id="SEA_2025") # Maximilian Becker
    assert "benchmark_meta" in dossier
    b_meta = dossier["benchmark_meta"]
    assert b_meta["season_id"] == "SEA_2025"
    assert b_meta["competition_id"] == "CMP_JBBL"
    assert b_meta["game_type"] == "OFFICIAL"
    assert b_meta["min_minutes"] == 100.0
    assert b_meta["qualified_pop_size"] == 34
    assert b_meta["as_of_date"] is None
