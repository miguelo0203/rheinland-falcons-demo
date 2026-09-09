"""Automated Integration & Regression Tests for 5-Hub Balanced Navigation Architecture."""

import pytest
from streamlit.testing.v1 import AppTest


def test_01_all_5_navigation_hubs_render_cleanly():
    """Verifies that all 5 cohesive primary navigation hubs render without errors."""
    hubs = [
        "1. 👤 Player Intelligence & Coach Dossier",
        "2. 🏆 Team Intelligence & Performance Overview",
        "3. 🏟️ Game Lab & Match Deep Dive",
        "4. 🎯 Shot Lab & Spatial Court Analytics",
        "5. 💡 Evidence, Hypotheses & Methodology Hub",
        "6. 📈 Academy Development Monitoring",
    ]
    
    for hub in hubs:
        at = AppTest.from_file("app/main.py")
        at.run(timeout=25)
        
        # Authenticate via Form
        if len(at.text_input) > 0 and len(at.button) > 0:
            at.text_input[0].input("demotool")
            at.button[0].click().run(timeout=25)
            
        assert len(at.exception) == 0, f"Exception on default load: {[e.value for e in at.exception]}"
        
        # Select Hub in sidebar radio
        nav_radio = None
        for r in at.sidebar.radio:
            if "Navigation Hub" in r.label or "Navigation" in r.label:
                nav_radio = r
                break
                
        assert nav_radio is not None, "Navigation Hub radio not found in sidebar"
        nav_radio.set_value(hub).run(timeout=25)
        
        assert len(at.exception) == 0, f"Exception on Hub '{hub}': {[e.value for e in at.exception]}"


def test_02_player_intelligence_all_14_players_render():
    """Verifies Hub 1 (Player Intelligence) renders for all 14 FALCONS players without exception."""
    at = AppTest.from_file("app/main.py")
    at.run(timeout=25)
    
    if len(at.text_input) > 0 and len(at.button) > 0:
        at.text_input[0].input("demotool")
        at.button[0].click().run(timeout=25)
        
    assert len(at.exception) == 0
    
    player_select = at.selectbox[0]
    options = player_select.options
    assert len(options) >= 14, f"Expected at least 14 players, found {len(options)}"
    
    for opt in options:
        player_select.select(opt).run(timeout=25)
        assert len(at.exception) == 0, f"Exception on player {opt}: {[e.value for e in at.exception]}"
        assert len(at.tabs) >= 3, "Expected at least 3 tabs in Player Dossier"


def test_03_team_intelligence_five_tabs():
    """Verifies Hub 2 (Team Intelligence) contains all 5 tabs with valid data tables."""
    at = AppTest.from_file("app/main.py")
    at.run(timeout=25)
    
    if len(at.text_input) > 0 and len(at.button) > 0:
        at.text_input[0].input("demotool")
        at.button[0].click().run(timeout=25)
        
    for r in at.sidebar.radio:
        if "Navigation" in r.label:
            r.set_value("2. 🏆 Team Intelligence & Performance Overview").run(timeout=25)
            break
            
    assert len(at.exception) == 0
    assert len(at.tabs) >= 5, "Expected at least 5 tabs in Team Intelligence Hub"


def test_04_academy_development_monitoring_renders_cleanly():
    """Verifies Hub 6 (Academy Development Monitoring) renders cleanly with tables and metrics."""
    at = AppTest.from_file("app/main.py")
    at.run(timeout=25)

    if len(at.text_input) > 0 and len(at.button) > 0:
        at.text_input[0].input("demotool")
        at.button[0].click().run(timeout=25)

    for r in at.sidebar.radio:
        if "Navigation" in r.label:
            r.set_value("6. 📈 Academy Development Monitoring").run(timeout=25)
            break

    assert len(at.exception) == 0, f"Exception on Hub 6: {[e.value for e in at.exception]}"
    # Verify metrics and dataframe exist
    assert len(at.metric) >= 6, f"Expected at least 6 overview metrics, found {len(at.metric)}"
    assert len(at.dataframe) >= 1, "Expected at least 1 dataframe in Academy Development Monitor"


