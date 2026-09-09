"""Investigate schedule, standings, stats, team matches, and historical parameters on the SCB API."""

import json
import urllib.request
import urllib.parse
from pathlib import Path

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
API_BASE = "https://api.bbl.scb.world/v2"
API_KEYS = {
    "JBBL": "81e03c389456a1d3441cd89ce9703d88",
    "NBBL": "8dc905d70eac940c38313e1284b2d5c0",
}

def fetch_json(url: str, headers: dict = None) -> dict:
    req_headers = {"User-Agent": USER_AGENT}
    if headers:
        req_headers.update(headers)
    req = urllib.request.Request(url, headers=req_headers)
    with urllib.request.urlopen(req, timeout=15) as resp:
        content = resp.read().decode("utf-8", errors="replace")
        try:
            return json.loads(content)
        except Exception:
            return {"raw": content}

def explore_schedule_and_standings():
    print("=== Exploring Schedule, Standings, Teams, and Historical Queries ===")
    
    headers_jbbl = {"X-API-KEY": API_KEYS["JBBL"], "Accept": "application/json"}
    
    # Test query params for schedule / standings / matches
    test_queries = [
        # Schedule tests
        "/schedule?seasonId=2025",
        "/schedule?seasonId=2024",
        "/schedule?seasonId=2023",
        "/schedule?season=2025",
        "/schedule?season=2024",
        "/schedule?teamId=2048",
        "/schedule?team=2048",
        "/schedule?group=7",
        "/schedule?stage=ROUND_OF_8",
        # Standings tests
        "/standings?seasonId=2025",
        "/standings?seasonId=2024",
        "/standings?season=2025",
        "/standings?group=7",
        # Team details
        "/team/2048",
        "/teams/2048",
        "/team/2048/schedule",
        "/team/2048/matches",
        "/team/2048/roster",
        "/team/2048/players",
        "/team/2048/stats",
        # Player details
        "/player/58857", # Julian Wagner
        "/players/58857",
        "/player/57052", # master playerId
        "/players/57052",
        # Stats / Leaders
        "/stats",
        "/stats?seasonId=2025",
        "/leaders",
        "/leaders?seasonId=2025",
        "/statistics",
        "/statistics?seasonId=2025",
        # Games list
        "/games",
        "/games?seasonId=2025",
        "/games?teamId=2048",
    ]
    
    for q in test_queries:
        url = f"{API_BASE}{q}"
        try:
            data = fetch_json(url, headers=headers_jbbl)
            print(f"SUCCESS: {q}")
            if isinstance(data, list):
                print(f"   -> List of {len(data)} items. Sample: {data[0] if data else 'empty'}")
            elif isinstance(data, dict):
                print(f"   -> Dict keys: {list(data.keys())[:10]}")
            
            # Save sample
            safe_name = q.replace("/", "_").replace("?", "_").replace("=", "_").strip("_")
            sample_path = Path(f"reports/source_audit/samples/explore_{safe_name}.json")
            sample_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except urllib.error.HTTPError as e:
            # print(f"HTTP {e.code}: {q}")
            pass
        except Exception as e:
            pass

if __name__ == "__main__":
    explore_schedule_and_standings()
