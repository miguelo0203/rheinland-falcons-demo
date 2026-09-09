"""Download all Nuxt chunks and uncover exact API endpoints, match payload formats, and PBP structures."""

import json
import re
import urllib.request
import urllib.parse
from pathlib import Path

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
API_BASE = "https://api.bbl.scb.world/v2"
API_KEYS = {
    "JBBL": "81e03c389456a1d3441cd89ce9703d88",
    "NBBL": "8dc905d70eac940c38313e1284b2d5c0",
}

def fetch_text(url: str, headers: dict = None) -> str:
    req_headers = {"User-Agent": USER_AGENT}
    if headers:
        req_headers.update(headers)
    req = urllib.request.Request(url, headers=req_headers)
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.read().decode("utf-8", errors="replace")

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

def discover_all_chunks():
    print("=== Scanning Nuxt manifest and downloading all chunks ===")
    main_bundle = Path("reports/source_audit/samples/nuxt_bundle_DzMyqwY6.js").read_text(encoding="utf-8")
    
    # Extract chunk hash filenames
    chunk_hashes = set(re.findall(r'["\']([a-zA-Z0-9_\-]+\.js)["\']', main_bundle))
    print(f"Found {len(chunk_hashes)} candidate chunk filenames.")
    
    out_dir = Path("reports/source_audit/samples/chunks")
    out_dir.mkdir(parents=True, exist_ok=True)
    
    api_urls = set()
    
    for ch in sorted(chunk_hashes):
        url = f"https://www.nbbl-basketball.de/_nuxt/{ch}"
        try:
            content = fetch_text(url)
            (out_dir / ch).write_text(content, encoding="utf-8")
            # Scan for API strings in this chunk
            found_apis = re.findall(r'["\'](/[^"\']+)["\']', content)
            for a in found_apis:
                if any(kw in a for kw in ["matches", "teams", "players", "standings", "statistics", "seasons", "schedule", "pbp", "ticker", "boxscore", "live", "competition"]):
                    api_urls.add(a)
        except Exception:
            pass

    print(f"\nDiscovered API Path References across all chunks ({len(api_urls)}):")
    for a in sorted(api_urls):
        print(f"  - {a}")

def test_scb_api_systematically():
    print("\n=== Testing SCB API systematically with JBBL and NBBL keys ===")
    
    # Let's test known match 9995585 and team 2048 and other candidate REST paths
    endpoints_to_test = [
        "/seasons",
        "/teams",
        "/teams/2048",
        "/players",
        "/matches",
        "/matches/9995585",
        "/matches/9995585/boxscore",
        "/matches/9995585/pbp",
        "/matches/9995585/ticker",
        "/matches/9995585/events",
        "/matches/9995585/play-by-play",
        "/matches/9995585/stats",
        "/schedule",
        "/standings",
        "/statistics",
        "/competitions",
        "/leagues",
        "/clubs",
        "/clubs/2048",
    ]
    
    headers = {
        "X-API-KEY": API_KEYS["JBBL"],
        "Accept": "application/json",
    }
    
    results = {}
    for ep in endpoints_to_test:
        url = f"{API_BASE}{ep}"
        try:
            data = fetch_json(url, headers=headers)
            print(f"SUCCESS {url} -> {type(data)}")
            if isinstance(data, dict):
                print(f"   Keys: {list(data.keys())[:10]}")
            elif isinstance(data, list):
                print(f"   Items count: {len(data)}, Sample item keys: {list(data[0].keys()) if len(data) > 0 and isinstance(data[0], dict) else 'primitive'}")
            
            # Save sample
            safe_name = ep.replace("/", "_").strip("_")
            sample_path = Path(f"reports/source_audit/samples/scb_{safe_name}.json")
            sample_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
            results[ep] = "OK"
        except urllib.error.HTTPError as e:
            print(f"HTTP {e.code} for {url}")
            results[ep] = f"HTTP {e.code}"
        except Exception as e:
            print(f"Error {url}: {e}")
            results[ep] = str(e)

if __name__ == "__main__":
    discover_all_chunks()
    test_scb_api_systematically()