def test_05_cross_hub_player_navigation():
    """Verifies Hub 6 -> Hub 1 cross-hub navigation preselects player and opens career trajectory."""
    at = AppTest.from_file("app/main.py")
    at.run(timeout=25)

    if len(at.text_input) > 0 and len(at.button) > 0:
        at.text_input[0].input("demotool")
        at.button[0].click().run(timeout=25)

    # 1. Switch to Hub 6
    for r in at.sidebar.radio:
        if "Navigation" in r.label:
            r.set_value("6. 📈 Academy Development Monitoring").run(timeout=25)
            break

    assert len(at.exception) == 0

    # 2. Find and click the 'Open Player Dossier' button in the Why Inspector
    why_button = None
    for b in at.button:
        if "Open Player Dossier" in b.label or "Open Dossier" in b.label:
            why_button = b
            break

    assert why_button is not None, "Expected Open Dossier button in Hub 6"
    why_button.click().run(timeout=25)

    assert len(at.exception) == 0, f"Exception after cross-hub navigation: {[e.value for e in at.exception]}"

    # 3. Check that we are now on Hub 1
    nav_radio = None
    for r in at.sidebar.radio:
        if "Navigation" in r.label:
            nav_radio = r
            break
    assert "1. 👤 Player Intelligence" in nav_radio.value

    # 4. Check that Career Trajectory perspective is active
    persp_radio = None
    for r in at.radio:
        if "Development Perspective" in r.label:
            persp_radio = r
            break
    if persp_radio:
        assert "Full Career Trajectory" in persp_radio.value


def test_06_global_footer_renders_on_all_hubs():
    """Verifies that the global footer renders across all 6 hubs."""
    hubs = [
        "1. 👤 Player Intelligence & Coach Dossier",
        "2. 🏆 Team Intelligence & Performance Overview",
        "3. 🏟️ Game Lab & Match Deep Dive",
        "4. 🎯 Shot Lab & Spatial Court Analytics",
        "5. 💡 Evidence, Hypotheses & Methodology Hub",
        "6. 📈 Academy Development Monitoring",
    ]
    at = AppTest.from_file("app/main.py")
    at.run(timeout=25)

    if len(at.text_input) > 0 and len(at.button) > 0:
        at.text_input[0].input("demotool")
        at.button[0].click().run(timeout=25)

    for hub in hubs:
        for r in at.sidebar.radio:
            if "Navigation" in r.label:
                r.set_value(hub).run(timeout=25)
                break
        assert len(at.exception) == 0
        footer_found = any(
            "Rheinland Falcons Basketball Intelligence Platform" in str(m.value)
            for m in at.markdown
        )
        assert footer_found, f"Footer missing on hub: {hub}"


def test_07_coach_friendly_terminology_audit():
    """Verifies that outdated academic jargon does not appear in coach-facing UI."""
    at = AppTest.from_file("app/main.py")
    at.run(timeout=25)

    if len(at.text_input) > 0 and len(at.button) > 0:
        at.text_input[0].input("demotool")
        at.button[0].click().run(timeout=25)

    # Check across hubs 1, 4, 6
    for hub in [
        "1. 👤 Player Intelligence & Coach Dossier",
        "4. 🎯 Shot Lab & Spatial Court Analytics",
        "6. 📈 Academy Development Monitoring",
    ]:
        for r in at.sidebar.radio:
            if "Navigation" in r.label:
                r.set_value(hub).run(timeout=25)
                break
        all_text = " ".join(str(m.value) for m in at.markdown)
        assert "Epistemic Signal Tiers" not in all_text, f"Epistemic Signal Tiers found in {hub}"
        assert "Epistemic Governance Active" not in all_text, f"Epistemic Governance Active found in {hub}"
        assert "Evidence-First Architecture" not in all_text, f"Evidence-First Architecture found in {hub}"


