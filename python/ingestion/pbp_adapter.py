"""Play-by-Play (PBP) Ingestion Adapter."""

import csv
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from python.ingestion.base import BaseAdapter, NormalizedPayload
from python.ingestion.provenance import generate_id
from python.models.canonical import PBPEvent, Shot, LineupStint
from python.models.enums import (
    EventType,
    ObservationStatus,
    PeriodType,
    ShotType,
    SourceType,
    ConfidenceStatus,
    ReconstructionMethod,
)


def parse_clock_to_seconds(clock_str: str, period_duration_sec: float = 600.0) -> float:
    """Parse 'MM:SS' or 'MM:SS.s' into seconds remaining in period."""
    if not clock_str:
        return period_duration_sec
    parts = str(clock_str).strip().split(":")
    if len(parts) == 2:
        try:
            mins = float(parts[0])
            secs = float(parts[1])
            return mins * 60.0 + secs
        except ValueError:
            return period_duration_sec
    try:
        return float(clock_str)
    except ValueError:
        return period_duration_sec


class PBPAdapter(BaseAdapter):
    """Adapter for ingesting structured Play-by-Play event stream logs."""

    def __init__(
        self,
        provider_name: str = "GENERIC_PBP",
        entity_resolver=None,
        provenance_tracker=None,
    ):
        super().__init__(
            source_type=SourceType.PBP,
            provider_name=provider_name,
            entity_resolver=entity_resolver,
            provenance_tracker=provenance_tracker,
        )

    def detect(self, file_path: Union[str, Path]) -> bool:
        """Detect if file is a PBP log."""
        path = Path(file_path)
        if not path.exists():
            return False
        if path.suffix.lower() == ".json":
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return "events" in data or "pbp" in data or "plays" in data
            except Exception:
                return False
        elif path.suffix.lower() == ".csv":
            try:
                with open(path, "r", encoding="utf-8") as f:
                    header = f.readline().upper()
                    return ("PERIOD" in header or "QUARTER" in header) and ("CLOCK" in header or "TIME" in header)
            except Exception:
                return False
        return False

    def extract(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """Extract raw events into structured dictionary."""
        path = Path(file_path)
        if path.suffix.lower() == ".json":
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        elif path.suffix.lower() == ".csv":
            records = []
            with open(path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    records.append(row)
            return {"events": records}
        raise ValueError(f"Unsupported PBP format: {path}")

    def normalize(
        self,
        raw_data: Dict[str, Any],
        file_path: Union[str, Path],
        game_id: Optional[str] = None,
        season_id: Optional[str] = None,
        competition_id: Optional[str] = None,
    ) -> NormalizedPayload:
        """Normalize extracted PBP data to canonical domain models."""
        provenance = self.provenance_tracker.create_provenance(
            source_type=SourceType.PBP,
            source_provider=self.provider_name,
            source_file_path=file_path,
            parser_version="1.0.0",
        )

        payload = NormalizedPayload(provenance=provenance)
        actual_game_id = game_id or raw_data.get("game_id") or generate_id("GAM")
        events_list = raw_data.get("events") or raw_data.get("plays") or []

        running_home_score = 0
        running_away_score = 0
        current_possession_num = 1
        possession_id = f"POS_{actual_game_id}_1"

        for idx, ev in enumerate(events_list):
            period = int(ev.get("period", 1))
            clock_str = str(ev.get("clock_display") or ev.get("clock") or "10:00")
            period_sec_rem = parse_clock_to_seconds(clock_str)
            
            # 4 quarters of 10 min (600s). Regulation total = 2400s.
            if period <= 4:
                game_sec_rem = (4 - period) * 600.0 + period_sec_rem
                period_type = PeriodType.REGULAR
            else:
                game_sec_rem = period_sec_rem  # Overtime (5 mins = 300s)
                period_type = PeriodType.OVERTIME

            raw_type = str(ev.get("event_type") or ev.get("type") or "UNKNOWN").upper()
            event_type = self._map_event_type(raw_type)

            # Resolve team & player
            team_id = None
            if ev.get("team_name") or ev.get("team"):
                t_name = ev.get("team_name") or ev.get("team")
                team_id, t_alias = self.resolver.resolve_team(t_name, provider=self.provider_name)
                payload.aliases.append(t_alias)

            player_id = None
            if ev.get("player_name") or ev.get("player"):
                p_name = ev.get("player_name") or ev.get("player")
                p_id, p_alias = self.resolver.resolve_player(
                    raw_name=p_name,
                    provider=self.provider_name,
                    jersey_number=str(ev.get("jersey_number")) if ev.get("jersey_number") else None,
                    team_id=team_id,
                )
                player_id = p_id
                payload.aliases.append(p_alias)

            # Score tracking
            pts = int(ev.get("points_scored") or ev.get("points", 0))
            is_home_scoring = ev.get("is_home", True)
            if "home_score" in ev and "away_score" in ev:
                running_home_score = int(ev["home_score"])
                running_away_score = int(ev["away_score"])
            else:
                if pts > 0:
                    if is_home_scoring:
                        running_home_score += pts
                    else:
                        running_away_score += pts

            # Possession boundary detection heuristic
            if event_type in [EventType.TURNOVER, EventType.REBOUND] or (event_type == EventType.SHOT and pts > 0):
                current_possession_num += 1
                possession_id = f"POS_{actual_game_id}_{current_possession_num}"

            event_id = generate_id("EVT")
            pbp_ev = PBPEvent(
                event_id=event_id,
                game_id=actual_game_id,
                period=period,
                period_type=period_type,
                clock_display=clock_str,
                game_seconds_remaining=game_sec_rem,
                period_seconds_remaining=period_sec_rem,
                event_index=idx,
                event_type=event_type,
                event_subtype=ev.get("event_subtype") or ev.get("subtype"),
                team_id=team_id,
                player_id=player_id,
                secondary_player_id=None,
                home_score=running_home_score,
                away_score=running_away_score,
                score_margin=running_home_score - running_away_score,
                points_scored=pts,
                description=ev.get("description"),
                possession_id=possession_id,
                provenance_id=provenance.provenance_id,
            )
            payload.pbp_events.append(pbp_ev)

            # Extract shot if applicable
            if event_type == EventType.SHOT or raw_type in ["SHOT", "2PT", "3PT", "FIELD_GOAL"]:
                is_3pt = bool(ev.get("is_3pt") or "3PT" in raw_type or pts == 3)
                shot_type = ShotType.THREE_POINT if is_3pt else ShotType.TWO_POINT
                is_made = bool(pts > 0 or ev.get("is_made"))
                x_c = float(ev["x"]) if ev.get("x") is not None else None
                y_c = float(ev["y"]) if ev.get("y") is not None else None
                loc_status = ObservationStatus.OBSERVED if (x_c is not None and y_c is not None) else ObservationStatus.NOT_AVAILABLE

                shot = Shot(
                    shot_id=generate_id("SHT"),
                    event_id=event_id,
                    game_id=actual_game_id,
                    team_id=team_id or "TEM_UNKNOWN",
                    player_id=player_id or "PLY_UNKNOWN",
                    period=period,
                    game_seconds_remaining=game_sec_rem,
                    shot_type=shot_type,
                    shot_subtype=ev.get("shot_subtype"),
                    is_made=is_made,
                    points=pts,
                    x_coord=x_c,
                    y_coord=y_c,
                    shot_distance_m=float(ev["distance_m"]) if ev.get("distance_m") is not None else None,
                    shot_location_status=loc_status,
                    assisted_by_player_id=None,
                    provenance_id=provenance.provenance_id,
                )
                payload.shots.append(shot)

        return payload

    def _map_event_type(self, raw_type: str) -> EventType:
        """Map raw provider event type to canonical EventType."""
        if any(k in raw_type for k in ["SHOT", "LAYUP", "DUNK", "JUMP", "2PT", "3PT"]):
            return EventType.SHOT
        elif "FREE" in raw_type or "FT" in raw_type:
            return EventType.FREE_THROW
        elif "REB" in raw_type:
            return EventType.REBOUND
        elif "TURN" in raw_type or "TOV" in raw_type:
            return EventType.TURNOVER
        elif "FOUL" in raw_type:
            return EventType.FOUL
        elif "SUB" in raw_type:
            return EventType.SUB
        elif "TIMEOUT" in raw_type:
            return EventType.TIMEOUT
        elif "JUMP" in raw_type and "BALL" in raw_type:
            return EventType.JUMP_BALL
        elif "PERIOD" in raw_type and "START" in raw_type:
            return EventType.PERIOD_START
        elif "PERIOD" in raw_type and "END" in raw_type:
            return EventType.PERIOD_END
        return EventType.VIOLATION
