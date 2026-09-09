"""Conflict Detector and Multi-Source Preservation Engine."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from python.models.canonical import SourceConflictLog
from python.ingestion.provenance import generate_id
from python.config import Settings


class ConflictDetector:
    """Detects discrepancies between multiple sources, logs conflicts, and applies precedence."""

    def __init__(self, precedence_rules: Optional[Dict[str, List[str]]] = None):
        self.precedence_rules = precedence_rules or Settings.CONFIG.get("source_precedence", {
            "game_score": ["BOXSCORE", "PBP", "VIDEO"],
            "player_statistics": ["BOXSCORE", "PBP"],
            "shot_locations": ["PBP", "VIDEO"],
        })
        self.detected_conflicts: List[SourceConflictLog] = []

    def check_and_log_conflict(
        self,
        game_id: str,
        entity_table: str,
        entity_id: str,
        field_name: str,
        source_a_type: str,
        source_a_val: Any,
        source_b_type: str,
        source_b_val: Any,
        category: str = "player_statistics",
    ) -> Optional[SourceConflictLog]:
        """Compare two values for the same fact. If different, record conflict and determine resolution."""
        if source_a_val is None or source_b_val is None:
            return None

        # Compare stringified or numeric equality
        if str(source_a_val).strip() == str(source_b_val).strip():
            return None

        # Conflict exists! Resolve via documented precedence
        precedence = self.precedence_rules.get(category, ["BOXSCORE", "PBP", "VIDEO"])
        if source_a_type in precedence and source_b_type in precedence:
            idx_a = precedence.index(source_a_type)
            idx_b = precedence.index(source_b_type)
            if idx_a <= idx_b:
                policy = f"SOURCE_PRECEDENCE_{source_a_type}"
                resolved = str(source_a_val)
            else:
                policy = f"SOURCE_PRECEDENCE_{source_b_type}"
                resolved = str(source_b_val)
        else:
            policy = f"SOURCE_PRECEDENCE_{source_a_type}"
            resolved = str(source_a_val)

        conflict = SourceConflictLog(
            conflict_id=generate_id("CNF"),
            game_id=game_id,
            entity_table=entity_table,
            entity_id=entity_id,
            field_name=field_name,
            source_a_type=source_a_type,
            source_a_value=str(source_a_val),
            source_b_type=source_b_type,
            source_b_value=str(source_b_val),
            resolution_policy=policy,
            resolved_value=resolved,
            logged_at=datetime.now(timezone.utc),
        )
        self.detected_conflicts.append(conflict)
        return conflict
