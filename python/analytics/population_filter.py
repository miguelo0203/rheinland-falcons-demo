"""Mathematical Population Isolation Layer for Rheinland Falcons Analytics."""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

DOCS_DIR = Path("docs")
DOCS_DIR.mkdir(parents=True, exist_ok=True)

def filter_by_population(df: pd.DataFrame, population_mode: str = "OFFICIAL_ONLY") -> pd.DataFrame:
    """Filters dataset according to strict mathematical population rules."""
    if df.empty:
        return df

    if "game_type" in df.columns:
        if population_mode == "OFFICIAL_ONLY":
            return df[df["game_type"] == "OFFICIAL"].copy()
        elif population_mode == "PRACTICE_ONLY":
            return df[df["game_type"].isin(["PRACTICE", "SCRIMMAGE", "FRIENDLY"])].copy()
        else: # ALL_GAMES
            return df.copy()

    elif "is_official_competition" in df.columns:
        if population_mode == "OFFICIAL_ONLY":
            return df[df["is_official_competition"] == True].copy()
        elif population_mode == "PRACTICE_ONLY":
            return df[df["is_official_competition"] == False].copy()
        else:
            return df.copy()

    return df

def get_population_metadata(df: pd.DataFrame) -> Dict[str, Any]:
    """Extracts explicit population breakdown for UI transparency."""
    if df.empty:
        return {"total_records": 0, "official_count": 0, "practice_count": 0, "label": "No Data"}

    total = len(df)
    if "game_type" in df.columns:
        official = int((df["game_type"] == "OFFICIAL").sum())
        practice = int((df["game_type"] != "OFFICIAL").sum())
    elif "is_official_competition" in df.columns:
        official = int((df["is_official_competition"] == True).sum())
        practice = int((df["is_official_competition"] == False).sum())
    else:
        official = total
        practice = 0

    return {
        "total_records": total,
        "official_count": official,
        "practice_count": practice,
        "label": f"{official} Official + {practice} Practice/Scrimmage" if practice > 0 else f"{official} Official Games",
    }

def generate_practice_population_policy_doc():
    doc = """# Practice & Scrimmage Game Population Policy

## 1. Strict Mathematical Isolation Layer
1. **Official Competition Benchmarks**: All official league tables, standings, Four Factors, percentiles, and season win percentages are computed STRICTLY over `game_type == 'OFFICIAL'`.
2. **Practice / Scrimmage Inclusion**: Practice, scrimmage, and friendly fixtures are preserved and queryable for internal player development, workload tracking, and tactical experimentation.
3. **No Silent Mixing**: Every UI view explicitly presents its population denominator (e.g. `17 Official + 4 Practice`).
"""
    (DOCS_DIR / "practice_game_population_policy.md").write_text(doc.strip(), encoding="utf-8")
    print("Generated docs/practice_game_population_policy.md")

if __name__ == "__main__":
    generate_practice_population_policy_doc()
