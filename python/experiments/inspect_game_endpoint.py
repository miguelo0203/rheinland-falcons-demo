"""Test /game/{id} and download C7LJJbUd.js and CAGDsTvq.js for match data and websocket forensics."""

import json
import re
import urllib.request
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

def fetch_text(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.read().decode("utf-8", errors="replace")

# 1. Test /game/9995585
headers = {"X-API-KEY": API_KEYS["JBBL"], "Accept": "application/json"}
print("Fetching /game/9995585 ...")
try:
    game_data = fetch_json(f"{API_BASE}/game/9995585", headers=headers)
    sample_file = Path("reports/source_audit/samples/scb_game_9995585.json")
    sample_file.write_text(json.dumps(game_data, indent=2), encoding="utf-8")
    print(f"SUCCESS /game/9995585! Keys: {list(game_data.keys()) if isinstance(game_data, dict) else len(game_data)}")
    if isinstance(game_data, dict) and "data" in game_data:
        print(f"   data keys: {list(game_data['data'].keys()) if isinstance(game_data['data'], dict) else len(game_data['data'])}")
except Exception as e:
    print(f"Error fetching /game/9995585: {e}")

# 2. Download and inspect C7LJJbUd.js and CAGDsTvq.js
for js in ["C7LJJbUd.js", "CAGDsTvq.js", "BFR8XOnm.js", "DxL7g_Da.js"]:
    url = f"https://www.nbbl-basketball.de/_nuxt/{js}"
    try:
        content = fetch_text(url)
        (Path("reports/source_audit/samples/components") / js).write_text(content, encoding="utf-8")
        print(f"Downloaded {js} ({len(content)} chars)")
    except Exception as e:
        print(f"Error downloading {js}: {e}")
