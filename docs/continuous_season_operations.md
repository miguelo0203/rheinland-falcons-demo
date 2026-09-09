# Continuous Season Operations & Incremental Maintenance Guide

## 1. Automated Lifecycle for New Match Arrival

```text
NEW GAME
   ↓
INCREMENTAL INGESTION (Duplicate Check & SHA-256 Hashing)
   ↓
VALIDATION ENGINE (Mathematical Invariants)
   ↓
CANONICAL REGISTRY UPDATE (game_registry.parquet)
   ↓
DEPENDENCY RECOMPUTATION (Rolling Windows, Weekly Stats, Season Ratings)
   ↓
COACH INTELLIGENCE INTERFACE (Live Streamlit Reload)
```