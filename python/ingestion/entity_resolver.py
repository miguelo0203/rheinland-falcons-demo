"""Entity Resolution and Alias Management Engine."""

import re
import unicodedata
from difflib import SequenceMatcher
from typing import Dict, List, Optional, Tuple

from python.models.canonical import EntityAlias, Player, Team, Competition
from python.ingestion.provenance import generate_id
from python.config import Settings


def normalize_string(s: str) -> str:
    """Normalize string by removing accents, special characters, and uppercase."""
    if not s:
        return ""
    # Normalize unicode characters (e.g., ä -> a, é -> e)
    nfkd_form = unicodedata.normalize("NFKD", s)
    only_ascii = "".join([c for c in nfkd_form if not unicodedata.combining(c)])
    # Remove non-alphanumeric except spaces
    cleaned = re.sub(r"[^\w\s]", " ", only_ascii)
    # Collapse whitespace
    return re.sub(r"\s+", " ", cleaned).strip().upper()


def string_similarity(a: str, b: str) -> float:
    """Compute normalized Levenshtein-like similarity ratio between two strings [0.0, 1.0]."""
    norm_a = normalize_string(a)
    norm_b = normalize_string(b)
    if norm_a == norm_b:
        return 1.0
    return SequenceMatcher(None, norm_a, norm_b).ratio()


class EntityResolver:
    """Resolves external provider names and IDs to stable canonical internal IDs."""

    def __init__(
        self,
        similarity_threshold: Optional[float] = None,
        review_threshold: Optional[float] = None,
    ):
        cfg = Settings.ENTITY_RESOLUTION
        self.similarity_threshold = similarity_threshold or cfg.get("similarity_threshold", 0.85)
        self.review_threshold = review_threshold or cfg.get("flag_ambiguous_below", 0.90)

        # In-memory entity registries
        self.players: Dict[str, Player] = {}
        self.teams: Dict[str, Team] = {}
        self.competitions: Dict[str, Competition] = {}
        self.aliases: Dict[str, EntityAlias] = {}

    def resolve_team(
        self,
        raw_name: str,
        provider: str = "GENERIC",
        provider_team_id: Optional[str] = None,
        club_name: Optional[str] = None,
        age_category: Optional[str] = None,
    ) -> Tuple[str, EntityAlias]:
        """Resolve a team to a canonical team_id."""
        norm_name = normalize_string(raw_name)
        
        # 1. Exact alias match
        alias_key = f"TEAM:{provider}:{provider_team_id or norm_name}"
        if alias_key in self.aliases:
            return self.aliases[alias_key].canonical_id, self.aliases[alias_key]

        # 2. Check existing canonical teams
        best_team_id = None
        best_score = 0.0

        for t_id, team in self.teams.items():
            score = string_similarity(raw_name, team.canonical_name)
            if score > best_score:
                best_score = score
                best_team_id = t_id

        if best_team_id and best_score >= self.similarity_threshold:
            requires_review = (best_score < self.review_threshold)
            alias = EntityAlias(
                alias_id=generate_id("ALS"),
                entity_type="TEAM",
                canonical_id=best_team_id,
                source_provider=provider,
                source_id=provider_team_id,
                source_name_raw=raw_name,
                normalized_name=norm_name,
                match_confidence=round(best_score, 4),
                requires_review=requires_review,
            )
            self.aliases[alias_key] = alias
            return best_team_id, alias

        # 3. Create new canonical team
        new_team_id = generate_id("TEM")
        new_team = Team(
            team_id=new_team_id,
            canonical_name=raw_name.strip(),
            club_name=club_name or raw_name.strip(),
            age_category=age_category,
        )
        self.teams[new_team_id] = new_team

        alias = EntityAlias(
            alias_id=generate_id("ALS"),
            entity_type="TEAM",
            canonical_id=new_team_id,
            source_provider=provider,
            source_id=provider_team_id,
            source_name_raw=raw_name,
            normalized_name=norm_name,
            match_confidence=1.0,
            requires_review=False,
        )
        self.aliases[alias_key] = alias
        return new_team_id, alias

    def resolve_player(
        self,
        raw_name: str,
        provider: str = "GENERIC",
        provider_player_id: Optional[str] = None,
        jersey_number: Optional[str] = None,
        team_id: Optional[str] = None,
        listed_position: Optional[str] = None,
    ) -> Tuple[str, EntityAlias]:
        """Resolve a player to a canonical player_id with ambiguity detection."""
        norm_name = normalize_string(raw_name)
        alias_key = f"PLAYER:{provider}:{provider_player_id or norm_name}:{jersey_number or ''}"

        if alias_key in self.aliases:
            return self.aliases[alias_key].canonical_id, self.aliases[alias_key]

        # Check existing canonical players
        best_player_id = None
        best_score = 0.0

        for p_id, player in self.players.items():
            score = string_similarity(raw_name, player.canonical_name)
            if score > best_score:
                best_score = score
                best_player_id = p_id

        if best_player_id and best_score >= self.similarity_threshold:
            requires_review = (best_score < self.review_threshold)
            alias = EntityAlias(
                alias_id=generate_id("ALS"),
                entity_type="PLAYER",
                canonical_id=best_player_id,
                source_provider=provider,
                source_id=provider_player_id,
                source_name_raw=raw_name,
                normalized_name=norm_name,
                jersey_number=jersey_number,
                match_confidence=round(best_score, 4),
                requires_review=requires_review,
            )
            self.aliases[alias_key] = alias
            return best_player_id, alias

        # Create new canonical player (position is stored as listed_position, never inferred)
        new_player_id = generate_id("PLY")
        parts = raw_name.strip().split(" ", 1)
        first_name = parts[0] if len(parts) > 1 else None
        last_name = parts[1] if len(parts) > 1 else parts[0]

        new_player = Player(
            player_id=new_player_id,
            canonical_name=raw_name.strip(),
            first_name=first_name,
            last_name=last_name,
            listed_position=listed_position,
        )
        self.players[new_player_id] = new_player

        alias = EntityAlias(
            alias_id=generate_id("ALS"),
            entity_type="PLAYER",
            canonical_id=new_player_id,
            source_provider=provider,
            source_id=provider_player_id,
            source_name_raw=raw_name,
            normalized_name=norm_name,
            jersey_number=jersey_number,
            match_confidence=1.0,
            requires_review=False,
        )
        self.aliases[alias_key] = alias
        return new_player_id, alias
