"""Forensic discovery script to inspect raw HTML, API calls, and embedded data on nbbl-basketball.de."""

import json
import re
import urllib.request
import urllib.parse
from pathlib import Path

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

def fetch_url(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.read().decode("utf-8", errors="replace")

def inspect_page(url: str, name: str):
    print(f"=== Fetching {name}: {url} ===")
    try:
        html = fetch_url(url)
        print(f"Length: {len(html)} chars")
        
        # Save raw HTML sample for forensic evidence
        out_dir = Path("reports/source_audit/samples")
        out_dir.mkdir(parents=True, exist_ok=True)
        sample_path = out_dir / f"{name}.html"
        sample_path.write_text(html, encoding="utf-8")
        print(f"Saved to {sample_path}")
        
        # Look for JSON-like data or API endpoints or script tags
        scripts = re.findall(r"<script\b[^>]*>(.*?)</script>", html, re.DOTALL | re.IGNORECASE)
        print(f"Found {len(scripts)} script tags")
        
        for i, s in enumerate(scripts):
            s_clean = s.strip()
            if not s_clean:
                continue
            if any(kw in s_clean for kw in ["window.", "__NEXT_DATA__", "__INITIAL_STATE__", "api", "json", "match", "boxscore", "pbp", "live"]):
                print(f"--- Script {i} snippet (len={len(s_clean)}): ---")
                print(s_clean[:500])
                print("...")

        # Search for API endpoints or ajax calls in script sources
        script_srcs = re.findall(r'<script\b[^>]*src=["\']([^"\']+)["\']', html, re.IGNORECASE)
        print(f"Script sources ({len(script_srcs)}):")
        for src in script_srcs[:10]:
            print(f"  - {src}")

        # Check links
        links = re.findall(r'<a\b[^>]*href=["\']([^"\']+)["\']', html, re.IGNORECASE)
        print(f"Found {len(links)} links. Sample distinct link patterns:")
        distinct_patterns = set()
        for link in links:
            if link.startswith("/") or "nbbl-basketball" in link:
                distinct_patterns.add(link.split("?")[0])
        for p in sorted(list(distinct_patterns))[:20]:
            print(f"  link: {p}")

    except Exception as e:
        print(f"Error fetching {url}: {e}")

if __name__ == "__main__":
    inspect_page("https://www.nbbl-basketball.de/jbbl/matches/9995585?status=0", "match_9995585")
    inspect_page("https://www.nbbl-basketball.de/jbbl/teams/2048", "team_2048")
    inspect_page("https://www.nbbl-basketball.de/", "home")
