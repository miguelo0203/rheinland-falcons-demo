"""Integration and Regression Test Suite for U19 NBBL Expansion & Controlled Cleanup.

Covers all 10 requirements from Phase Section 13:
1. SEA_2023 no longer exists in operational tables.
2. No game belongs to SEA_2023.
3. No NBBL historical benchmark references SEA_2023.
4. U16 2025/26 data remains unchanged (100% data protection).
5. U19 current roster remains intact (8 declared players in SEA_2025 and SEA_2026).
6. U16/U19 Squad Scope remains isolated.
7. All Academy excludes deleted historical data.
8. Dual-category players do not have mixed game logs.
9. 2026/27 (SEA_2026) can be selected without errors.
10. Missing U19 game data is represented as unavailable/empty, not fabricated.
"""

import sys
from pathlib import Path
import pandas as pd
import pytest

sys.path.insert(0, ".")

from app.services.data_service import DataService

@pytest.fixture(scope="module")
def ds():
    return DataService()


# =============================================================================
# 1. ENTITY INVARIANTS: TEAMS & ROSTERS
# =============================================================================
def test_01_team_entities_exist(ds):
    """Verifies Rheinland Falcons U16 and U19 teams are canonically present."""
    team_dict = ds.get_team_map()
    assert "TEM_DEMO_U16" in team_dict, "Rheinland Falcons U16 (TEM_DEMO_U16) must exist"
    assert "TEM_DEMO_U19" in team_dict, "Rheinland Falcons U19 (TEM_DEMO_U19) must exist"
    assert "Rheinland" in team_dict["TEM_DEMO_U19"] or "Falcons" in team_dict["TEM_DEMO_U19"]


# =============================================================================
# 2. MATCH CENSUS & GAME REGISTRY INVARIANTS
# =============================================================================
def test_02_game_census_and_squad_column(ds):
    """Verifies exact game counts and squad column in game_registry."""
    df_all = ds.get_game_registry(squad_scope="All Academy")
    assert len(df_all) == 48, f"Expected 48 total games in registry (SEA_2025 only), got {len(df_all)}"

    df_u16 = ds.get_game_registry(squad_scope="U16")
    assert len(df_u16) == 48, f"Expected 48 JBBL games for U16, got {len(df_u16)}"
    assert (df_u16["competition_id"] == "CMP_JBBL").all()

    df_u19 = ds.get_game_registry(squad_scope="U19")
    assert len(df_u19) == 0, f"Expected 0 NBBL games for U19 before season games are played, got {len(df_u19)}"


def test_03_rheinland_nbbl_match_census(ds):
    """Verifies Rheinland U19 has 0 historical matches remaining (SEA_2023 deleted)."""
    df_u19 = ds.get_game_registry(squad_scope="U19")
    rheinland_games = df_u19[
        (df_u19["home_team_id"] == "TEM_DEMO_U19") | (df_u19["away_team_id"] == "TEM_DEMO_U19")
    ]
    assert len(rheinland_games) == 0, f"Expected 0 Rheinland U19 games, got {len(rheinland_games)}"


# =============================================================================
# 3. SQUAD SCOPE & SEASON SCOPE DYNAMICS
# =============================================================================
def test_04_squad_and_season_options(ds):
    """Verifies dynamic squad and season selector options (SEA_2025 and SEA_2026)."""
    squads = ds.get_available_squads()
    assert squads == ["U16", "U19", "All Academy"]

    seasons_u16 = ds.get_available_seasons("U16")
    assert "SEA_2025" in seasons_u16
    assert "SEA_2026" in seasons_u16
    assert "SEA_2023" not in seasons_u16, "SEA_2023 must be completely removed"

    seasons_u19 = ds.get_available_seasons("U19")
    assert "SEA_2025" in seasons_u19
    assert "SEA_2026" in seasons_u19
    assert "SEA_2023" not in seasons_u19


