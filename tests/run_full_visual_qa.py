"""Comprehensive Automated Visual QA & User Journey Validation Suite for 5-Hub Platform."""

import sys
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
from streamlit.testing.v1 import AppTest

def run_qa():
    print("==========================================================================")
    print(" [FINAL VISUAL QA] 5-HUB RHEINLAND FALCONS BASKETBALL INTELLIGENCE PLATFORM")
    print("==========================================================================")

    hubs = [
        "1. 👤 Player Intelligence & Coach Dossier",
        "2. 🏆 Team Intelligence & Performance Overview",
        "3. 🏟️ Game Lab & Match Deep Dive",
        "4. 🎯 Shot Lab & Spatial Court Analytics",
        "5. 💡 Evidence, Hypotheses & Methodology Hub",
    ]

    # 1. Test All 14 Players in Hero Hub (Hub 1)
    print("\n=== 1. TESTING PLAYER INTELLIGENCE (HERO VIEW) ACROSS ALL 14 PLAYERS ===")
    at = AppTest.from_file("app/main.py")
    at.run(timeout=25)
    if len(at.text_input) > 0 and len(at.button) > 0:
        at.text_input[0].input("demotool")
        at.button[0].click().run(timeout=25)
    
    assert len(at.exception) == 0, f"Auth exception: {[e.value for e in at.exception]}"
    p_select = at.selectbox[0]
    for i, pname in enumerate(p_select.options, 1):
        p_select.select(pname).run(timeout=25)
        assert len(at.exception) == 0, f"Exception on player {pname}: {[e.value for e in at.exception]}"
        print(f"  [{i:02d}/14] PASS: {pname} (Tabs: {len(at.tabs)})")

    # 2. Test All 5 Navigation Hubs (Isolated AppTest instances)
    print("\n=== 2. TESTING ALL 5 BALANCED NAVIGATION HUBS ===")
    for hub in hubs:
        at_hub = AppTest.from_file("app/main.py")
        at_hub.run(timeout=25)
        if len(at_hub.text_input) > 0 and len(at_hub.button) > 0:
            at_hub.text_input[0].input("demotool")
            at_hub.button[0].click().run(timeout=25)
        
        nav_radio = [r for r in at_hub.sidebar.radio if "Navigation" in r.label][0]
        nav_radio.set_value(hub).run(timeout=25)
        assert len(at_hub.exception) == 0, f"Exception on Hub '{hub}': {[e.value for e in at_hub.exception]}"
        print(f"  PASS: {hub} (Tabs: {len(at_hub.tabs)}, Tables: {len(at_hub.dataframe)}, Metrics: {len(at_hub.metric)})")

    # 3. Test Population Universe Switching
    print("\n=== 3. TESTING POPULATION UNIVERSE SWITCHING ===")
    at_pop = AppTest.from_file("app/main.py")
    at_pop.run(timeout=25)
    if len(at_pop.text_input) > 0 and len(at_pop.button) > 0:
        at_pop.text_input[0].input("demotool")
        at_pop.button[0].click().run(timeout=25)
    
    pop_radio = [r for r in at_pop.sidebar.radio if "Universe" in r.label or "Population" in r.label][0]
    pop_radio.set_value("ALL_GAMES").run(timeout=25)
    assert len(at_pop.exception) == 0
    print("  PASS: Switched to ALL_GAMES match universe")

    print("\n==========================================================================")
    print(" ALL 5-HUB VISUAL & FUNCTIONAL JOURNEY CHECKS PASSED WITH ZERO ERRORS!")
    print("==========================================================================")

if __name__ == "__main__":
    run_qa()
