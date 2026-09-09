"""Validation Engine for JBBL / NBBL Sandbox."""

from typing import Any, Dict, List, Optional
from python.models.canonical import (
    BoxscorePlayer,
    BoxscoreTeam,
    Game,
    GameSources,
    PBPEvent,
    Shot,
    Video,
    ValidationLog,
)
from python.validation.rules import (
    BaseRule,
    DistinctTeamsRule,
    NonNegativeScoresRule,
    NonNegativePlayerStatsRule,
    ShootingBoundsRule,
    PlayingTimeLimitRule,
    ValidationResult,
)
from python.validation.reconcilers import BoxscoreReconciler, PBPReconciler
from python.validation.quality_assessor import QualityAssessor
from python.ingestion.conflict_detector import ConflictDetector


class ValidationEngine:
    """Executes validation rules, mathematical reconciliations, and quality evaluation."""

    def __init__(self, conflict_detector: Optional[ConflictDetector] = None):
        self.conflict_detector = conflict_detector or ConflictDetector()
        self.rules: List[BaseRule] = [
            DistinctTeamsRule(),
            NonNegativeScoresRule(),
            NonNegativePlayerStatsRule(),
            ShootingBoundsRule(),
            PlayingTimeLimitRule(),
        ]

    def validate_game(
        self,
        game_id: str,
        game: Optional[Game] = None,
        boxscore_teams: Optional[List[BoxscoreTeam]] = None,
        boxscore_players: Optional[List[BoxscorePlayer]] = None,
        pbp_events: Optional[List[PBPEvent]] = None,
        shots: Optional[List[Shot]] = None,
        videos: Optional[List[Video]] = None,
        boxscore_path: Optional[str] = None,
        pbp_path: Optional[str] = None,
        video_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Execute full validation suite for a game and return results and GameSources."""
        bxt = boxscore_teams or []
        bxp = boxscore_players or []
        events = pbp_events or []
        shot_list = shots or []
        video_list = videos or []

        context = {
            "game": game,
            "boxscore_teams": bxt,
            "boxscore_players": bxp,
            "pbp_events": events,
            "shots": shot_list,
            "videos": video_list,
        }

        all_results: List[ValidationResult] = []

        # 1. Base Rules
        for rule in self.rules:
            res = rule.evaluate(context)
            all_results.append(res)

        # 2. Boxscore Reconciliations
        if bxt and bxp:
            all_results.extend(BoxscoreReconciler.reconcile_points(game, bxt, bxp))
            all_results.extend(BoxscoreReconciler.reconcile_rebounds(bxt, bxp))

        # 3. PBP Reconciliations
        if events:
            all_results.append(PBPReconciler.check_clock_monotonicity(events))
            if game:
                score_res = PBPReconciler.reconcile_final_score(game, events)
                all_results.append(score_res)
                if not score_res.passed and game.home_score is not None:
                    # Detect & log multi-source conflict for final score
                    self.conflict_detector.check_and_log_conflict(
                        game_id=game_id,
                        entity_table="game",
                        entity_id=game_id,
                        field_name="home_score",
                        source_a_type="BOXSCORE",
                        source_a_val=game.home_score,
                        source_b_type="PBP",
                        source_b_val=events[-1].home_score,
                        category="game_score",
                    )
                    self.conflict_detector.check_and_log_conflict(
                        game_id=game_id,
                        entity_table="game",
                        entity_id=game_id,
                        field_name="away_score",
                        source_a_type="BOXSCORE",
                        source_a_val=game.away_score,
                        source_b_type="PBP",
                        source_b_val=events[-1].away_score,
                        category="game_score",
                    )

            if bxp:
                pbp_pts_results = PBPReconciler.reconcile_player_points(bxp, events)
                all_results.extend(pbp_pts_results)
                for pr in pbp_pts_results:
                    if not pr.passed and pr.details:
                        # Log conflict
                        self.conflict_detector.check_and_log_conflict(
                            game_id=game_id,
                            entity_table="boxscore_player",
                            entity_id=pr.details["player_id"],
                            field_name="points",
                            source_a_type="BOXSCORE",
                            source_a_val=pr.details["boxscore_points"],
                            source_b_type="PBP",
                            source_b_val=pr.details["pbp_points"],
                            category="player_statistics",
                        )

        # 4. Assess Overall Quality & Source Availability
        has_boxscore = bool(bxt or bxp)
        has_pbp = bool(events)
        has_video = bool(video_list)
        has_shots = any(s.x_coord is not None and s.y_coord is not None for s in shot_list)

        game_sources = QualityAssessor.assess_game(
            game_id=game_id,
            boxscore_available=has_boxscore,
            pbp_available=has_pbp,
            video_available=has_video,
            shot_chart_available=has_shots,
            validation_results=all_results,
            boxscore_path=boxscore_path,
            pbp_path=pbp_path,
            video_path=video_path,
        )

        # Convert results to ValidationLog models
        logs: List[ValidationLog] = [r.to_log_model(game_id) for r in all_results]

        return {
            "game_sources": game_sources,
            "validation_results": all_results,
            "validation_logs": logs,
            "conflicts": self.conflict_detector.detected_conflicts,
        }
