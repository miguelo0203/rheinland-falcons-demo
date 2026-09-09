"""Boxscore Ingestion Adapter."""

import csv
import json
from datetime import datetime, date
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from python.ingestion.base import BaseAdapter, NormalizedPayload
from python.ingestion.provenance import generate_id
from python.models.canonical import (
    BoxscorePlayer,
    BoxscoreTeam,
    Game,
    GameRoster,
    PlayerTeam,
)
from python.models.enums import ObservationStatus, SourceType, SourceProvider


class BoxscoreAdapter(BaseAdapter):
    """Adapter for ingesting structured Boxscore files (JSON or CSV)."""

    def __init__(
        self,
        provider_name: str = "GENERIC_BOXSCORE",
        entity_resolver=None,
        provenance_tracker=None,
    ):
        super().__init__(
            source_type=SourceType.BOXSCORE,
            provider_name=provider_name,
            entity_resolver=entity_resolver,
            provenance_tracker=provenance_tracker,
        )

    def detect(self, file_path: Union[str, Path]) -> bool:
        """Detect if file is a supported boxscore format."""
        path = Path(file_path)
        if not path.exists():
            return False
        if path.suffix.lower() == ".json":
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return "boxscore" in data or "home_team" in data or "players" in data
            except Exception:
                return False
        elif path.suffix.lower() == ".csv":
            try:
                with open(path, "r", encoding="utf-8") as f:
                    header = f.readline().upper()
                    return ("PTS" in header or "POINTS" in header) and ("PLAYER" in header or "TEAM" in header)
            except Exception:
                return False
        return False

    def extract(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """Extract raw records into structured dictionary."""
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
            return {"format": "csv", "records": records}
        raise ValueError(f"Unsupported boxscore format: {path}")

    def normalize(
        self,
        raw_data: Dict[str, Any],
        file_path: Union[str, Path],
        game_id: Optional[str] = None,
        season_id: Optional[str] = None,
        competition_id: Optional[str] = None,
    ) -> NormalizedPayload:
        """Normalize extracted boxscore data to canonical domain models."""
        provenance = self.provenance_tracker.create_provenance(
            source_type=SourceType.BOXSCORE,
            source_provider=self.provider_name,
            source_file_path=file_path,
            parser_version="1.0.0",
        )

        payload = NormalizedPayload(provenance=provenance)
        actual_game_id = game_id or raw_data.get("game_id") or generate_id("GAM")
        actual_season_id = season_id or raw_data.get("season_id") or "SEA_DEFAULT"
        actual_comp_id = competition_id or raw_data.get("competition_id") or "CMP_DEFAULT"

        # Handle JSON structured boxscore
        if "home_team" in raw_data and "away_team" in raw_data:
            self._normalize_json_boxscore(
                raw_data=raw_data,
                payload=payload,
                game_id=actual_game_id,
                season_id=actual_season_id,
                competition_id=actual_comp_id,
                provenance_id=provenance.provenance_id,
            )
        elif "records" in raw_data:
            self._normalize_csv_boxscore(
                records=raw_data["records"],
                payload=payload,
                game_id=actual_game_id,
                season_id=actual_season_id,
                competition_id=actual_comp_id,
                provenance_id=provenance.provenance_id,
            )

        return payload

    def _normalize_json_boxscore(
        self,
        raw_data: Dict[str, Any],
        payload: NormalizedPayload,
        game_id: str,
        season_id: str,
        competition_id: str,
        provenance_id: str,
    ):
        home_raw = raw_data["home_team"]
        away_raw = raw_data["away_team"]

        home_team_id, h_alias = self.resolver.resolve_team(
            raw_name=home_raw.get("name", "Home Team"),
            provider=self.provider_name,
            provider_team_id=home_raw.get("id"),
        )
        away_team_id, a_alias = self.resolver.resolve_team(
            raw_name=away_raw.get("name", "Away Team"),
            provider=self.provider_name,
            provider_team_id=away_raw.get("id"),
        )

        payload.aliases.extend([h_alias, a_alias])

        # Parse Game
        game_date_val = raw_data.get("game_date")
        parsed_date = date.fromisoformat(game_date_val) if game_date_val else date.today()

        game_obj = Game(
            game_id=game_id,
            season_id=season_id,
            competition_id=competition_id,
            game_date=parsed_date,
            game_time=raw_data.get("game_time"),
            round_number=raw_data.get("round_number"),
            home_team_id=home_team_id,
            away_team_id=away_team_id,
            venue=raw_data.get("venue"),
            periods_played=raw_data.get("periods_played", 4),
            home_score=home_raw.get("points"),
            away_score=away_raw.get("points"),
            game_status="FINAL",
        )
        payload.games.append(game_obj)

        for is_home, team_data, team_id in [(True, home_raw, home_team_id), (False, away_raw, away_team_id)]:
            # Team Boxscore
            team_stats = team_data.get("stats", {})
            bxt = BoxscoreTeam(
                boxscore_team_id=generate_id("BXT"),
                game_id=game_id,
                team_id=team_id,
                is_home=is_home,
                points=team_data.get("points", team_stats.get("points", 0)),
                fgm=team_stats.get("fgm"),
                fga=team_stats.get("fga"),
                fg2m=team_stats.get("fg2m"),
                fg2a=team_stats.get("fg2a"),
                fg3m=team_stats.get("fg3m"),
                fg3a=team_stats.get("fg3a"),
                ftm=team_stats.get("ftm"),
                fta=team_stats.get("fta"),
                orb=team_stats.get("orb"),
                drb=team_stats.get("drb"),
                trb=team_stats.get("trb"),
                ast=team_stats.get("ast"),
                stl=team_stats.get("stl"),
                blk=team_stats.get("blk"),
                tov=team_stats.get("tov"),
                pf=team_stats.get("pf"),
                team_rebounds=team_stats.get("team_rebounds"),
                team_turnovers=team_stats.get("team_turnovers"),
                provenance_id=provenance_id,
            )
            payload.boxscore_teams.append(bxt)

            # Player Boxscores
            for p_data in team_data.get("players", []):
                p_name = p_data.get("name") or f"Player {p_data.get('jersey_number', 'Unknown')}"
                p_jersey = str(p_data.get("jersey_number")) if p_data.get("jersey_number") is not None else None
                p_id, p_alias = self.resolver.resolve_player(
                    raw_name=p_name,
                    provider=self.provider_name,
                    provider_player_id=p_data.get("id"),
                    jersey_number=p_jersey,
                    team_id=team_id,
                    listed_position=p_data.get("listed_position"),
                )
                payload.aliases.append(p_alias)

                # Roster entry
                roster_entry = GameRoster(
                    game_roster_id=generate_id("ROS"),
                    game_id=game_id,
                    team_id=team_id,
                    player_id=p_id,
                    jersey_number=p_jersey,
                    is_starter=p_data.get("is_starter"),
                    is_captain=p_data.get("is_captain"),
                    is_active=p_data.get("is_active", True),
                    provenance_id=provenance_id,
                )
                payload.game_rosters.append(roster_entry)

                # Player boxscore entry
                bxp = BoxscorePlayer(
                    boxscore_player_id=generate_id("BXP"),
                    game_id=game_id,
                    team_id=team_id,
                    player_id=p_id,
                    jersey_number=p_jersey,
                    seconds_played=p_data.get("seconds_played"),
                    points=p_data.get("points", 0),
                    fgm=p_data.get("fgm"),
                    fga=p_data.get("fga"),
                    fg2m=p_data.get("fg2m"),
                    fg2a=p_data.get("fg2a"),
                    fg3m=p_data.get("fg3m"),
                    fg3a=p_data.get("fg3a"),
                    ftm=p_data.get("ftm"),
                    fta=p_data.get("fta"),
                    orb=p_data.get("orb"),
                    drb=p_data.get("drb"),
                    trb=p_data.get("trb"),
                    ast=p_data.get("ast"),
                    stl=p_data.get("stl"),
                    blk=p_data.get("blk"),
                    tov=p_data.get("tov"),
                    pf=p_data.get("pf"),
                    plus_minus=p_data.get("plus_minus"),
                    is_dnp=p_data.get("is_dnp", False),
                    dnp_reason=p_data.get("dnp_reason"),
                    observation_status=ObservationStatus.OBSERVED,
                    provenance_id=provenance_id,
                )
                payload.boxscore_players.append(bxp)

    def _normalize_csv_boxscore(
        self,
        records: List[Dict[str, Any]],
        payload: NormalizedPayload,
        game_id: str,
        season_id: str,
        competition_id: str,
        provenance_id: str,
    ):
        # Infer teams from CSV
        teams_found = {}
        for r in records:
            t_name = r.get("team_name") or r.get("team") or "Unknown Team"
            if t_name not in teams_found:
                t_id, alias = self.resolver.resolve_team(t_name, provider=self.provider_name)
                teams_found[t_name] = t_id
                payload.aliases.append(alias)

        team_id_list = list(teams_found.values())
        home_team_id = team_id_list[0] if team_id_list else generate_id("TEM")
        away_team_id = team_id_list[1] if len(team_id_list) > 1 else generate_id("TEM")

        # Game row
        payload.games.append(Game(
            game_id=game_id,
            season_id=season_id,
            competition_id=competition_id,
            game_date=date.today(),
            home_team_id=home_team_id,
            away_team_id=away_team_id,
        ))

        # Players
        for r in records:
            p_name = r.get("player_name") or r.get("player") or "Unknown Player"
            t_name = r.get("team_name") or r.get("team") or "Unknown Team"
            t_id = teams_found.get(t_name, home_team_id)
            jersey = r.get("jersey_number") or r.get("jersey")

            p_id, p_alias = self.resolver.resolve_player(
                raw_name=p_name,
                provider=self.provider_name,
                jersey_number=jersey,
                team_id=t_id,
            )
            payload.aliases.append(p_alias)

            def get_int(key: str) -> Optional[int]:
                v = r.get(key)
                if v is not None and str(v).strip() != "":
                    try:
                        return int(float(v))
                    except ValueError:
                        return None
                return None

            payload.boxscore_players.append(BoxscorePlayer(
                boxscore_player_id=generate_id("BXP"),
                game_id=game_id,
                team_id=t_id,
                player_id=p_id,
                jersey_number=str(jersey) if jersey else None,
                points=get_int("points") or get_int("pts") or 0,
                fgm=get_int("fgm"),
                fga=get_int("fga"),
                fg2m=get_int("fg2m"),
                fg2a=get_int("fg2a"),
                fg3m=get_int("fg3m"),
                fg3a=get_int("fg3a"),
                ftm=get_int("ftm"),
                fta=get_int("fta"),
                orb=get_int("orb"),
                drb=get_int("drb"),
                trb=get_int("trb") or get_int("reb"),
                ast=get_int("ast"),
                stl=get_int("stl"),
                blk=get_int("blk"),
                tov=get_int("tov"),
                pf=get_int("pf"),
                observation_status=ObservationStatus.OBSERVED,
                provenance_id=provenance_id,
            ))
