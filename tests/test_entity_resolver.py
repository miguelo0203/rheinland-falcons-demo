"""Unit tests for Entity Resolution and Ambiguity Detection in Sandbox."""

import pytest
from python.ingestion.entity_resolver import (
    EntityResolver,
    normalize_string,
    string_similarity,
)


def test_string_normalization():
    """Test accent and character normalization."""
    assert normalize_string("Lukas Müller") == "LUKAS MULLER"
    assert normalize_string("Éric García") == "ERIC GARCIA"
    assert normalize_string("  Falcons   Falcons  Rheinland  ") == "FALCONS FALCONS RHEINLAND"


def test_entity_resolution_team():
    """Test team resolution and alias creation."""
    resolver = EntityResolver()
    team_id_1, alias_1 = resolver.resolve_team("Rheinland Falcons U16")
    team_id_2, alias_2 = resolver.resolve_team("Rheinland Falcons U16")

    assert team_id_1 == team_id_2
    assert alias_1.canonical_id == team_id_1
    assert alias_2.canonical_id == team_id_1


def test_entity_resolution_player_fuzzy_and_review_flag():
    """Test player matching with typos and ambiguous review flags."""
    # Set review threshold to 0.98 so that Lukas Schmidtt (0.963) is matched but flagged for review
    resolver = EntityResolver(similarity_threshold=0.80, review_threshold=0.98)
    p_id_1, alias_1 = resolver.resolve_player("Lukas Schmidt", jersey_number="7")
    
    # Fuzzy match with typo
    p_id_2, alias_2 = resolver.resolve_player("Lukas Schmidtt", jersey_number="7")
    assert p_id_1 == p_id_2
    # Flagged for review because 0.80 <= similarity < 0.98
    assert alias_2.requires_review is True

    # Position independence: position is never inferred silently
    p_id_3, _ = resolver.resolve_player("New Guard", listed_position=None)
    assert resolver.players[p_id_3].listed_position is None
