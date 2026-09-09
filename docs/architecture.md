# System Architecture — JBBL / NBBL Experimental Sandbox

## 1. Executive Summary

This architecture implements a strict, multi-source, reproducible data foundation for experimental JBBL/NBBL youth basketball analytics. It is an exact experimental clone of the production Club Basketball Analytics foundation, operating in total isolation within its own DuckDB database and directory tree.

```text
┌─────────────────────────────────────────────────────────────┐
│ 1. RAW (Immutable JSON / CSV / Video Media)                 │
└──────────────────────────────┬──────────────────────────────┘
                               │ Extract & Hash (SHA-256)
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. STAGING (In-Memory Dictionaries / Clean Payloads)         │
└──────────────────────────────┬──────────────────────────────┘
                               │ Canonical Normalization & Resolution
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. NORMALIZED (Pydantic Domain Models / Parquet Snapshots)   │
└──────────────────────────────┬──────────────────────────────┘
                               │ Validation Engine & Quality Scoring
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. VALIDATED (Verified Records / Quality Tier Assigned)      │
└──────────────────────────────┬──────────────────────────────┘
                               │ Lineup / Possession Reconstruction
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. DERIVED (Lineup Stints / Possessions / Sync Anchors)     │
└──────────────────────────────┬──────────────────────────────┘
                               │ Analytical Queries / Feature Store
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ 6. ANALYTICS (DuckDB Storage / Downstream Research Views)   │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Core Architectural Pillars

1. **Raw Data is Sacred**: Never mutate, overwrite, or delete raw source files.
2. **Epistemic Missingness Standard**: Explicit missingness with `OBSERVED`, `NOT_AVAILABLE`, `NOT_APPLICABLE`, `NOT_OBSERVED`, `ESTIMATED`.
3. **No Silent Overwrites & Conflict Preservation**: Multi-source discrepancies are preserved in `source_conflict_log`.
4. **Source Independence**: Boxscore, Play-by-Play (PBP), and Video are completely decoupled.
5. **Missing Source Tolerance**: The architecture cleanly supports all 7 permutations of source availability.
6. **Isolated Storage**: Operates on `database/jbbl_sandbox.duckdb` and separate Parquet layers.
