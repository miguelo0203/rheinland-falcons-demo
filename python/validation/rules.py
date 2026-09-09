"""Validation Rules Definitions and Results Models."""

import json
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel

from python.models.canonical import (
    BoxscorePlayer,
    BoxscoreTeam,
    Game,
    ValidationLog,
)
from python.models.enums import ValidationSeverity
from python.ingestion.provenance import generate_id


class ValidationResult(BaseModel):
    rule_id: str
    rule_category: str
    severity: ValidationSeverity
    passed: bool
    message: str
    details: Optional[Dict[str, Any]] = None

    def to_log_model(self, game_id: str) -> ValidationLog:
        return ValidationLog(
            validation_id=generate_id("VAL"),
            game_id=game_id,
            rule_id=self.rule_id,
            rule_category=self.rule_category,
            severity=self.severity,
            status="PASSED" if self.passed else "FAILED",
            message=self.message,
            details_json=json.dumps(self.details) if self.details else None,
        )


class BaseRule(ABC):
    """Base class for an individual validation rule."""
    rule_id: str
    rule_category: str
    severity: ValidationSeverity
    description: str

    @abstractmethod
    def evaluate(self, context: Dict[str, Any]) -> ValidationResult:
        pass


class DistinctTeamsRule(BaseRule):
    rule_id = "RULE_GAM_001"
    rule_category = "GAME_LEVEL"
    severity = ValidationSeverity.CRITICAL
    description = "Home team and away team must be distinct."

    def evaluate(self, context: Dict[str, Any]) -> ValidationResult:
        game: Optional[Game] = context.get("game")
        if not game:
            return ValidationResult(
                rule_id=self.rule_id,
                rule_category=self.rule_category,
                severity=self.severity,
                passed=True,
                message="No game record in context (skipped).",
            )
        passed = game.home_team_id != game.away_team_id
        msg = "Home and away teams are distinct." if passed else f"Home team equals away team: {game.home_team_id}"
        return ValidationResult(
            rule_id=self.rule_id,
            rule_category=self.rule_category,
            severity=self.severity,
            passed=passed,
            message=msg,
            details={"home_team_id": game.home_team_id, "away_team_id": game.away_team_id},
        )


class NonNegativeScoresRule(BaseRule):
    rule_id = "RULE_GAM_004"
    rule_category = "GAME_LEVEL"
    severity = ValidationSeverity.CRITICAL
    description = "Game scores cannot be negative."

    def evaluate(self, context: Dict[str, Any]) -> ValidationResult:
        game: Optional[Game] = context.get("game")
        if not game or game.home_score is None or game.away_score is None:
            return ValidationResult(
                rule_id=self.rule_id,
                rule_category=self.rule_category,
                severity=self.severity,
                passed=True,
                message="Game score not present or unplayed.",
            )
        passed = game.home_score >= 0 and game.away_score >= 0
        msg = "Scores are non-negative." if passed else f"Negative score detected: {game.home_score}-{game.away_score}"
        return ValidationResult(
            rule_id=self.rule_id,
            rule_category=self.rule_category,
            severity=self.severity,
            passed=passed,
            message=msg,
            details={"home_score": game.home_score, "away_score": game.away_score},
        )


class NonNegativePlayerStatsRule(BaseRule):
    rule_id = "RULE_PLY_001"
    rule_category = "PLAYER_LEVEL"
    severity = ValidationSeverity.CRITICAL
    description = "Player statistics must be non-negative."

    def evaluate(self, context: Dict[str, Any]) -> ValidationResult:
        players: List[BoxscorePlayer] = context.get("boxscore_players", [])
        negatives = []
        for p in players:
            for stat in ["points", "fgm", "fga", "ftm", "fta", "orb", "drb", "trb", "ast", "stl", "blk", "tov", "pf"]:
                val = getattr(p, stat, None)
                if val is not None and val < 0:
                    negatives.append({"player_id": p.player_id, "stat": stat, "val": val})

        passed = len(negatives) == 0
        msg = "All player stats non-negative." if passed else f"Found {len(negatives)} negative player statistics."
        return ValidationResult(
            rule_id=self.rule_id,
            rule_category=self.rule_category,
            severity=self.severity,
            passed=passed,
            message=msg,
            details={"negative_entries": negatives[:10]},
        )


class ShootingBoundsRule(BaseRule):
    rule_id = "RULE_PLY_002"
    rule_category = "PLAYER_LEVEL"
    severity = ValidationSeverity.ERROR
    description = "Field goals made cannot exceed field goals attempted (FGM <= FGA)."

    def evaluate(self, context: Dict[str, Any]) -> ValidationResult:
        players: List[BoxscorePlayer] = context.get("boxscore_players", [])
        violations = []
        for p in players:
            if p.fgm is not None and p.fga is not None and p.fgm > p.fga:
                violations.append({"player_id": p.player_id, "fgm": p.fgm, "fga": p.fga})
            if p.ftm is not None and p.fta is not None and p.ftm > p.fta:
                violations.append({"player_id": p.player_id, "ftm": p.ftm, "fta": p.fta})

        passed = len(violations) == 0
        msg = "Shooting bounds valid." if passed else f"Found {len(violations)} shooting bound violations (made > attempted)."
        return ValidationResult(
            rule_id=self.rule_id,
            rule_category=self.rule_category,
            severity=self.severity,
            passed=passed,
            message=msg,
            details={"violations": violations},
        )


class PlayingTimeLimitRule(BaseRule):
    rule_id = "RULE_PLY_003"
    rule_category = "PLAYER_LEVEL"
    severity = ValidationSeverity.ERROR
    description = "Player seconds played cannot exceed total game duration."

    def evaluate(self, context: Dict[str, Any]) -> ValidationResult:
        game: Optional[Game] = context.get("game")
        players: List[BoxscorePlayer] = context.get("boxscore_players", [])
        periods = game.periods_played if game else 4
        max_allowed_seconds = periods * 600

        violations = []
        for p in players:
            if p.seconds_played is not None and p.seconds_played > max_allowed_seconds:
                violations.append({"player_id": p.player_id, "seconds": p.seconds_played, "max_allowed": max_allowed_seconds})

        passed = len(violations) == 0
        msg = "Playing time bounds valid." if passed else f"Found {len(violations)} playing time limit violations."
        return ValidationResult(
            rule_id=self.rule_id,
            rule_category=self.rule_category,
            severity=self.severity,
            passed=passed,
            message=msg,
            details={"violations": violations},
        )
