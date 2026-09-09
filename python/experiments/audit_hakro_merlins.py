"""Test multi-season match retrieval and Rheinland Falcons Basketball match history."""

import json
import urllib.request
from pathlib import Path

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
API_BASE = "https://api.bbl.scb.world/v2"
API_KEY_JBBL = "81e03c389456a1d3441cd89ce9703d88"

def fetch_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "X-API-KEY": API_KEY_JBBL, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))

def audit_falcons_falcons():
    print("=== Auditing Rheinland Falcons Basketball (Team ID: 2048) in JBBL ===")
    
    # 1. Fetch team details
    team_info = fetch_json(f"{API_BASE}/team/2048")
    print(f"Team Name: {team_info.get('name')}")
    print(f"Available Seasons for Team: {team_info.get('availableSeasons')}")
    
    # 2. Find all matches involving Rheinland Falcons across all seasons
    falcons_matches = []
    
    for season in [2025, 2024, 2023, 2022, 2021, 2020, 2019, 2018, 2017]:
        schedule = fetch_json(f"{API_BASE}/schedule?seasonId={season}")
        matches_in_season = [
            m for m in schedule
            if (m.get("homeTeam", {}).get("id") == 2048 or m.get("guestTeam", {}).get("id") == 2048)
        ]
        print(f"Season {season}: Found {len(matches_in_season)} matches for Rheinland Falcons Basketball")
        for m in matches_in_season[:2]:
            print(f"   Match {m.get('id')}: {m.get('homeTeam', {}).get('short')} vs {m.get('guestTeam', {}).get('short')} - Final: {m.get('results', {}).get('finalScore')} on {m.get('scheduledTime')}")
            falcons_matches.append({
                "season": season,
                "match_id": m.get("id"),
                "round": m.get("round"),
                "home": m.get("homeTeam", {}).get("name"),
                "away": m.get("guestTeam", {}).get("name"),
                "date": m.get("scheduledTime"),
                "final_score": m.get("results", {}).get("finalScore"),
                "quarter_scores": m.get("results", {}).get("scores"),
            })

    out_path = Path("reports/source_audit/samples/falcons_falcons_matches.json")
    out_path.write_text(json.dumps(falcons_matches, indent=2), encoding="utf-8")
    print(f"\nSaved {len(falcons_matches)} Rheinland Falcons match records to {out_path}")

if __name__ == "__main__":
    audit_falcons_falcons()
