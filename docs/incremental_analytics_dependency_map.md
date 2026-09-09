# Incremental Analytics Dependency Map

## 1. Downstream Recomputation Graph

```text
NEW GAME INGESTION (game_id, season_id, game_type)
    │
    ├──> 1. CANONICAL GAME REGISTRY (data/derived/game_registry.parquet)
    │
    ├──> 2. TEAM INTELLIGENCE (data/derived/team_intelligence.parquet)
    │       - If OFFICIAL: Updates season Four Factors, win%, ORtg/DRtg
    │       - If PRACTICE: Isolated from official league tables
    │
    ├──> 3. PLAYER EVOLUTION & ROLLING WINDOWS (data/derived/player_evolution.parquet)
    │       - Game-by-game deltas
    │       - Rolling 3/4/5-game averages & trend slopes
    │       - Weekly performance trajectories
    │
    ├──> 4. SHOT INTELLIGENCE (data/derived/shot_intelligence.parquet)
    │       - Spatial coordinates & 5 tactical court zones
    │
    └──> 5. COACH FINDINGS & HYPOTHESES (data/derived/coach_intelligence_findings.parquet)
            - 3-level cognitive hierarchy & video review tags
```