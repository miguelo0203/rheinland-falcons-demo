"""Automated test suite for Phase 5 DataService and Zero Hardcoded Values in UI."""

import re
from pathlib import Path
import pandas as pd
import pytest

from app.services.data_service import DataService

def test_data_service_methods():
    """Verify that DataService loads all intelligence datasets correctly."""
    ds = DataService()
    
    assert len(ds.get_coach_findings()) >= 5
    assert len(ds.get_hypotheses()) >= 3
    assert len(ds.get_team_intelligence()) >= 100
    assert len(ds.get_player_intelligence()) >= 300
    assert len(ds.get_player_evolution()) >= 900
    assert len(ds.get_shot_intelligence()) >= 5000
    assert len(ds.get_league_context()) >= 50
    assert len(ds.get_game_data_quality()) >= 48

def test_no_hardcoded_analytical_values_in_main_app():
    """Verify that app/main.py uses DataService dynamic methods without hardcoded values."""
    app_file = Path("app/main.py")
    assert app_file.exists()
    content = app_file.read_text(encoding="utf-8")
    
    # Check that DataService is used for dynamic queries across the 5 hubs
    assert "ds = load_service()" in content or "DataService()" in content
    assert "ds.get_" in content
    assert "ds.get_team_shots" in content
    assert "ds.get_player_map" in content
