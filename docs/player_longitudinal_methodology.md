# Longitudinal Player Performance & Multi-Game Evolution Methodology

## 1. Longitudinal Architecture & Aggregation Layers

The sandbox implements a 3-tier longitudinal performance framework to track player development without small-sample distortions:

```text
LEVEL 1: Granular Game Log (player_game_performance.parquet) [1 Row / Player x Game]
  │
  ▼
LEVEL 2: Rolling Trajectories (player_rolling_performance.parquet) [3-Game & 5-Game Windows]
  │
  ▼
LEVEL 3: Weekly Aggregations (player_weekly_performance.parquet) [Player x Competition Week]
```

---

## 2. Four-Game Player Evolution Demonstration (`SHORT_SAMPLE_DEMONSTRATION`)

> [!IMPORTANT]
> **Methodological Notice**: The 4-game sequences below are presented strictly as a **`SHORT_SAMPLE_DEMONSTRATION`** to illustrate the trajectory mechanics of the monitoring framework. In accordance with our statistical safety protocol, 4 games do not constitute a definitive long-term developmental trend.

### Player Evolution: Lukas Weber (Rheinland Falcons Basketball)

| Game Seq | Date | Opponent | H/A | MIN | PTS | FG% | 3P% | FT% | TS% | TRB | AST | TOV | Starter | Score Margin |
|:---:|:---:|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `Game 1` (N-3) | 2026-03-22 00:00:00 | Isar Bulls U16 | Home | 29.3 | **22** | 72.7% | 66.7% | 80.0% | **83.3%** | 6 | 6 | 5 | Bench | 13 |
| `Game 2` (N-2) | 2026-03-27 00:00:00 | Isar Bulls U16 | Away | 31.33 | **17** | 40.0% | 33.3% | 80.0% | **59.0%** | 3 | 3 | 4 | Bench | -1 |
| `Game 3` (N-1) | 2026-03-29 00:00:00 | Isar Bulls U16 | Home | 25.33 | **22** | 63.6% | 50.0% | 85.7% | **78.1%** | 8 | 1 | 2 | Bench | 21 |
| `Game 4` (N-0) | 2026-04-26 00:00:00 | Ruhr Titans U16 | Away | 27.3 | **16** | 55.6% | 66.7% | 100.0% | **74.3%** | 1 | 1 | 3 | Bench | -2 |

- **4-Game Scoring Progression**: 22 $\to$ 16 PTS ($\Delta = -6$ PTS)
- **4-Game True Shooting Efficiency**: 83.3% $\to$ 74.3% TS% ($\Delta = -9.0\%$ TS)

### Player Evolution: Julian Wagner (Rheinland Falcons Basketball)

| Game Seq | Date | Opponent | H/A | MIN | PTS | FG% | 3P% | FT% | TS% | TRB | AST | TOV | Starter | Score Margin |
|:---:|:---:|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `Game 1` (N-3) | 2026-03-22 00:00:00 | Isar Bulls U16 | Home | 32.47 | **20** | 43.8% | 11.1% | 100.0% | **54.9%** | 4 | 10 | 2 | Bench | 13 |
| `Game 2` (N-2) | 2026-03-27 00:00:00 | Isar Bulls U16 | Away | 36.37 | **17** | 30.4% | 25.0% | nan% | **37.0%** | 5 | 2 | 3 | Bench | -1 |
| `Game 3` (N-1) | 2026-03-29 00:00:00 | Isar Bulls U16 | Home | 29.63 | **8** | 23.1% | 0.0% | 50.0% | **27.1%** | 9 | 6 | 2 | Bench | 21 |
| `Game 4` (N-0) | 2026-04-26 00:00:00 | Ruhr Titans U16 | Away | 37.3 | **18** | 26.1% | 15.4% | 100.0% | **36.3%** | 2 | 2 | 5 | Bench | -2 |

- **4-Game Scoring Progression**: 20 $\to$ 18 PTS ($\Delta = -2$ PTS)
- **4-Game True Shooting Efficiency**: 54.9% $\to$ 36.3% TS% ($\Delta = -18.6\%$ TS)

### Player Evolution: Lukas Rademacher (Isar Bulls U16)

| Game Seq | Date | Opponent | H/A | MIN | PTS | FG% | 3P% | FT% | TS% | TRB | AST | TOV | Starter | Score Margin |
|:---:|:---:|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `Game 1` (N-3) | 2026-02-22 00:00:00 | Rheinland Falcons Basketball | Away | 35.22 | **29** | 36.8% | 35.7% | 100.0% | **62.0%** | 5 | 6 | 4 | Bench | -5 |
| `Game 2` (N-2) | 2026-03-22 00:00:00 | Rheinland Falcons Basketball | Away | 31.68 | **26** | 38.1% | 37.5% | 80.0% | **56.0%** | 4 | 2 | 5 | Bench | -13 |
| `Game 3` (N-1) | 2026-03-27 00:00:00 | Rheinland Falcons Basketball | Home | 36.75 | **31** | 56.3% | 53.8% | 100.0% | **83.2%** | 3 | 6 | 1 | Bench | 1 |
| `Game 4` (N-0) | 2026-03-29 00:00:00 | Rheinland Falcons Basketball | Away | 35.45 | **11** | 28.6% | 37.5% | nan% | **39.3%** | 5 | 1 | 4 | Bench | -21 |

- **4-Game Scoring Progression**: 29 $\to$ 11 PTS ($\Delta = -18$ PTS)
- **4-Game True Shooting Efficiency**: 62.0% $\to$ 39.3% TS% ($\Delta = -22.7\%$ TS)

---

## 3. Small-Sample Protection Invariants

1. **Sample Threshold Guards**:
   - $N < 3$ games: Flagged as `SMALL_SAMPLE` (Uncertainty: `HIGH`). No trend claims permitted.
   - $3 \le N < 5$ games: Flagged as `INTERMEDIATE_SAMPLE` (Uncertainty: `MEDIUM`). Exposes rolling trajectory only.
   - $N \ge 5$ games: Flagged as `STABLE_SAMPLE` (Uncertainty: `LOW`). Evaluated against season baseline.
2. **Zero-Baseline Safeguard**: Percentage changes are never computed when the baseline is zero or unstable.