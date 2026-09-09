# Incremental Update & Continuous Season Ingestion Architecture

## 1. Pipeline Invariants for Continuous Data Loading
1. **Idempotency**: Repeated ingestion of existing matches produces zero duplicates (`INSERT ... WHERE pk NOT IN (...)`).
2. **Persistent Entity Keys**: Player and Team IDs remain stable across multi-season schedules.
3. **Automatic Window Updates**: Rolling 3/4/5-game performance windows and weekly aggregates update automatically upon new game ingestion.