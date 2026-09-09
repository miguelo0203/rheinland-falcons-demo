"""Extract Boxscore and Play-by-Play mechanisms from C7LJJbUd.js and CAGDsTvq.js."""

import json
import re
from pathlib import Path

for name in ["C7LJJbUd.js", "CAGDsTvq.js"]:
    p = Path(f"reports/source_audit/samples/components/{name}")
    content = p.read_text(encoding="utf-8")
    print(f"=== File {name} ({len(content)} bytes) ===")
    
    # Check for websocket connections (wss://, ws://, socket.io, stomp, mqtt, etc.)
    ws_matches = re.findall(r'["\'](wss?://[^"\']+)["\']', content)
    print(f"Websocket matches ({len(ws_matches)}): {set(ws_matches)}")
    
    # Check for URLs or endpoints
    urls = re.findall(r'["\'](https?://[^"\']+|/[a-zA-Z0-9_\-/.:?&=]+)["\']', content)
    print(f"URLs in {name}:")
    for u in sorted(set(urls)):
        if any(k in u for k in ["scb", "bbl", "socket", "live", "game", "match", "action", "pbp", "ticker", "event", "boxscore", "stat"]):
            print(f"   -> {u}")

    # Check for action / event properties in PBP (e.g. action_type, text, score, period, etc.)
    fields = set(re.findall(r'[a-zA-Z0-9_]+_nr|[a-zA-Z0-9_]+_1|[a-zA-Z0-9_]+_2|[a-zA-Z0-9_]+code|teamcode', content))
    print(f"Interesting field patterns in {name}: {fields}")
