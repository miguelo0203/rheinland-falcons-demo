"""Abstract Base Adapter for Ingestion Pipeline."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel

from python.models.canonical import SourceProvenance
from python.models.enums import SourceType
from python.ingestion.provenance import ProvenanceTracker
from python.ingestion.entity_resolver import EntityResolver


class NormalizedPayload(BaseModel):
    """Container for normalized entities produced by an adapter."""
    provenance: SourceProvenance
    competitions: List[Any] = []
    seasons: List[Any] = []
    teams: List[Any] = []
    players: List[Any] = []
    player_teams: List[Any] = []
    games: List[Any] = []
    game_rosters: List[Any] = []
    boxscore_teams: List[Any] = []
    boxscore_players: List[Any] = []
    pbp_events: List[Any] = []
    shots: List[Any] = []
    lineup_stints: List[Any] = []
    videos: List[Any] = []
    video_event_syncs: List[Any] = []
    aliases: List[Any] = []


class BaseAdapter(ABC):
    """Abstract base class that all data modality adapters must implement."""

    def __init__(
        self,
        source_type: SourceType,
        provider_name: str,
        entity_resolver: Optional[EntityResolver] = None,
        provenance_tracker: Optional[ProvenanceTracker] = None,
    ):
        self.source_type = source_type
        self.provider_name = provider_name
        self.resolver = entity_resolver or EntityResolver()
        self.provenance_tracker = provenance_tracker or ProvenanceTracker()

    @abstractmethod
    def detect(self, file_path: Union[str, Path]) -> bool:
        """Inspect file and return True if this adapter can process it."""
        pass

    @abstractmethod
    def extract(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """Extract raw records into a structured dictionary without mutating data."""
        pass

    @abstractmethod
    def normalize(
        self,
        raw_data: Dict[str, Any],
        file_path: Union[str, Path],
        game_id: Optional[str] = None,
        season_id: Optional[str] = None,
        competition_id: Optional[str] = None,
    ) -> NormalizedPayload:
        """Map raw staging data to canonical Pydantic models."""
        pass
