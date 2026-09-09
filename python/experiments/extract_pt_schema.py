"""Extract the complete pt packet decoding dictionary from C7LJJbUd.js."""

import re
from pathlib import Path

content = Path("reports/source_audit/samples/components/C7LJJbUd.js").read_text(encoding="utf-8")

pos = content.find("function dt(n)")
if pos != -1:
    start = max(0, pos - 4000)
    snippet = content[start:pos + 200]
    print(snippet)
