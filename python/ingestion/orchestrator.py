"""Master Pipeline Orchestrator for JBBL / NBBL Sandbox."""

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import pandas as pd

from python.config import Settings
from python.database.duckdb_manager import DuckDBManager
from python.ingestion.base import BaseAdapter, NormalizedPayload
from python.ingestion.boxscore_adapter import BoxscoreAdapter
from python.ingestion.conflict_detector import ConflictDetector
from python.ingestion.entity_resolver import EntityResolver
from python.ingestion.pbp_adapter import PBPAdapter
from python.ingestion.provenance import ProvenanceTracker, generate_id
from python.ingestion.video_adapter import VideoAdapter
from python.models.canonical import Game
from python.validation.engine import ValidationEngine


class PipelineOrchestrator:
    """Coordinates multi-source ingestion, entity resolution, validation, and storage."""

    def __init__(
        self,
        db_manager: Optional[DuckDBManager] = None,
        entity_resolver: Optional[EntityResolver] = None,
        provenance_tracker: Optional[ProvenanceTracker] = None,
        conflict_detector: Optional[ConflictDetector] = None,
    ):
        Settings.ensure_directories()
        self.db = db_manager or DuckDBManager()
        self.resolver = entity_resolver or EntityResolver()
        self.provenance_tracker = provenance_tracker or ProvenanceTracker()
        self.conflict_detector = conflict_detector or ConflictDetector()
        self.validator = ValidationEngine(conflict_detector=self.conflict_detector)

        self.boxscore_adapter = BoxscoreAdapter(
            entity_resolver=self.resolver,
            provenance_tracker=self.provenance_tracker,
        )
        self.pbp_adapter = PBPAdapter(
            entity_resolver=self.resolver,
            provenance_tracker=self.provenance_tracker,
        )
        self.video_adapter = VideoAdapter(
            entity_resolver=self.resolver,
            provenance_tracker=self.provenance_tracker,
        )

        # Initialize schema in DuckDB
        self.db.initialize_schema()

    def ingest_game(
        self,
        game_id: str,
        boxscore_file: Optional[Union[str, Path]] = None,
        pbp_file: Optional[Union[str, Path]] = None,
        video_file: Optional[Union[str, Path]] = None,
        season_id: str = "SEA_2024_2025",
        competition_id: str = "CMP_U16_REGIONAL",
    ) -> Dict[str, Any]:
        """Ingest a game with any combination of Boxscore, PBP, and Video sources."""
        provenances = []
        all_competitions = []
        all_seasons = []
        all_teams = []
        all_players = []
        all_player_teams = []
        all_games = []
        all_game_rosters = []
        all_boxscore_teams = []
        all_boxscore_players = []
        all_pbp_events = []
        all_shots = []
        all_lineup_stints = []
        all_videos = []
        all_video_syncs = []
        all_aliases = []

        # 1. Boxscore Ingestion (if provided)
        if boxscore_file and Path(boxscore_file).exists():
            raw_box = self.boxscore_adapter.extract(boxscore_file)
            box_payload = self.boxscore_adapter.normalize(
                raw_data=raw_box,
                file_path=boxscore_file,
                game_id=game_id,
                season_id=season_id,
                competition_id=competition_id,
            )
            provenances.append(box_payload.provenance)
            all_games.extend(box_payload.games)
            all_boxscore_teams.extend(box_payload.boxscore_teams)
            all_boxscore_players.extend(box_payload.boxscore_players)
            all_game_rosters.extend(box_payload.game_rosters)
            all_aliases.extend(box_payload.aliases)

        # 2. PBP Ingestion (if provided)
        if pbp_file and Path(pbp_file).exists():
            raw_pbp = self.pbp_adapter.extract(pbp_file)
            pbp_payload = self.pbp_adapter.normalize(
                raw_data=raw_pbp,
                file_path=pbp_file,
                game_id=game_id,
                season_id=season_id,
                competition_id=competition_id,
            )
            provenances.append(pbp_payload.provenance)
            all_pbp_events.extend(pbp_payload.pbp_events)
            all_shots.extend(pbp_payload.shots)
            all_aliases.extend(pbp_payload.aliases)

        # 3. Video Ingestion (if provided)
        if video_file and Path(video_file).exists():
            raw_vid = self.video_adapter.extract(video_file)
            vid_payload = self.video_adapter.normalize(
                raw_data=raw_vid,
                file_path=video_file,
                game_id=game_id,
                season_id=season_id,
                competition_id=competition_id,
            )
            provenances.append(vid_payload.provenance)
            all_videos.extend(vid_payload.videos)

            # Ensure referential integrity on video syncs
            existing_event_ids = {e.event_id for e in all_pbp_events}
            for sync in vid_payload.video_event_syncs:
                if sync.event_id and sync.event_id not in existing_event_ids:
                    sync.event_id = None
                all_video_syncs.append(sync)

        # Ensure base game entity exists even if boxscore was missing
        active_game = all_games[0] if all_games else None
        if not active_game:
            # Check if PBP events have team IDs
            pbp_team_ids = [e.team_id for e in all_pbp_events if e.team_id]
            distinct_pbp_teams = list(dict.fromkeys(pbp_team_ids))

            if len(distinct_pbp_teams) >= 2:
                home_team_id = distinct_pbp_teams[0]
                away_team_id = distinct_pbp_teams[1]
            else:
                home_team_id, h_alias = self.resolver.resolve_team("Home Team (Unspecified)", provider="FALLBACK")
                away_team_id, a_alias = self.resolver.resolve_team("Away Team (Unspecified)", provider="FALLBACK")
                all_aliases.extend([h_alias, a_alias])

            active_game = Game(
                game_id=game_id,
                season_id=season_id,
                competition_id=competition_id,
                game_date=datetime.now(timezone.utc).date(),
                home_team_id=home_team_id,
                away_team_id=away_team_id,
                home_score=all_pbp_events[-1].home_score if all_pbp_events else None,
                away_score=all_pbp_events[-1].away_score if all_pbp_events else None,
                game_status="SCHEDULED" if not all_videos and not all_pbp_events else "FINAL",
            )
            all_games.append(active_game)

        # 4. Validation & Quality Assessment
        validation_output = self.validator.validate_game(
            game_id=game_id,
            game=active_game,
            boxscore_teams=all_boxscore_teams,
            boxscore_players=all_boxscore_players,
            pbp_events=all_pbp_events,
            shots=all_shots,
            videos=all_videos,
            boxscore_path=f"data/demo/boxscores/{Path(boxscore_file).name}" if boxscore_file else None,
            pbp_path=f"data/demo/pbp/{Path(pbp_file).name}" if pbp_file else None,
            video_path="data/video/demo_tactical_match.mp4" if video_file else None,
        )

        game_sources = validation_output["game_sources"]
        val_logs = validation_output["validation_logs"]
        conflicts = validation_output["conflicts"]

        # 5. Persist to DuckDB
        self._persist_to_duckdb(
            game_id=game_id,
            provenances=provenances,
            games=all_games,
            game_sources=game_sources,
            game_rosters=all_game_rosters,
            boxscore_teams=all_boxscore_teams,
            boxscore_players=all_boxscore_players,
            pbp_events=all_pbp_events,
            shots=all_shots,
            lineup_stints=all_lineup_stints,
            videos=all_videos,
            video_syncs=all_video_syncs,
            aliases=all_aliases,
            conflicts=conflicts,
            val_logs=val_logs,
        )

        # 6. Save normalized / validated Parquet files
        self._export_parquets(game_id)

        return {
            "game_id": game_id,
            "sources": game_sources.model_dump(),
            "validation_status": game_sources.validation_status,
            "overall_quality": game_sources.overall_quality,
            "completeness_score": game_sources.completeness_score,
            "counts": {
                "boxscore_players": len(all_boxscore_players),
                "pbp_events": len(all_pbp_events),
                "shots": len(all_shots),
                "videos": len(all_videos),
                "conflicts": len(conflicts),
                "validation_logs": len(val_logs),
            }
        }

    def _persist_to_duckdb(self, game_id: str, **kwargs):
        """Insert records into DuckDB without destructive overwriting."""
        # Ensure default competition and season exist
        comp_records = [{"competition_id": "CMP_U16_REGIONAL", "name": "U16 Regional League", "gender": "MALE", "age_category": "U16", "country": "DEU", "governing_body": "DBB", "created_at": datetime.now(timezone.utc)}]
        season_records = [{"season_id": "SEA_2024_2025", "competition_id": "CMP_U16_REGIONAL", "name": "2024-2025"}]
        
        try:
            self.db.insert_records("competition", comp_records)
            self.db.insert_records("season", season_records)
        except Exception:
            pass  # Already exists

        # Teams & Players from Resolver
        teams_records = [t.model_dump() for t in self.resolver.teams.values()]
        players_records = [p.model_dump() for p in self.resolver.players.values()]
        try:
            if teams_records:
                self.db.insert_records("team", teams_records)
            if players_records:
                self.db.insert_records("player", players_records)
        except Exception:
            pass

        # Provenance
        if kwargs.get("provenances"):
            self.db.insert_records("source_provenance", [p.model_dump() for p in kwargs["provenances"]])

        # Game & GameSources
        if kwargs.get("games"):
            self.db.insert_records("game", [g.model_dump() for g in kwargs["games"]])
        if kwargs.get("game_sources"):
            self.db.insert_records("game_sources", [kwargs["game_sources"].model_dump()])

        # Boxscore & Rosters
        if kwargs.get("game_rosters"):
            self.db.insert_records("game_roster", [r.model_dump() for r in kwargs["game_rosters"]])
        if kwargs.get("boxscore_teams"):
            self.db.insert_records("boxscore_team", [t.model_dump() for t in kwargs["boxscore_teams"]])
        if kwargs.get("boxscore_players"):
            self.db.insert_records("boxscore_player", [p.model_dump() for p in kwargs["boxscore_players"]])

        # PBP & Shots
        if kwargs.get("pbp_events"):
            self.db.insert_records("pbp_event", [e.model_dump() for e in kwargs["pbp_events"]])
        if kwargs.get("shots"):
            self.db.insert_records("shot", [s.model_dump() for s in kwargs["shots"]])

        # Videos & Sync
        if kwargs.get("videos"):
            self.db.insert_records("video", [v.model_dump() for v in kwargs["videos"]])
        if kwargs.get("video_syncs"):
            self.db.insert_records("video_event_sync", [s.model_dump() for s in kwargs["video_syncs"]])

        # Aliases, Conflicts, Validation Logs
        if kwargs.get("aliases"):
            self.db.insert_records("entity_alias", [a.model_dump() for a in kwargs["aliases"]])
        if kwargs.get("conflicts"):
            self.db.insert_records("source_conflict_log", [c.model_dump() for c in kwargs["conflicts"]])
        if kwargs.get("val_logs"):
            self.db.insert_records("validation_log", [l.model_dump() for l in kwargs["val_logs"]])

    def _export_parquets(self, game_id: str):
        """Export game data to normalized and validated Parquet lakehouse directories."""
        if getattr(self.db, "db_path", None) == ":memory:":
            return
        for table in ["boxscore_player", "boxscore_team", "pbp_event", "shot", "video", "validation_log", "game_sources"]:
            if self.db.get_table_count(table) > 0:
                pqt_path = Settings.NORMALIZED_DIR / f"{table}.parquet"
                self.db.export_to_parquet(table, pqt_path)
