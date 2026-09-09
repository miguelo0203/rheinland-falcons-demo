# Canonical Game Registry & Incremental Season Operations

## 1. Registry Operational Summary

- **Total Ingested Fixtures**: 69
- **Official Competition Games**: 63 (100% of historical universe)
- **Player Boxscore Modality**: 60 / 69 games (87.0%)
- **Play-by-Play Modality**: 58 / 69 games (84.1%)
- **Spatial Shot Modality**: 58 / 69 games (84.1%)

## 2. Game Type Taxonomy & Population Rules

```text
┌────────────────┬─────────────────────────────────────────────────────────────┐
│ GAME TYPE      │ OPERATIONAL & STATISTICAL RULE                              │
├────────────────┼─────────────────────────────────────────────────────────────┤
│ OFFICIAL       │ Standard league competition (JBBL Vorrunde/Hauptrunde/PO).  │
│                │ Included in official Win%, Four Factors, standings.         │
├────────────────┼─────────────────────────────────────────────────────────────┤
│ PRACTICE       │ Internal scrimmage / practice match with boxscore/PBP data. │
│                │ ISOLATED from official league tables. Accessible in         │
│                │ player development & workload monitoring views.             │
├────────────────┼─────────────────────────────────────────────────────────────┤
│ SCRIMMAGE      │ Unofficial closed-door training fixture.                    │
├────────────────┼─────────────────────────────────────────────────────────────┤
│ FRIENDLY       │ Pre-season or exhibition match outside JBBL standings.      │
└────────────────┴─────────────────────────────────────────────────────────────┘
```