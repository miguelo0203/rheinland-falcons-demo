"""Unit tests for Validation Rules and Reconcilers in Sandbox."""

from datetime import date
import pytest

from python.models.canonical import BoxscorePlayer, BoxscoreTeam, Game, PBPEvent
from python.models.enums import ValidationSeverity, EventType, PeriodType
from python.validation.rules import (
    DistinctTeamsRule,
    NonNegativeScoresRule,
    NonNegativePlayerStatsRule,
    ShootingBoundsRule,
    PlayingTimeLimitRule,
)
from python.validation.reconcilers import BoxscoreReconciler, PBPReconciler
from python.validation.engine import ValidationEngine


def test_distinct_teams_rule():
    rule = DistinctTeamsRule()
    
    # Valid
    game_ok = Game(
        game_id="GAM_001",
        season_id="SEA_001",
        competition_id="CMP_001",
        game_date=date.today(),
        home_team_id="TEM_HOME",
        away_team_id="TEM_AWAY",
    )
    res_ok = rule.evaluate({"game": game_ok})
    assert res_ok.passed is True

    # Invalid
    game_bad = Game(
        game_id="GAM_002",
        season_id="SEA_001",
        competition_id="CMP_001",
        game_date=date.today(),
        home_team_id="TEM_SAME",
        away_team_id="TEM_SAME",
    )
    res_bad = rule.evaluate({"game": game_bad})
    assert res_bad.passed is False
    assert res_bad.severity == ValidationSeverity.CRITICAL


def test_shooting_bounds_rule():
    rule = ShootingBoundsRule()
    # Violation: made 10 out of 8 attempts
    bad_player = BoxscorePlayer(
        boxscore_player_id="BXP_001",
        game_id="GAM_001",
        team_id="TEM_001",
        player_id="PLY_001",
        points=20,
        fgm=10,
        fga=8,
        provenance_id="PRV_001",
    )
    res = rule.evaluate({"boxscore_players": [bad_player]})
    assert res.passed is False
    assert res.severity == ValidationSeverity.ERROR


def test_boxscore_points_reconciliation():
    team = BoxscoreTeam(
        boxscore_team_id="BXT_001",
        game_id="GAM_001",
        team_id="TEM_001",
        is_home=True,
        points=50,
        provenance_id="PRV_001",
    )
    p1 = BoxscorePlayer(
        boxscore_player_id="BXP_001",
        game_id="GAM_001",
        team_id="TEM_001",
        player_id="PLY_001",
        points=30,
        provenance_id="PRV_001",
    )
    p2 = BoxscorePlayer(
        boxscore_player_id="BXP_002",
        game_id="GAM_001",
        team_id="TEM_001",
        player_id="PLY_002",
        points=20,
        provenance_id="PRV_001",
    )

    results = BoxscoreReconciler.reconcile_points(None, [team], [p1, p2])
    assert len(results) == 1
    assert results[0].passed is True


def test_clock_monotonicity():
    events = [
        PBPEvent(
            event_id="EVT_1",
            game_id="GAM_1",
            period=1,
            period_type=PeriodType.REGULAR,
            clock_display="10:00",
            game_seconds_remaining=2400.0,
            period_seconds_remaining=600.0,
            event_index=0,
            event_type=EventType.PERIOD_START,
            home_score=0,
            away_score=0,
            score_margin=0,
            provenance_id="PRV_1",
        ),
        PBPEvent(
            event_id="EVT_2",
            game_id="GAM_1",
            period=1,
            period_type=PeriodType.REGULAR,
            clock_display="09:50",
            game_seconds_remaining=2390.0,
            period_seconds_remaining=590.0,
            event_index=1,
            event_type=EventType.SHOT,
            home_score=2,
            away_score=0,
            score_margin=2,
            provenance_id="PRV_1",
        ),
    ]
    res = PBPReconciler.check_clock_monotonicity(events)
    assert res.passed is True
