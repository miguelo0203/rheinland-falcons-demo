"""Test historical season coverage on SCB API from 2010 to 2026 for both JBBL and NBBL."""

import json
import urllib.request
from pathlib import Path

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
API_BASE = "https://api.bbl.scb.world/v2"
API_KEYS = {
    "JBBL": "81e03c389456a1d3441cd89ce9703d88",
    "NBBL": "8dc905d70eac940c38313e1284b2d5c0",
}

def fetch_json(url: str, headers: dict) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, **headers, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))

def test_historical_seasons():
    report = []
    
    for league, key in API_KEYS.items():
        headers = {"X-API-KEY": key}
        print(f"\n==================== {league} HISTORICAL AUDIT ====================")
        
        for year in range(2014, 2027):
            # Test Schedule
            schedule_count = 0
            schedule_accessible = False
            try:
                data = fetch_json(f"{API_BASE}/schedule?seasonId={year}", headers)
                if isinstance(data, list) and len(data) > 0:
                    schedule_count = len(data)
                    schedule_accessible = True
            except Exception:
                pass

            # Test Standings
            standings_count = 0
            standings_accessible = False
            try:
                data_st = fetch_json(f"{API_BASE}/standings?seasonId={year}", headers)
                if isinstance(data_st, list) and len(data_st) > 0:
                    standings_count = len(data_st)
                    standings_accessible = True
            except Exception:
                pass

            # Test Teams
            teams_count = 0
            try:
                data_tm = fetch_json(f"{API_BASE}/teams?seasonId={year}", headers)
                if isinstance(data_tm, list) and len(data_tm) > 0:
                    teams_count = len(data_tm)
            except Exception:
                pass

            status_str = f"Season {year}: Accessible={schedule_accessible}, Matches={schedule_count}, StandingsGroups={standings_count}, Teams={teams_count}"
            print(status_str)
            report.append({
                "league": league,
                "season": year,
                "accessible": schedule_accessible or standings_accessible,
                "matches": schedule_count,
                "standings_entries": standings_count,
                "teams": teams_count,
            })

    out_path = Path("reports/source_audit/samples/historical_coverage.json")
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

if __name__ == "__main__":
    test_historical_seasons()
