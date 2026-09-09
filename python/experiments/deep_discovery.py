"""Deep forensic discovery of Nuxt frontend bundles, routes, and SCB backend API."""

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

def fetch_text(url: str, headers: dict = None) -> str:
    req_headers = {"User-Agent": USER_AGENT}
    if headers:
        req_headers.update(headers)
    req = urllib.request.Request(url, headers=req_headers)
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.read().decode("utf-8", errors="replace")

def test_api_endpoints():
    print("=== Testing API Endpoints on api.bbl.scb.world/v2 ===")
    
    # Common REST endpoints to test with API key header or query param
    test_endpoints = [
        "/",
        "/seasons",
        "/competitions",
        "/leagues",
        "/teams",
        "/matches",
        "/games",
        "/players",
        "/standings",
        "/statistics",
        "/clubs",
        "/rounds",
        "/groups",
    ]
    
    for league, key in API_KEYS.items():
        print(f"\n--- Testing League: {league} with Key: {key} ---")
        # Test headers: X-API-KEY, Authorization, Api-Key, etc. or query ?apiKey= or ?key= or ?api_key=
        for ep in test_endpoints:
            # Method 1: header
            for header_name in ["apiKey", "X-API-KEY", "x-api-key", "api-key", "Authorization"]:
                header_val = key if header_name != "Authorization" else f"Bearer {key}"
                try:
                    url = f"{API_BASE}{ep}"
                    data = fetch_json(url, headers={header_name: header_val})
                    print(f"SUCCESS [Header {header_name}] {url} -> {type(data)} keys/len: {list(data.keys()) if isinstance(data, dict) else len(data)}")
                    # Save sample
                    sample_file = Path(f"reports/source_audit/samples/api_{league}_{ep.strip('/')}_{header_name}.json")
                    sample_file.parent.mkdir(parents=True, exist_ok=True)
                    sample_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
                    break
                except urllib.error.HTTPError as e:
                    # print(f"HTTP {e.code} for {ep} with {header_name}")
                    pass
                except Exception as e:
                    pass

            # Method 2: query param
            for q_param in ["apiKey", "key", "api_key", "token"]:
                try:
                    url = f"{API_BASE}{ep}?{q_param}={key}"
                    data = fetch_json(url)
                    print(f"SUCCESS [Query ?{q_param}] {url} -> {type(data)} keys/len: {list(data.keys()) if isinstance(data, dict) else len(data)}")
                    sample_file = Path(f"reports/source_audit/samples/api_{league}_{ep.strip('/')}_query.json")
                    sample_file.parent.mkdir(parents=True, exist_ok=True)
                    sample_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
                    break
                except Exception:
                    pass

def inspect_nuxt_bundles():
    print("\n=== Inspecting Nuxt Javascript Bundles ===")
    home_html = fetch_text("https://www.nbbl-basketball.de/")
    
    # Extract all js files
    js_files = re.findall(r'src=["\'](/_nuxt/[^"\']+\.js)["\']', home_html)
    print(f"Found JS bundles: {js_files}")
    
    manifest_urls = set()
    for js_rel in js_files:
        js_url = f"https://www.nbbl-basketball.de{js_rel}"
        js_content = fetch_text(js_url)
        print(f"Downloaded {js_url} ({len(js_content)} chars)")
        
        # Save bundle
        bundle_path = Path(f"reports/source_audit/samples/nuxt_bundle_{Path(js_rel).name}")
        bundle_path.parent.mkdir(parents=True, exist_ok=True)
        bundle_path.write_text(js_content, encoding="utf-8")
        
        # Search for routes
        routes = re.findall(r'path:\s*["\']([^"\']+)["\']', js_content)
        print(f"Found {len(routes)} routes in {js_rel}: {set(routes)}")
        
        # Search for api calls (e.g. $fetch, /v2/, /seasons, etc.)
        api_matches = re.findall(r'["\'](/v2/[^"\']+|https?://[^"\']+)["\']', js_content)
        print(f"Found {len(api_matches)} URL/API references in {js_rel}")
        for m in sorted(list(set(api_matches)))[:25]:
            print(f"  api ref: {m}")
            
        # Search for other nuxt chunk imports
        chunks = re.findall(r'["\'](/_nuxt/[^"\']+\.js)["\']', js_content)
        for c in chunks:
            manifest_urls.add(f"https://www.nbbl-basketball.de{c}")

    print(f"Discovered {len(manifest_urls)} additional Nuxt chunk URLs: {manifest_urls}")

if __name__ == "__main__":
    inspect_nuxt_bundles()
    test_api_endpoints()
