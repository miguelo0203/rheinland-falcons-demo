"""Tests for Coach UI & Evidence Presentation Layer.

Verifies:
- Clean HTML rendering with zero NaN / None leakage
- Stability badge generation across all four tiers
- Executive KPI card formatting
- Evidence card structured progressive disclosure
- Film hypothesis formatting with explicit non-claim banner
- Provenance card metadata display
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, ".")

from app.components.ui import (
    get_custom_css,
    render_badge,
    render_kpi_card,
    render_evidence_card,
    render_film_card,
    render_provenance_card
)

def test_01_custom_css_structure():
    """Verifies that custom CSS contains key class selectors."""
    css = get_custom_css()
    assert ".hm-header-container" in css
    assert ".hm-kpi-card" in css
    assert ".hm-evidence-card" in css
    assert ".hm-film-card" in css
    assert ".hm-provenance-box" in css
    assert "#0284c7" in css # FALCONS blue

def test_02_stability_badge_tiers():
    """Verifies that all four stability tiers render distinct badge classes."""
    b_est = render_badge("ESTABLISHED_SIGNAL")
    assert "hm-badge-established" in b_est
    assert "ESTABLISHED SIGNAL" in b_est

    b_usa = render_badge("USABLE_SIGNAL")
    assert "hm-badge-usable" in b_usa
    assert "USABLE SIGNAL" in b_usa

    b_eme = render_badge("EMERGING_SIGNAL")
    assert "hm-badge-emerging" in b_eme
    assert "EMERGING SIGNAL" in b_eme

    b_des = render_badge("DESCRIPTIVE_ONLY")
    assert "hm-badge-descriptive" in b_des
    assert ("LOW SAMPLE" in b_des or "DESCRIPTIVE ONLY" in b_des)

def test_03_kpi_card_rendering():
    """Verifies that KPI cards correctly assemble value, percentile, stability, and volume."""
    html = render_kpi_card(
        label="SCORING",
        value="25.0 PTS/40",
        percentile_text="85th percentile",
        stability_tier="ESTABLISHED_SIGNAL",
        volume_text="297 PTS · 474.9 MIN · 15.6 PPG"
    )
    assert "SCORING" in html
    assert "25.0 PTS/40" in html
    assert "85th percentile" in html
    assert "ESTABLISHED SIGNAL" in html
    assert "297 PTS · 474.9 MIN" in html
    assert "NaN" not in html
    assert "None" not in html

def test_04_evidence_card_rendering():
    """Verifies structured progressive disclosure in evidence cards."""
    finding = {
        "category": "Perimeter Shooting",
        "headline": "48.9% 3P (23/47) | 100th %ile",
        "observation": "Converted 23 of 47 three-point attempts (48.9% 3P, 2.5 3PA/G).",
        "context": "Ranks at the 100th percentile in 3P% among 34 qualified JBBL peers from season 2025/26 (Median: 25.0%).",
        "volume_note": "Three-point attempts account for 21.9% of total field goal attempts (47/215 FGA).",
        "interpretation": "Strong observed conversion efficiency, but 47 attempts classify the percentage as an emerging rather than established signal.",
        "stability_tier": "EMERGING_SIGNAL"
    }
    html = render_evidence_card(finding)
    assert "Perimeter Shooting" in html
    assert "48.9% 3P (23/47)" in html
    assert "1. Observed Production" in html
    assert "2. League Benchmark Context" in html
    assert "3. Volume & Opportunity Diet" in html
    assert "EMERGING SIGNAL" in html
    assert "NaN" not in html
    assert "None" not in html

def test_05_film_card_rendering():
    """Verifies video hypothesis card rendering and explicit non-claim banner."""
    finding = {
        "category": "Perimeter Shooting",
        "headline": "48.9% 3P (23/47)",
        "observation": "Converted 23 of 47 3PT.",
        "film_question": "Inspect whether 3-point makes stem predominantly from assisted catch-and-shoot looks vs pull-ups."
    }
    html = render_film_card(finding)
    assert "VIDEO HYPOTHESIS — NOT A STATISTICAL CLAIM" in html
    assert "catch-and-shoot" in html
    assert "Grounded in evidence:" in html
    assert "NaN" not in html
    assert "None" not in html

def test_06_provenance_card_rendering():
    """Verifies provenance card metadata integrity."""
    bench_meta = {
        "season_id": "SEA_2025",
        "competition_id": "CMP_JBBL",
        "game_type": "OFFICIAL",
        "min_minutes": 100.0,
        "qualified_pop_size": 34
    }
    freshness = {"latest_game_date": "2026-03-15"}
    html = render_provenance_card(bench_meta, freshness)
    assert "N = 34 qualified JBBL players" in html
    assert "Season 2025" in html
    assert "OFFICIAL matches only" in html
    assert "Minimum 100 regulation minutes" in html
    assert "2026-03-15" in html
    assert "NaN" not in html
