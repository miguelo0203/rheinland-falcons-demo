"""Batch extraction harvester for NBBL (U19) matches and rosters with secure credential handling."""

import hashlib
import json
import time
import urllib.request
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from python.config import get_api_key

API_BASE = "https://api.bbl.scb.world/v2"
SOCKET_BASE = "https://api.bbl.scb.world"
NBBL_KEY = get_api_key("NBBL")
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Rheinland Falcons Analytics Batch Harvester"

RAW_ROOT = Path("data/raw/nbbl")
RAW_ROOT.mkdir(parents=True, exist_ok=True)


def fetch_bytes(url: str, headers: Dict[str, str], method: str = "GET", post_data: bytes = None) -> Tuple[bytes, int, float]:
    t0 = time.time()
    req = urllib.request.Request(url, data=post_data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=15) as resp:
        content = resp.read()
        latency = round((time.time() - t0) * 1000, 1)
        return content, resp.status, latency


def acquire_game_socket_stream(game_id: int, headers: Dict[str, str]) -> Tuple[bytes, str]:
    """Acquires the full historical Socket.IO array replay stream for an NBBL game."""
    hs_url = f"{SOCKET_BASE}/socket.io/?EIO=4&transport=polling"
    raw_hs, _, _ = fetch_bytes(hs_url, headers)
    hs_text = raw_hs.decode("utf-8", errors="replace")
    sid = json.loads(hs_text[1:])["sid"]
    
    poll_url = f"{SOCKET_BASE}/socket.io/?EIO=4&transport=polling&sid={sid}"
    fetch_bytes(poll_url, {**headers, "Content-Type": "text/plain"}, method="POST", post_data=b"40")
    fetch_bytes(poll_url, headers)
    
    join_payload = f'42["join",{game_id}]'.encode("utf-8")
    hist_payload = f'42["history",{game_id}]'.encode("utf-8")
    fetch_bytes(poll_url, {**headers, "Content-Type": "text/plain"}, method="POST", post_data=join_payload)
    fetch_bytes(poll_url, {**headers, "Content-Type": "text/plain"}, method="POST", post_data=hist_payload)
    
    stream_bytes, _, _ = fetch_bytes(poll_url, headers)
    return stream_bytes, sid


def harvest_single_game(game_id: int, season: int = 2023, force: bool = False) -> Dict[str, Any]:
    """Harvests REST header and Socket.IO replay stream for an NBBL game and saves to disk."""
    if not NBBL_KEY:
        raise ValueError("NBBL API key not found in environment or secrets.")

    game_dir = RAW_ROOT / str(season) / str(game_id)
    game_dir.mkdir(parents=True, exist_ok=True)
    
    header_path = game_dir / "raw_game_header.json"
    stream_path = game_dir / f"raw_socket_stream_{game_id}.txt"
    manifest_path = game_dir / "raw_provenance_manifest.json"
    
    if not force and header_path.exists() and stream_path.exists() and manifest_path.exists():
        try:
            manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))
            return {
                "game_id": game_id,
                "season": season,
                "status": "CACHED",
                "manifest": manifest_data,
            }
        except Exception:
            pass

    auth_headers = {
        "User-Agent": USER_AGENT,
        "X-API-KEY": NBBL_KEY,
        "Accept": "application/json",
    }
    
    manifest = {
        "game_id": game_id,
        "season": season,
        "league": "NBBL",
        "competition": "CMP_NBBL",
        "age_category": "U19",
        "retrieval_timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "artifacts": {},
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
            "file": header_path.name,
        }
    except Exception as e:
        manifest["artifacts"]["header"] = {"error": str(e)}

    time.sleep(0.08) # Polite pacing

    # 2. Socket.IO Stream
    try:
        socket_headers = {
            "User-Agent": USER_AGENT,
            "x-api-key": NBBL_KEY,
            "Accept": "*/*",
        }
        strm_bytes, sid = acquire_game_socket_stream(game_id, socket_headers)
        strm_sha = hashlib.sha256(strm_bytes).hexdigest()
        stream_path.write_bytes(strm_bytes)
        manifest["artifacts"]["socket_stream"] = {
            "sid": sid,
            "sha256": strm_sha,
            "size_bytes": len(strm_bytes),
            "file": stream_path.name,
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


def harvest_nbbl_rheinland_all(force: bool = False) -> Dict[str, Any]:
    """Harvests all 18 official Rheinland NBBL 2023 matches plus active 2025/26 roster."""
    rheinland_2023_gids = [
        33132, 33137, 33138, 33142, 33145, 33146, 33150, 33153,
        33155, 33161, 33839, 33843, 33850, 33854, 33855, 33859, 33866, 33870
    ]
    
    print("==========================================================================")
    print(f" HARVESTING {len(rheinland_2023_gids)} OFFICIAL NBBL MATCHES FOR RHEINLAND FALCONS U19")
    print("==========================================================================")
    
    results = []
    success_count = 0
    cached_count = 0
    error_count = 0
    
    for idx, gid in enumerate(rheinland_2023_gids, 1):
        try:
            res = harvest_single_game(gid, season=2023, force=force)
            st = res["status"]
            if st == "CACHED":
                cached_count += 1
                print(f"  [{idx:2d}/{len(rheinland_2023_gids):2d}] Match {gid} (2023): [CACHED]")
            else:
                success_count += 1
                print(f"  [{idx:2d}/{len(rheinland_2023_gids):2d}] Match {gid} (2023): [HARVESTED] ({res['header_size']}B / {res['stream_size']}B)")
            results.append(res)
            time.sleep(0.1)
        except Exception as e:
            error_count += 1
            print(f"  [{idx:2d}/{len(rheinland_2023_gids):2d}] Match {gid} (2023): [ERROR] {e}")
            results.append({"game_id": gid, "season": 2023, "status": "FAILED", "error": str(e)})

    # Also harvest active 2025/2026 team 1083 profile and roster
    print("\n--- Harvesting Active 2025/26 NBBL Team & Roster Profile ---")
    try:
        t_url = f"{API_BASE}/team/1083"
        auth_headers = {"User-Agent": USER_AGENT, "X-API-KEY": NBBL_KEY, "Accept": "application/json"}
        t_bytes, _, _ = fetch_bytes(t_url, auth_headers)
        r2025_dir = RAW_ROOT / "2025"
        r2025_dir.mkdir(parents=True, exist_ok=True)
        (r2025_dir / "team_1083.json").write_bytes(t_bytes)
        print(f"  Saved active Rheinland NBBL roster ({len(t_bytes)} bytes).")
    except Exception as e:
        print(f"  Warning: Could not fetch active team 1083 profile: {e}")

    return {
        "total": len(rheinland_2023_gids),
        "harvested": success_count,
        "cached": cached_count,
        "errors": error_count,
        "results": results,
    }


if __name__ == "__main__":
    harvest_nbbl_rheinland_all()
