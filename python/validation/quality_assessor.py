"""Quality Assessor and Completeness Scorer."""

from datetime import datetime, timezone
from typing import List, Optional

from python.models.canonical import GameSources
from python.models.enums import (
    CompletenessTier,
    QualityTier,
    ValidationSeverity,
    ValidationStatus,
)
from python.validation.rules import ValidationResult


class QualityAssessor:
    """Assesses composite completeness and overall data quality score for a game."""

    @staticmethod
    def assess_game(
        game_id: str,
        boxscore_available: bool,
        pbp_available: bool,
        video_available: bool,
        shot_chart_available: bool,
        validation_results: List[ValidationResult],
        boxscore_path: Optional[str] = None,
        pbp_path: Optional[str] = None,
        video_path: Optional[str] = None,
    ) -> GameSources:
        # Determine Validation Status
        has_critical = any(not r.passed and r.severity == ValidationSeverity.CRITICAL for r in validation_results)
        has_errors = any(not r.passed and r.severity == ValidationSeverity.ERROR for r in validation_results)
        has_warnings = any(not r.passed and r.severity == ValidationSeverity.WARNING for r in validation_results)

        if has_critical or has_errors:
            val_status = ValidationStatus.FAIL_WITH_ERRORS
        elif has_warnings:
            val_status = ValidationStatus.PASS_WITH_WARNINGS
        else:
            val_status = ValidationStatus.PASS

        # Source Count (0 to 3)
        source_count = sum([1 for s in [boxscore_available, pbp_available, video_available] if s])

        if source_count == 3 and shot_chart_available:
            completeness = CompletenessTier.COMPLETE
        elif source_count >= 2:
            completeness = CompletenessTier.HIGH
        elif source_count == 1:
            completeness = CompletenessTier.PARTIAL
        else:
            completeness = CompletenessTier.MINIMAL

        # Composite Quality Tier
        if val_status == ValidationStatus.PASS and source_count >= 2:
            overall_quality = QualityTier.HIGH
        elif val_status in [ValidationStatus.PASS, ValidationStatus.PASS_WITH_WARNINGS] and source_count >= 1:
            overall_quality = QualityTier.MEDIUM
        elif val_status == ValidationStatus.FAIL_WITH_ERRORS and not has_critical:
            overall_quality = QualityTier.LOW
        else:
            overall_quality = QualityTier.COMPROMISED

        return GameSources(
            game_id=game_id,
            boxscore_available=boxscore_available,
            pbp_available=pbp_available,
            video_available=video_available,
            shot_chart_available=shot_chart_available,
            boxscore_file_path=boxscore_path,
            pbp_file_path=pbp_path,
            video_file_path=video_path,
            validation_status=val_status,
            completeness_score=completeness,
            overall_quality=overall_quality,
            updated_at=datetime.now(timezone.utc),
        )
