# Player Trend Classification Methodology

## 1. Mathematical Classification Framework

To prevent interpreting random game-to-game noise as genuine player development, player trajectories are categorized strictly using deterministic thresholds:

```text
┌──────────────────────┬─────────────────────────────────────────────────────────────┐
│ CLASSIFICATION       │ MATHEMATICAL RULE / THRESHOLD                               │
├──────────────────────┼─────────────────────────────────────────────────────────────┤
│ IMPROVING            │ N >= 4, Trend Slope beta > +0.50 PTS/game & diff >= +2.0 PPG│
│ DECLINING            │ N >= 4, Trend Slope beta < -0.50 PTS/game & diff <= -2.0 PPG│
│ STABLE               │ N >= 4, |beta| <= 0.50 & |Recent - Baseline| <= 1.5 PPG     │
│ VOLATILE             │ N >= 4, StdDev / Mean > 0.50 or fluctuating trajectory      │
│ INSUFFICIENT_DATA    │ N < 4 games played                                          │
└──────────────────────┴─────────────────────────────────────────────────────────────┘
```

## 2. Longitudinal Season Phases

- **`EARLY_SEASON`**: Games 1 to 6 (Vorrunde group stage).
- **`MID_SEASON`**: Games 7 to 16 (Hauptrunde main round).
- **`LATE_SEASON_PLAYOFFS`**: Games 17+ (National playoff elimination brackets).