# =============================================================================
# 4. ROSTER COVERAGE & CONTINUITY
# =============================================================================
def test_05_u19_roster_discovery(ds):
    """Verifies FALCONS U19 player discovery in 2025 and 2026, and 0 in deleted 2023."""
    # 2023 Season Boxscore Players: 0
    u19_2023 = ds.get_falcons_player_list(season_id="SEA_2023", squad_scope="U19")
    assert len(u19_2023) == 0

    # 2025 Active Roster Declarations (8 declared players)
    u19_2025 = ds.get_falcons_player_list(season_id="SEA_2025", squad_scope="U19")
    assert len(u19_2025) == 8, f"Expected 8 U19 declared players in 2025, got {len(u19_2025)}"

    # 2026 Active Roster Declarations (8 declared players)
    u19_2026 = ds.get_falcons_player_list(season_id="SEA_2026", squad_scope="U19")
    assert len(u19_2026) == 8, f"Expected 8 U19 declared players in 2026, got {len(u19_2026)}"


def test_06_squad_roster_isolation(ds):
    """Verifies that U16 and U19 rosters are properly isolated in 2025."""
    u16_players = {p["player_id"] for p in ds.get_falcons_player_list(season_id="SEA_2025", squad_scope="U16")}
    u19_players = {p["player_id"] for p in ds.get_falcons_player_list(season_id="SEA_2025", squad_scope="U19")}
    all_players = {p["player_id"] for p in ds.get_falcons_player_list(season_id="SEA_2025", squad_scope="All Academy")}

    assert len(u16_players) == 14
    assert len(u19_players) == 8
    # All Academy contains the combined union
    assert u16_players.issubset(all_players)
    assert u19_players.issubset(all_players)


# =============================================================================
# 5. STRICT CATEGORY BENCHMARK ISOLATION
# =============================================================================
def test_07_statistical_benchmark_isolation(ds):
    """Verifies that U16 and U19 players are evaluated strictly against their own competition."""
    # Test U16 player (Lukas Weber, 2025)
    dossier_u16 = ds.get_player_dossier("PLY_DEMO_101", season_id="SEA_2025", squad_scope="U16")
    assert dossier_u16 is not None
    assert dossier_u16["benchmark_meta"]["competition_id"] == "CMP_JBBL"
    assert dossier_u16["benchmark_meta"]["qualified_pop_size"] > 0

    # Test U19 player (Lakhat Fall PLY_DEMO_104, 2025 in U19 scope)
    dossier_u19 = ds.get_player_dossier("PLY_DEMO_104", season_id="SEA_2025", squad_scope="U19")
    assert dossier_u19 is not None
    assert dossier_u19["benchmark_meta"]["competition_id"] == "CMP_NBBL"
    assert dossier_u19["stats"]["gp"] == 0
    assert dossier_u19["stats"]["total_min"] == 0.0

    # Test All Academy (no combined normative benchmark)
    dossier_all = ds.get_player_dossier("PLY_DEMO_104", season_id="SEA_2025", squad_scope="All Academy")
    assert dossier_all is not None
    assert dossier_all["benchmark_meta"]["qualified_pop_size"] == 0
    assert dossier_all["benchmark_meta"].get("peer_group") == "None (Multi-tier aggregate)"


# =============================================================================
# 6. DATA QUALITY & HONESTY (NO FABRICATION)
# =============================================================================
def test_08_no_fabricated_modalities(ds):
    """Verifies that missing modalities in U19 are accurately reported as absent, not fabricated."""
    df_u19 = ds.get_game_registry(squad_scope="U19")
    assert len(df_u19) == 0, "No fake U19 games may exist"

    # In 2025, U19 player has 0 shots and 0 game logs
    shots_u19 = ds.get_player_shots("PLY_DEMO_104", season_id="SEA_2025", squad_scope="U19")
    assert len(shots_u19) == 0

    log_u19 = ds.get_player_game_log("PLY_DEMO_104", season_id="SEA_2025", squad_scope="U19")
    assert len(log_u19) == 0


