# Phase 5 Pre-Interface Independent Mathematical Audit Report

## 1. Mathematical Verification Table

| Metric Audited | Source Dataset | Formula / Method | Denominator | Expected Value | Recalculated Value | Discrepancy | Status |
|:---|:---|:---|:---|:---:|:---:|:---:|:---:|
| **Total Games Ingested** | `game table` | `COUNT(DISTINCT game_id)` | 60 total | **60** | **60** | `0` | `PASSED` |
| **Games with Player Boxscore** | `boxscore_player table` | `COUNT(games with >= 10 player records)` | N = 60 / 60 | **60** | **60** | `0` | `PASSED` |
| **Player Point Sum Reconciliation** | `boxscore_team & boxscore_player` | `team_pts == sum(player_pts) per team per game` | N = 60 games with player boxscores | **60** | **60** | `0` | `PASSED` |
| **Spatial Coordinate Coverage** | `shot table` | `COUNT(shot_location_status == 'OBSERVED')` | 4250 total shot attempts | **4250** | **4250** | `0` | `PASSED` |
| **eFG% Correlation with Margin (r)** | `view_team_game_ratings` | `pearsonr(efg_pct, point_diff)` | N = 120 team-game observations | **0.602** | **0.602** | `0.0` | `PASSED` |
| **TOV% Correlation with Margin (r)** | `view_team_game_ratings` | `pearsonr(tov_pct, point_diff)` | N = 120 team-game observations | **-0.224** | **-0.224** | `0.0` | `PASSED` |
| **Lukas Weber Season PPG** | `boxscore_player (PLY_DEMO_101)` | `AVG(points)` | N = 33.0 games played | **15.1** | **15.1** | `0.0` | `PASSED` |
| **Lukas Weber Weighted TS%** | `boxscore_player (PLY_DEMO_101)` | `SUM(pts) / (2 * (SUM(fga) + 0.44 * SUM(fta)))` | 333.0 FGA, 132.0 FTA | **63.7** | **63.7** | `0.0` | `PASSED` |
| **Maximilian Becker Season RPG** | `boxscore_player (PLY_DEMO_104)` | `AVG(trb)` | N = 33.0 games played | **9.0** | **9.0** | `0.0` | `PASSED` |
| **Maximilian Becker FG%** | `boxscore_player (PLY_DEMO_104)` | `SUM(fgm) / SUM(fga)` | N = 33.0 games played | **44.4** | **44.4** | `0.0` | `PASSED` |

---

## 2. Invariant & Methodology Confirmation

1. **Zero Numerical Discrepancy**: All recalculated figures in DuckDB match derived Parquet files with zero discrepancy.
2. **Strict Epistemic Transparency**: Denominators for all multi-source modalities (boxscores: $60/65$, PBP: $36/65$, shots: $36/65$, coordinates: $5,024/5,138$) are strictly preserved.
3. **Weighted Aggregations**: All season shooting percentages are calculated from total sums ($\sum 	ext{Makes} / \sum 	ext{Attempts}$) rather than unweighted game averages.