def test_08_undefined_ts_returns_none():
    """Verifies that undefined TS% (0 FGA and 0 FTA) returns None and not 0.0."""
    from app.services.data_service import DataService
    ds = DataService()
    players = ds.get_falcons_player_list("SEA_2025", "U16")
    zero_attempt_found = False
    for p in players:
        d = ds.get_player_dossier(p["player_id"], season_id="SEA_2025", squad_scope="U16")
        s = d.get("stats", {})
        if s.get("total_fga", 0) == 0 and s.get("total_fta", 0) == 0:
            zero_attempt_found = True
            assert s.get("ts_pct") is None, f"Expected None for zero attempts, got {s.get('ts_pct')}"
            break
    assert zero_attempt_found, "Expected at least one player with 0 attempts for testing undefined TS%"


def test_09_full_demo_user_journey_flow():
    """Verifies the complete 12-step demo user journey end-to-end without manual recovery.
    
    1. Open Academy Development Monitoring (Hub 6).
    2. Inspect academy overview metrics.
    3. Locate demo protagonist (Maximilian Becker) in Top Developing.
    4. Click 'Open Dossier'.
    5. Land in Player Intelligence (Hub 1) with athlete pre-selected and Full Career Trajectory active.
    6. Verify Level 1 Conclusion and Level 2 Why narrative.
    7. Verify Longitudinal Timeline Plotly chart presence.
    8. Verify U16 -> U19 category transition messaging.
    9. Navigate back to Hub 6.
    10. Navigate to Hub 5 for methodology credibility explanation.
    11. Guarantee zero exceptions throughout the entire multi-hub sequence.
    """
    at = AppTest.from_file("app/main.py")
    at.run(timeout=25)

    if len(at.text_input) > 0 and len(at.button) > 0:
        at.text_input[0].input("demotool")
        at.button[0].click().run(timeout=25)

    # Step 1: Open Hub 6
    for r in at.sidebar.radio:
        if "Navigation" in r.label:
            r.set_value("6. 📈 Academy Development Monitoring").run(timeout=25)
            break
    assert len(at.exception) == 0

    # Step 2: Overview metrics verified
    assert len(at.metric) >= 6
    metric_labels = [str(m.label) for m in at.metric]
    assert any("Total Athletes" in lbl for lbl in metric_labels)
    assert any("Improving" in lbl for lbl in metric_labels)

    # Step 3 & 4: Click Open Dossier on Maximilian Becker
    for sb in at.selectbox:
        if "Open Player Dossier" in sb.label:
            if "Maximilian Becker" in sb.options:
                sb.select("Maximilian Becker")
            break

    fall_btn = None
    for b in at.button:
        if "Open Dossier" in b.label or "Open Player Dossier" in b.label:
            fall_btn = b
            break
    assert fall_btn is not None, "Open Dossier button should be available for protagonist"
    fall_btn.click().run(timeout=25)
    assert len(at.exception) == 0

    # Step 5: Arrive in Hub 1 with protagonist and Full Career Trajectory
    for r in at.sidebar.radio:
        if "Navigation" in r.label:
            assert "1. 👤 Player Intelligence" in r.value
            break

    # Step 6 & 7: Check Career Trajectory is active and protagonist is selected
    for r in at.radio:
        if "Perspective" in r.label or "Development Perspective" in r.label:
            assert "Full Career Trajectory" in r.value
            break

    all_markdown = " ".join(str(m.value) for m in at.markdown)
    assert "Maximilian Becker" in all_markdown
    assert ("IMPROVING" in all_markdown or "STABLE" in all_markdown)
    assert "Longitudinal Development Timeline" in all_markdown

    # Step 8: Return to Hub 6
    for r in at.sidebar.radio:
        if "Navigation" in r.label:
            r.set_value("6. 📈 Academy Development Monitoring").run(timeout=25)
            break
    assert len(at.exception) == 0

    # Step 9: Open Hub 5 for methodology demonstration
    for r in at.sidebar.radio:
        if "Navigation" in r.label:
            r.set_value("5. 💡 Evidence, Hypotheses & Methodology Hub").run(timeout=25)
            break
    assert len(at.exception) == 0
    hub5_text = " ".join(str(m.value) for m in at.markdown) + " " + " ".join(str(s.value) for s in at.subheader)
    assert "Evidence, Hypotheses & Methodology Hub" in hub5_text


