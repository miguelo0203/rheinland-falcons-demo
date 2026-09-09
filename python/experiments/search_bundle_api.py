"""Exhaustively search Nuxt JS bundle for all occurrences of API calls, route loaders, and data fetching."""

import json
import re
from pathlib import Path

bundle_path = Path("reports/source_audit/samples/nuxt_bundle_DzMyqwY6.js")
code = bundle_path.read_text(encoding="utf-8")

keywords = [
    "apiBase",
    "devBaseUrl",
    "bbl.scb.world",
    "/schedule",
    "/standings",
    "/teams",
    "/players",
    "/matches",
    "/live",
    "/stats",
    "/games",
    "useFetch",
    "$fetch",
    "asyncData",
]

for kw in keywords:
    matches = [m.start() for m in re.finditer(re.escape(kw), code)]
    print(f"=== Keyword: '{kw}' (found {len(matches)} times) ===")
    for idx in matches[:5]:
        start = max(0, idx - 150)
        end = min(len(code), idx + 250)
        snippet = code[start:end]
        print(f"--- Pos {idx} ---")
        print(snippet.replace("\n", " "))
        print()
