# Analytical Population Definitions — JBBL Experimental Sandbox

---

## 1. Hierarchy of Analytical Populations

To ensure statistical safety and prevent conflating incomparable fixtures or stages, all downstream analyses in Phase 4 must reference one of the explicitly defined analytical populations below:

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│ POPULATION 1: FALCONS PRIMARY CAMPAIGN (FALCONS_2025_PRIMARY)                   │
│ - Scope: Rheinland Falcons Basketball in Season 2025 (24 games)                 │
│ - Stages: Vorrunde Gruppe 7 (6g), Hauptrunde 4 (10g), Playoffs (8g)         │
│ - Intended Use: Core coach deliverables, active player performance profiles │
├─────────────────────────────────────────────────────────────────────────────┤
│ POPULATION 2: FALCONS HISTORICAL BENCHMARK (FALCONS_2023_BENCHMARK)             │
│ - Scope: Rheinland Falcons Basketball in Season 2023 (17 games)                 │
│ - Stages: Vorrunde Gruppe 7 (6g), Relegation (11g)                          │
│ - Intended Use: Year-over-year program development & longitudinal baseline  │
├─────────────────────────────────────────────────────────────────────────────┤
│ POPULATION 3: DIVISION & PLAYOFF OPPONENT UNIVERSE (LEAGUE_COMPARISON_2025) │
│ - Scope: All participating teams in Hauptrunde 4 & Playoff knockout brackets│
│ - Stages: Hauptrunde 4, Playoff 1/16, 1/8, Quarterfinals, Semifinals        │
│ - Intended Use: Contextual league distributions, percentiles, four factors  │
├─────────────────────────────────────────────────────────────────────────────┤
│ POPULATION 4: STAGE-SPECIFIC POPULATIONS                                    │
│ - STAGE_VORRUNDE: Group stage games only                                    │
│ - STAGE_HAUPTRUNDE: Top-tier main round games only                          │
│ - STAGE_PLAYOFFS: Knockout elimination games only                           │
│ - STAGE_RELEGATION: Relegation survival round only                          │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Minimum Sample Size Requirements by Metric Type

| Metric Category | Target Variables | Minimum Games ($N_{\min}$) | Minimum Possessions | Small-Sample Protection Action |
|:---|:---|:---:|:---:|:---|
| **Player Rate Metrics** | USG%, TS%, AST/TO | $N \ge 5$ | $\ge 100\text{ poss}$ | Flag as `SMALL_SAMPLE` if below threshold |
| **Team Efficiency** | ORtg, DRtg, NetRtg | $N \ge 3$ | $\ge 200\text{ poss}$ | Expose 95% Confidence Intervals |
| **Rolling Trends** | 3-game / 5-game $\Delta$ | $N \ge 3$ | N/A | Label as `SHORT_SAMPLE_DEMONSTRATION` |
| **Four Factors Regressions** | eFG%, TOV%, ORB%, FTr | $N \ge 15$ | N/A | Expose $R^2$ and standard errors |

---

## 3. Mathematical Formula References

* **Effective Field Goal Percentage**: $\text{eFG\%} = \frac{\text{FGM} + 0.5 \times \text{3PM}}{\text{FGA}}$
* **True Shooting Percentage**: $\text{TS\%} = \frac{\text{PTS}}{2 \times (\text{FGA} + 0.44 \times \text{FTA})}$
* **Estimated Possessions**: $\text{Poss} = \text{FGA} + 0.44 \times \text{FTA} - \text{OREB} + \text{TOV}$
* **Standardized Score (Z-Score)**: $z = \frac{x - \mu}{\sigma}$
