"""Download page components (matches, teams, spieler, stats, live, tabelle) and extract API routes and data structures."""

import json
import re
import urllib.request
from pathlib import Path

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

components = [
    "CWsQjA7C.js",  # matches-id
    "J6s6SohR.js",  # league-matches-id
    "DvZSHzX1.js",  # spieler-id
    "D3mpuIJW.js",  # league-spieler-id
    "B87s_89P.js",  # league-live-id
    "0LvxfO5N.js",  # live-id
    "CbwOJycL.js",  # stats
    "DIj-uKtM.js",  # league-stats
    "BSgDM5Dw.js",  # teams
    "DIWW9fVo.js",  # league-teams
    "CPoSYFq6.js",  # index
]

out_dir = Path("reports/source_audit/samples/components")
out_dir.mkdir(parents=True, exist_ok=True)

for comp in components:
    url = f"https://www.nbbl-basketball.de/_nuxt/{comp}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=15) as resp:
            content = resp.read().decode("utf-8", errors="replace")
            (out_dir / comp).write_text(content, encoding="utf-8")
            print(f"Downloaded {comp} ({len(content)} chars)")
            
            # Search for URLs, endpoints, properties, state, $fetch, params
            apis = re.findall(r'["\'](?:https?://[^"\']+|/[a-zA-Z0-9_\-/.:?&=]+)["\']', content)
            print(f"  Strings in {comp}:")
            for a in set(apis):
                if any(k in a for k in ["scb", "api", "match", "team", "player", "spieler", "stat", "live", "tabelle", "schedule", "v2"]):
                    print(f"    -> {a}")
    except Exception as e:
        print(f"Error fetching {comp}: {e}")
