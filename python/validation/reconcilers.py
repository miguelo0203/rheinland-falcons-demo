"""Mathematical Reconcilers for Boxscore and Play-by-Play."""

from typing import Any, Dict, List, Optional
from python.models.canonical import BoxscorePlayer, BoxscoreTeam, Game, PBPEvent
from python.models.enums import ValidationSeverity, EventType
from python.validation.rules import ValidationResult


class BoxscoreReconciler:
    """Reconciles player-level aggregations against team totals."""

    @staticmethod
    def reconcile_points(
        game: Optional[Game],
        teams: List[BoxscoreTeam],
        players: List[BoxscorePlayer]
    ) -> List[ValidationResult]:
        results = []
        for team in teams:
            team_players = [p for p in players if p.team_id == team.team_id]
            sum_player_pts = sum(p.points for p in team_players)
            diff = sum_player_pts - team.points

            passed = (diff == 0)
            msg = (
                f"Team {team.team_id} points reconcile (Sum: {sum_player_pts}, Team Total: {team.points})."
                if passed
                else f"Team {team.team_id} points mismatch: Player sum {sum_player_pts} != Team total {team.points} (Diff: {diff})."
            )
            results.append(ValidationResult(
                rule_id="RULE_BXC_PTS_SUM",
                rule_category="BOXSCORE_RECONCILIATION",
                severity=ValidationSeverity.ERROR,
                passed=passed,
                message=msg,
                details={"team_id": team.team_id, "player_sum": sum_player_pts, "team_total": team.points, "diff": diff},
            ))
        return results

    @staticmethod
    def reconcile_rebounds(
        teams: List[BoxscoreTeam],
        players: List[BoxscorePlayer]
    ) -> List[ValidationResult]:
        results = []
        for team in teams:
            team_players = [p for p in players if p.team_id == team.team_id and p.trb is not None]
            if not team_players or team.trb is None:
                continue

            sum_player_trb = sum(p.trb for p in team_players if p.trb is not None)
            team_reb = team.team_rebounds or 0
            total_calc = sum_player_trb + team_reb
            diff = total_calc - team.trb

            passed = (diff == 0)
            msg = (
                f"Team {team.team_id} rebounds reconcile ({total_calc} vs {team.trb})."
                if passed
                else f"Team {team.team_id} rebounds discrepancy: Player sum ({sum_player_trb}) + Team REB ({team_reb}) = {total_calc} != {team.trb} (Diff: {diff})."
            )
            results.append(ValidationResult(
                rule_id="RULE_BXC_REB_SUM",
                rule_category="BOXSCORE_RECONCILIATION",
                severity=ValidationSeverity.WARNING,
                passed=passed,
                message=msg,
                details={"team_id": team.team_id, "player_sum": sum_player_trb, "team_reb": team_reb, "team_total": team.trb, "diff": diff},
            ))
        return results


class PBPReconciler:
    """Reconciles Play-by-Play events against Boxscores and chronological rules."""

    @staticmethod
    def reconcile_final_score(
        game: Optional[Game],
        events: List[PBPEvent]
    ) -> ValidationResult:
        if not events or not game or game.home_score is None or game.away_score is None:
            return ValidationResult(
                rule_id="RULE_PBP_FINAL_SCORE",
                rule_category="PBP_RECONCILIATION",
                severity=ValidationSeverity.ERROR,
                passed=True,
                message="PBP or Game score not present (skipped).",
            )

        last_event = events[-1]
        pbp_home = last_event.home_score
        pbp_away = last_event.away_score

        home_match = (pbp_home == game.home_score)
        away_match = (pbp_away == game.away_score)
        passed = home_match and away_match

        msg = (
            f"PBP final score matches game score ({pbp_home}-{pbp_away})."
            if passed
            else f"PBP final score ({pbp_home}-{pbp_away}) diverges from game score ({game.home_score}-{game.away_score})."
        )
        return ValidationResult(
            rule_id="RULE_PBP_FINAL_SCORE",
            rule_category="PBP_RECONCILIATION",
            severity=ValidationSeverity.ERROR,
            passed=passed,
            message=msg,
            details={
                "pbp_home": pbp_home,
                "pbp_away": pbp_away,
                "game_home": game.home_score,
                "game_away": game.away_score,
            },
        )

    @staticmethod
    def check_clock_monotonicity(events: List[PBPEvent]) -> ValidationResult:
        if not events:
            return ValidationResult(
                rule_id="RULE_PBP_CLOCK_MONO",
                rule_category="PBP_RECONCILIATION",
                severity=ValidationSeverity.WARNING,
                passed=True,
                message="No events to evaluate for clock monotonicity.",
            )

        inversions = []
        for i in range(len(events) - 1):
            curr_ev = events[i]
            next_ev = events[i + 1]
            if curr_ev.period == next_ev.period:
                if next_ev.period_seconds_remaining > curr_ev.period_seconds_remaining:
                    inversions.append({
                        "period": curr_ev.period,
                        "from_clock": curr_ev.clock_display,
                        "to_clock": next_ev.clock_display,
                        "event_index": next_ev.event_index,
                    })

        passed = len(inversions) == 0
        msg = "PBP clock is monotonic." if passed else f"Detected {len(inversions)} clock resets/inversions."
        return ValidationResult(
            rule_id="RULE_PBP_CLOCK_MONO",
            rule_category="PBP_RECONCILIATION",
            severity=ValidationSeverity.WARNING,
            passed=passed,
            message=msg,
            details={"inversions": inversions[:5]},
        )

    @staticmethod
    def reconcile_player_points(
        players: List[BoxscorePlayer],
        events: List[PBPEvent]
    ) -> List[ValidationResult]:
        if not players or not events:
            return []

        # Aggregate points from PBP by player
        pbp_pts_by_player: Dict[str, int] = {}
        total_pbp_pts = 0
        for ev in events:
            if ev.player_id and ev.points_scored > 0:
                pbp_pts_by_player[ev.player_id] = pbp_pts_by_player.get(ev.player_id, 0) + ev.points_scored
                total_pbp_pts += ev.points_scored

        total_box_pts = sum(p.points for p in players)
        is_complete_pbp = (total_pbp_pts == total_box_pts)

        results = []
        for p in players:
            pbp_pts = pbp_pts_by_player.get(p.player_id, 0)
            if is_complete_pbp:
                diff = pbp_pts - p.points
                passed = (diff == 0)
                sev = ValidationSeverity.ERROR
                msg = (
                    f"Player {p.player_id} points reconcile (PBP: {pbp_pts}, Boxscore: {p.points})."
                    if passed
                    else f"Player {p.player_id} points mismatch: PBP {pbp_pts} != Boxscore {p.points} (Diff: {diff})."
                )
            else:
                # Partial / sample PBP: points in PBP cannot exceed boxscore
                passed = (pbp_pts <= p.points)
                sev = ValidationSeverity.WARNING if not passed else ValidationSeverity.INFO
                msg = (
                    f"Player {p.player_id} points in sample PBP ({pbp_pts}) within Boxscore ({p.points})."
                    if passed
                    else f"Player {p.player_id} PBP points ({pbp_pts}) exceed Boxscore ({p.points})."
                )

            results.append(ValidationResult(
                rule_id="RULE_PBP_PTS_RECON",
                rule_category="PBP_RECONCILIATION",
                severity=sev,
                passed=passed,
                message=msg,
                details={"player_id": p.player_id, "pbp_points": pbp_pts, "boxscore_points": p.points},
            ))
        return results