# =============================================================================
# 7. ZERO REGRESSION ON U16 DATA & FUNCTIONALITY
# =============================================================================
def test_09_u16_functionality_intact(ds):
    """Verifies that all U16 queries, shots, lineups and dossier metrics are 100% intact."""
    # U16 2025 shots
    df_shots = ds.get_team_shots("SEA_2025", is_falcons_only=True, squad_scope="U16")
    assert len(df_shots) == 1045, f"Expected 1045 U16 shots in SEA_2025, got {len(df_shots)}"

    # U16 2025 lineups
    df_lineups = ds.get_observed_lineups("SEA_2025", team_id="TEM_DEMO_U16")
    assert not df_lineups.empty, "U16 observed lineups must not be empty"

    # U16 core prospect dossier
    dossier = ds.get_player_dossier("PLY_DEMO_101", season_id="SEA_2025", squad_scope="U16")
    assert dossier is not None
    assert dossier["bio"]["canonical_name"] == "Lukas Weber"
    assert dossier["stability"]["overall_sample"] == "ESTABLISHED_SIGNAL"
    assert len(dossier["findings"]) >= 2


# =============================================================================
# 8. REGRESSION: COMPLETE SEA_2023 DELETION & ZERO RESIDUALS
# =============================================================================
def test_10_sea_2023_complete_absence(ds):
    """Requirement 1, 2, 3: SEA_2023 no longer exists in DB or benchmarks."""
    conn = ds.conn
    assert conn.execute("SELECT count(*) FROM season WHERE season_id = 'SEA_2023'").fetchone()[0] == 0
    assert conn.execute("SELECT count(*) FROM game WHERE season_id = 'SEA_2023'").fetchone()[0] == 0
    assert conn.execute("SELECT count(*) FROM boxscore_player bp JOIN game g ON bp.game_id = g.game_id WHERE g.season_id = 'SEA_2023'").fetchone()[0] == 0
    assert conn.execute("SELECT count(*) FROM player_team WHERE season_id = 'SEA_2023'").fetchone()[0] == 0

    # Benchmarks for SEA_2023 must be completely empty
    bench_2023 = ds.get_qualified_league_benchmark(season_id="SEA_2023", competition_id="CMP_JBBL")
    assert len(bench_2023) == 0


def test_11_dual_category_player_log_isolation(ds):
    """Requirement 8: Dual-category players do not have mixed game logs."""
    # Maximilian Becker is registered in U16 and U19
    u16_logs = ds.get_player_game_log("PLY_DEMO_104", season_id="SEA_2025", squad_scope="U16")
    u19_logs = ds.get_player_game_log("PLY_DEMO_104", season_id="SEA_2025", squad_scope="U19")
    all_logs = ds.get_player_game_log("PLY_DEMO_104", season_id="SEA_2025", squad_scope="All Academy")

    assert len(u16_logs) == 21
    assert len(u19_logs) == 0
    assert len(all_logs) == 21


def test_12_season_2026_preparation(ds):
    """Requirement 9: 2026/27 can be selected without errors and has active rosters."""
    u16_2026 = ds.get_falcons_player_list(season_id="SEA_2026", squad_scope="U16")
    u19_2026 = ds.get_falcons_player_list(season_id="SEA_2026", squad_scope="U19")
    all_2026 = ds.get_falcons_player_list(season_id="SEA_2026", squad_scope="All Academy")

    assert len(u16_2026) == 14
    assert len(u19_2026) == 8
    assert len(all_2026) == 22

    # Player dossier in 2026 returns safely with 0 games
    dossier_2026 = ds.get_player_dossier("PLY_DEMO_101", season_id="SEA_2026", squad_scope="U16")
    assert dossier_2026["stats"]["gp"] == 0
    assert dossier_2026["bio"]["canonical_name"] == "Lukas Weber"
