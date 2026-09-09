"""Find exact array index mappings for socket packet types in C7LJJbUd.js."""

import re
from pathlib import Path

content = Path("reports/source_audit/samples/components/C7LJJbUd.js").read_text(encoding="utf-8")

# Search for the function dt(u) or decoder function that converts raw arrays to objects
# In the previous snippet, we saw: `const p = dt(u), g = Array.isArray(p)?p:[p];`
matches = [m.start() for m in re.finditer(r'function dt\(|const dt\s*=|dt\s*=\s*function|dt\s*=\s*\(', content)]
print(f"Found {len(matches)} matches for 'dt'")

for idx in matches:
    start = max(0, idx - 50)
    end = min(len(content), idx + 2000)
    print(f"--- Decoder Function at Pos {idx} ---")
    print(content[start:end])
    print()
