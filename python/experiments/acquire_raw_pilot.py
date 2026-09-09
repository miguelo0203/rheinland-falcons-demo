"""Fetch and store original RAW payloads for JBBL Match 9995585 with complete provenance."""

import hashlib
import json
import time
import urllib.request
from pathlib import Path
from typing import Dict, Any

API_BASE = "https://api.bbl.scb.world/v2"
SOCKET_BASE = "https://api.bbl.scb.world"
JBBL_KEY = "81e03c389456a1d3441cd89ce9703d88"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Club Basketball Analytics Pilot Ingestion"

RAW_DIR = Path("data/raw/jbbl/9995585")
RAW_DIR.mkdir(parents=True, exist_ok=True)

def fetch_and_save_raw(
    filename: str,
    url: str,
    headers: Dict[str, str],
    method: str = "GET",
    post_data: bytes = None,
) -> Dict[str, Any]:
    """Fetches URL and saves raw bytes to disk without any modification."""
    t0 = time.time()
    req = urllib.request.Request(url, data=post_data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=15) as resp:
        raw_bytes = resp.read()
        latency_ms = round((time.time() - t0) * 1000, 1)
        raw_text = raw_bytes.decode("utf-8", errors="replace")
        sha256 = hashlib.sha256(raw_bytes).hexdigest()
        timestamp_utc = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        
        file_path = RAW_DIR / filename
        file_path.write_bytes(raw_bytes)
        print(f"  [SAVED] {filename:30} -> {len(raw_bytes):7,d} bytes | SHA256: {sha256[:12]}... | {latency_ms}ms")
        
        return {
            "filename": filename,
            "file_path": str(file_path.as_posix()),
            "url": url,
            "http_method": method,
            "http_status": resp.status,
            "content_length_bytes": len(raw_bytes),
            "sha256": sha256,
            "retrieval_timestamp_utc": timestamp_utc,
            "latency_ms": latency_ms,
        }

def acquire_raw_pilot_payloads():
    print("==========================================================================")
    print(" [PHASE 2 - STEP 1] ACQUIRING RAW SOURCE PAYLOADS FOR MATCH 9995585       ")
    print("==========================================================================")
    
    auth_headers = {
        "User-Agent": USER_AGENT,
        "X-API-KEY": JBBL_KEY,
        "Accept": "application/json",
    }
    
    manifest = {
        "game_id": 9995585,
        "league": "JBBL",
        "season_id": 2025,
        "raw_artifacts": []
    }
    
    # 1. Match Header
    m1 = fetch_and_save_raw("raw_game_header.json", f"{API_BASE}/game/9995585", auth_headers)
    manifest["raw_artifacts"].append(m1)
    
    # 2. Team 2048 (Rheinland)
    m2 = fetch_and_save_raw("raw_team_2048_rheinland.json", f"{API_BASE}/team/2048", auth_headers)
    manifest["raw_artifacts"].append(m2)
    
    # 3. Team 2054 (Isar Bulls)
    m3 = fetch_and_save_raw("raw_team_2054_wuerzburg.json", f"{API_BASE}/team/2054", auth_headers)
    manifest["raw_artifacts"].append(m3)
    
    # 4. Schedule Entry for Season 2025
    m4 = fetch_and_save_raw("raw_schedule_season_2025.json", f"{API_BASE}/schedule?seasonId=2025", auth_headers)
    manifest["raw_artifacts"].append(m4)
    
    # 5. Socket.IO Replay Stream
    socket_headers = {
        "User-Agent": USER_AGENT,
        "x-api-key": JBBL_KEY,
        "Accept": "*/*",
    }
    
    # Handshake
    hs_url = f"{SOCKET_BASE}/socket.io/?EIO=4&transport=polling"
    req_hs = urllib.request.Request(hs_url, headers=socket_headers)
    with urllib.request.urlopen(req_hs, timeout=10) as resp_hs:
        hs_text = resp_hs.read().decode("utf-8")
        sid = json.loads(hs_text[1:])["sid"]
        
    poll_url = f"{SOCKET_BASE}/socket.io/?EIO=4&transport=polling&sid={sid}"
    # Connect
    urllib.request.urlopen(urllib.request.Request(poll_url, data=b"40", headers={**socket_headers, "Content-Type": "text/plain"}))
    urllib.request.urlopen(urllib.request.Request(poll_url, headers=socket_headers))
    # Join & History
    urllib.request.urlopen(urllib.request.Request(poll_url, data=b'42["join",9995585]', headers={**socket_headers, "Content-Type": "text/plain"}))
    urllib.request.urlopen(urllib.request.Request(poll_url, data=b'42["history",9995585]', headers={**socket_headers, "Content-Type": "text/plain"}))
    
    # Ingest Stream
    m5 = fetch_and_save_raw("raw_socket_stream_9995585.txt", poll_url, socket_headers)
    manifest["raw_artifacts"].append(m5)
    
    # Save Manifest
    manifest_path = RAW_DIR / "raw_provenance_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"\nSaved RAW provenance manifest to {manifest_path}")

if __name__ == "__main__":
    acquire_raw_pilot_payloads()
