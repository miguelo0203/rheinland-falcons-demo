"""Decompile and extract all API routes, URL schemas, components, and parameter names from the Nuxt bundle."""

import json
import re
from pathlib import Path

bundle_path = Path("reports/source_audit/samples/nuxt_bundle_DzMyqwY6.js")
code = bundle_path.read_text(encoding="utf-8")

print(f"Loaded bundle: {len(code)} bytes")

# 1. Find all vue-router route definitions
# In Nuxt 3, routes typically look like {name:"...",path:"...",component:...} or similar
route_matches = re.findall(r'name:\s*["\']([^"\']+)["\'],\s*path:\s*["\']([^"\']+)["\']', code)
print(f"=== Found {len(route_matches)} Named Routes ===")
for name, path in sorted(route_matches):
    print(f"  Route [{name}]: {path}")

# Also find path matches with regex
path_matches = re.findall(r'path:\s*["\'](/[a-zA-Z0-9_\-/:?]+)["\']', code)
print(f"\n=== All Distinct Route Paths ({len(set(path_matches))}): ===")
for p in sorted(set(path_matches)):
    print(f"  {p}")

# 2. Find all API endpoint strings (e.g. /matches, /teams, /standings, /players, /clubs, /statistics, /news, /schedule)
api_calls = set(re.findall(r'["\'](/(?:v2/)?[a-zA-Z0-9_\-]+(?:/[a-zA-Z0-9_\-:]+)*)["\']', code))
print(f"\n=== Potential API Endpoint Paths ({len(api_calls)}): ===")
for a in sorted(api_calls):
    if any(k in a for k in ["match", "team", "player", "standing", "stat", "season", "comp", "club", "round", "group", "lead", "rank", "box", "pbp", "live"]):
        print(f"  {a}")

# 3. Find template strings or function calls fetching data (e.g. $fetch, useFetch, apiBase)
fetches = re.findall(r'(?:useFetch|\$fetch|apiBase)\s*\(\s*["\']?([^"\',)]+)["\']?', code)
print(f"\n=== Fetch Targets ({len(fetches)}): ===")
for f in sorted(set(fetches))[:30]:
    print(f"  fetch: {f}")

# 4. Search for query parameter patterns (e.g., seasonId, matchId, teamId, etc.)
params = set(re.findall(r'[a-zA-Z0-9_]+Id|[a-zA-Z0-9_]+_id', code))
print(f"\n=== Discovered Identifier Names: ===")
for p in sorted(params):
    print(f"  id param: {p}")
