"""Batch extraction harvester for historical JBBL matches with polite pacing and cryptographic preservation."""

import hashlib
import json
import re
import time
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from python.config import get_api_key

API_BASE = "https://api.bbl.scb.world/v2"
SOCKET_BASE = "https://api.bbl.scb.world"
JBBL_KEY = get_api_key("JBBL")
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Club Basketball Analytics Batch Harvester"

RAW_ROOT = Path("data/raw/jbbl")
RAW_ROOT.mkdir(parents=True, exist_ok=True)

def fetch_bytes(url: str, headers: Dict[str, str], method: str = "GET", post_data: bytes = None) -> Tuple[bytes, int, float]:
    t0 = time.time()
    req = urllib.request.Request(url, data=post_data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=12) as resp:
        content = resp.read()
        latency = round((time.time() - t0) * 1000, 1)
        return content, resp.status, latency

def acquire_game_socket_stream(game_id: int, headers: Dict[str, str]) -> Tuple[bytes, str]:
    """Acquires the full historical Socket.IO array replay stream for a game."""
    hs_url = f"{SOCKET_BASE}/socket.io/?EIO=4&transport=polling"
    raw_hs, _, _ = fetch_bytes(hs_url, headers)
    hs_text = raw_hs.decode("utf-8", errors="replace")
    sid = json.loads(hs_text[1:])["sid"]
    
    poll_url = f"{SOCKET_BASE}/socket.io/?EIO=4&transport=polling&sid={sid}"
    # Connect
    fetch_bytes(poll_url, {**headers, "Content-Type": "text/plain"}, method="POST", post_data=b"40")
    fetch_bytes(poll_url, headers)
    # Join & History
    join_payload = f'42["join",{game_id}]'.encode("utf-8")
    hist_payload = f'42["history",{game_id}]'.encode("utf-8")
    fetch_bytes(poll_url, {**headers, "Content-Type": "text/plain"}, method="POST", post_data=join_payload)
    fetch_bytes(poll_url, {**headers, "Content-Type": "text/plain"}, method="POST", post_data=hist_payload)
    # Ingest Stream
    stream_bytes, _, _ = fetch_bytes(poll_url, headers)
    return stream_bytes, sid

def harvest_single_game(game_id: int, season: int, force: bool = False) -> Dict[str, Any]:
    """Harvests REST header and Socket.IO replay stream for a single game and saves to disk."""
    game_dir = RAW_ROOT / str(season) / str(game_id)
    game_dir.mkdir(parents=True, exist_ok=True)
    
    header_path = game_dir / "raw_game_header.json"
    stream_path = game_dir / f"raw_socket_stream_{game_id}.txt"
    manifest_path = game_dir / "raw_provenance_manifest.json"
    
    if not force and header_path.exists() and stream_path.exists() and manifest_path.exists():
        manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))
        return {
            "game_id": game_id,
            "season": season,
            "status": "CACHED",
            "manifest": manifest_data
        }

    auth_headers = {
        "User-Agent": USER_AGENT,
        "X-API-KEY": JBBL_KEY,
        "Accept": "application/json",
    }
    
    manifest = {
        "game_id": game_id,
        "season": season,
        "league": "JBBL",
        "retrieval_timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "artifacts": {}
    }
    
    # 1. REST Header
    try:
        hdr_url = f"{API_BASE}/game/{game_id}"
        hdr_bytes, status, lat = fetch_bytes(hdr_url, auth_headers)
        hdr_sha = hashlib.sha256(hdr_bytes).hexdigest()
        header_path.write_bytes(hdr_bytes)
        manifest["artifacts"]["header"] = {
            "url": hdr_url,
            "sha256": hdr_sha,
            "size_bytes": len(hdr_bytes),
            "status": status,
            "latency_ms": lat,
            "file": header_path.name
        }
    except Exception as e:
        manifest["artifacts"]["header"] = {"error": str(e)}

    time.sleep(0.1) # Polite pacing

    # 2. Socket.IO Stream
    try:
        socket_headers = {
            "User-Agent": USER_AGENT,
            "x-api-key": JBBL_KEY,
            "Accept": "*/*",
        }
        strm_bytes, sid = acquire_game_socket_stream(game_id, socket_headers)
        strm_sha = hashlib.sha256(strm_bytes).hexdigest()
        stream_path.write_bytes(strm_bytes)
        manifest["artifacts"]["socket_stream"] = {
            "sid": sid,
            "sha256": strm_sha,
            "size_bytes": len(strm_bytes),
            "file": stream_path.name
        }
    except Exception as e:
        manifest["artifacts"]["socket_stream"] = {"error": str(e)}

    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    
    return {
        "game_id": game_id,
        "season": season,
        "status": "HARVESTED",
        "header_size": manifest["artifacts"].get("header", {}).get("size_bytes", 0),
        "stream_size": manifest["artifacts"].get("socket_stream", {}).get("size_bytes", 0),
    }

def harvest_batch(games_to_harvest: List[Tuple[int, int]]) -> Dict[str, Any]:
    print(f"\n==========================================================================")
    print(f"   STARTING BATCH HARVESTING FOR {len(games_to_harvest)} JBBL MATCHES")
    print(f"==========================================================================")
    
    results = []
    success_count = 0
    cached_count = 0
    error_count = 0
    
    for idx, (gid, season) in enumerate(games_to_harvest, 1):
        try:
            res = harvest_single_game(gid, season)
            st = res["status"]
            if st == "CACHED":
                cached_count += 1
                print(f"  [{idx:3d}/{len(games_to_harvest):3d}] Game {gid} (Season {season}): [CACHED]")
            else:
                success_count += 1
                h_size = res.get("header_size", 0)
                s_size = res.get("stream_size", 0)
                print(f"  [{idx:3d}/{len(games_to_harvest):3d}] Game {gid} (Season {season}): [DOWNLOADED] (Header: {h_size}B, Stream: {s_size}B)")
            results.append(res)
            time.sleep(0.12) # Polite request spacing
        except Exception as e:
            error_count += 1
            print(f"  [{idx:3d}/{len(games_to_harvest):3d}] Game {gid} (Season {season}): [ERROR] {e}")
            results.append({"game_id": gid, "season": season, "status": "FAILED", "error": str(e)})
            
    print(f"\n--- Batch Harvesting Completed ---")
    print(f"  Total Games: {len(games_to_harvest)} | Harvested: {success_count} | Cached: {cached_count} | Errors: {error_count}")
    
    return {
        "total": len(games_to_harvest),
        "harvested": success_count,
        "cached": cached_count,
        "errors": error_count,
        "results": results
    }

if __name__ == "__main__":
    # Test on a small sample of games
    test_games = [(9995585, 2025), (2005079, 2025), (9993655, 2025)]
    harvest_batch(test_games)
