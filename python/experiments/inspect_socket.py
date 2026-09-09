"""Search C7LJJbUd.js for Socket.IO host, events, and message handling."""

import re
from pathlib import Path

content = Path("reports/source_audit/samples/components/C7LJJbUd.js").read_text(encoding="utf-8")

matches = [m.start() for m in re.finditer(r'socket\.io|io\(|connect|socket', content, re.IGNORECASE)]
print(f"Found {len(matches)} socket matches")

for idx in matches[:15]:
    start = max(0, idx - 100)
    end = min(len(content), idx + 200)
    print(f"--- Pos {idx} ---")
    print(content[start:end])
    print()
