# Metric Context Engine, Denominators & Epistemic Methodology
## Rheinland Falcons Basketball — JBBL / NBBL Longitudinal Intelligence Platform

---

## 1. Core Principles of Contextual Reporting

In this platform, **no metric is ever displayed in isolation**. Every statistical output must be accompanied by its mathematical denominator, sample exposure, normative distribution, and epistemic reliability.

```text
┌────────────────────────────────────────────────────────────────────────┐
│                        RAW OBSERVED METRIC                             │
│                      e.g. 3P% = 48.9% (23/47)                          │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
      ┌────────────────────────────┼────────────────────────────┐
      ▼                            ▼                            ▼
┌──────────────┐          ┌──────────────────┐         ┌─────────────────┐
│ DENOMINATOR  │          │ LEAGUE BENCHMARK │         │   SAMPLE SIZE   │
│ & EXPOSURE   │          │  & PERCENTILE    │         │  RELIABILITY    │
│ 47 Attempts  │          │  94th Percentile │         │ EMERGING SIGNAL │
│ in 19 Games  │          │  (Median: 24.7%) │         │  (N = 47 3PA)   │
│ (2.5 3PA/G)  │          │                  │         │                 │
└──────────────┘          └──────────────────┘         └─────────────────┘
      │                            │                            │
      └────────────────────────────┼────────────────────────────┘
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│                DYNAMICALLY SYNTHESIZED CONTEXT CARD                    │
│ "Lukas Weber converts at an elite 48.9% 3P rate (94th percentile in    │
│ JBBL), attempting 2.5 threes per game across 19 appearances. While     │
│ highly promising, the 47-shot volume represents an emerging sample;   │
│ maintain volume monitoring across additional matchdays."               │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Exhaustive Metric Denominator & Formula Dictionary

Every player metric implemented in the system is defined below with its exact mathematical formulation, numerator, denominator, boundary handling, and population reference:

### Exposure Metrics
1. **Minutes per Game (MPG)**:
   $$	ext{MPG} = rac{\sum 	ext{Seconds Played}}{60.0 	imes 	ext{Games Played}}$$
   - *Denominator*: Games Played ($GP \ge 1$). If $GP = 0 \implies 	ext{NULL}$.
2. **Minutes Share (%MIN)**:
   $$	ext{Minutes Share} = rac{\sum 	ext{Seconds Played}}{60.0 	imes (200.0 	imes 	ext{Team Games Played})}$$
   - *Denominator*: Total available team regulation player-minutes ($5 	ext{ players} 	imes 40 	ext{ min} = 200 	ext{ min/game}$).

### Scoring & Rate Metrics
3. **Points per Game (PPG)**:
   $$	ext{PPG} = rac{\sum 	ext{Points}}{	ext{Games Played}}$$
4. **Points per 40 Minutes (PTS/40)**:
   $$	ext{PTS/40} = 40.0 	imes rac{\sum 	ext{Points}}{\sum 	ext{Minutes Played}}$$
   - *Denominator*: Total minutes played. Requires $	ext{Minutes} \ge 10.0$ to avoid division-by-zero artifacts.
5. **Usage Proxy (USG% Proxy)**:
   $$	ext{USG\% Proxy} = 100.0 	imes rac{(	ext{FGA} + 0.44 	imes 	ext{FTA} + 	ext{TOV}) 	imes (	ext{Team Minutes} / 5)}{	ext{Player Minutes} 	imes (	ext{Team FGA} + 0.44 	imes 	ext{Team FTA} + 	ext{Team TOV})}$$
   - *Denominator*: Team shooting possessions scaled by player's on-court time.

### Shooting Efficiency Metrics
6. **Field Goal Percentage (FG%)**:
   $$	ext{FG\%} = 100.0 	imes rac{	ext{FGM}}{	ext{FGA}}$$
   - *Denominator*: Total Field Goal Attempts ($	ext{FGA} = 	ext{2PA} + 	ext{3PA}$). If $	ext{FGA} = 0 \implies 	ext{NULL}$.
7. **2-Point Percentage (2P%)**:
   $$	ext{2P\%} = 100.0 	imes rac{	ext{2PM}}{	ext{2PA}}$$
   - *Denominator*: 2-Point Attempts.
8. **3-Point Percentage (3P%)**:
   $$	ext{3P\%} = 100.0 	imes rac{	ext{3PM}}{	ext{3PA}}$$
   - *Denominator*: 3-Point Attempts.
9. **Free Throw Percentage (FT%)**:
   $$	ext{FT\%} = 100.0 	imes rac{	ext{FTM}}{	ext{FTA}}$$
   - *Denominator*: Free Throw Attempts.
10. **Effective Field Goal Percentage (eFG%)**:
    $$	ext{eFG\%} = 100.0 	imes rac{	ext{FGM} + 0.5 	imes 	ext{3PM}}{	ext{FGA}}$$
    - *Purpose*: Rewards the 50% scoring premium of 3-point field goals.
11. **True Shooting Percentage (TS%)**:
    $$	ext{TS\%} = 100.0 	imes rac{	ext{Points}}{2 	imes (	ext{FGA} + 0.44 	imes 	ext{FTA})}$$
    - *Denominator*: Estimated total shooting possessions (where $0.44 	imes 	ext{FTA}$ accounts for and-1s, technical fouls, and 2/3-shot fouls).
12. **3-Point Attempt Rate (3PAr)**:
    $$	ext{3PAr} = 100.0 	imes rac{	ext{3PA}}{	ext{FGA}}$$
    - *Purpose*: Measures perimeter shot diet proportion.
13. **Free Throw Rate (FTr)**:
    $$	ext{FTr} = 100.0 	imes rac{	ext{FTA}}{	ext{FGA}}$$
    - *Purpose*: Measures ability to generate foul pressure relative to field goal attempts.

### Rebounding, Playmaking & Defense
14. **Rebounds per 40 (REB/40)**, **Assists per 40 (AST/40)**, **Steals per 40 (STL/40)**, **Blocks per 40 (BLK/40)**, **Turnovers per 40 (TOV/40)**:
    $$	ext{Stat/40} = 40.0 	imes rac{\sum 	ext{Stat}}{\sum 	ext{Minutes Played}}$$
15. **Assist-to-Turnover Ratio (AST/TOV)**:
    $$	ext{AST/TOV} = rac{\sum 	ext{AST}}{\sum 	ext{TOV}}$$
    - *Denominator*: Total Turnovers. If $	ext{TOV} = 0$, represented as $	ext{AST} / 0 \implies 	ext{UNDEFINED}$ (or displayed as $	ext{AST}$ with note).
16. **Game Score (John Hollinger)**:
    $$	ext{GmSc} = 	ext{PTS} + 0.4 	imes 	ext{FGM} - 0.7 	imes 	ext{FGA} - 0.4 	imes (	ext{FTA} - 	ext{FTM}) + 0.7 	imes 	ext{ORB} + 0.3 	imes 	ext{DRB} + 	ext{STL} + 0.7 	imes 	ext{AST} + 0.7 	imes 	ext{BLK} - 0.4 	imes 	ext{PF} - 	ext{TOV}$$

---

## 3. Sample Size & Evidentiary Reliability Framework

To protect coaching staff from drawing definitive conclusions from ephemeral small samples, the system applies **metric-specific stability thresholds**:

| Metric Domain | `NO_DATA` | `DESCRIPTIVE_ONLY` (Caution) | `EMERGING_SIGNAL` (Exploratory) | `USABLE_SIGNAL` (Moderate) | `ESTABLISHED_SIGNAL` (High Conf) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Exposure / Playing Time** | $N=0$ GP | $1	ext{--}3$ Games ($<40$ min) | $4	ext{--}7$ Games ($40	ext{--}99$ min) | $8	ext{--}14$ Games ($100	ext{--}249$ min) | $\ge 15$ Games ($\ge 250$ min) |
| **Overall Scoring (PPG, PTS/40)** | $N=0$ FGA | $< 25$ FGA | $25	ext{--}74$ FGA | $75	ext{--}149$ FGA | $\ge 150$ FGA |
| **2-Point Shooting (2P%)** | $N=0$ 2PA | $< 20$ 2PA | $20	ext{--}49$ 2PA | $50	ext{--}99$ 2PA | $\ge 100$ 2PA |
| **3-Point Shooting (3P%)** | $N=0$ 3PA | $< 25$ 3PA | $25	ext{--}74$ 3PA | $75	ext{--}199$ 3PA | $\ge 200$ 3PA |
| **Free Throw Shooting (FT%)** | $N=0$ FTA | $< 20$ FTA | $20	ext{--}49$ FTA | $50	ext{--}99$ FTA | $\ge 100$ FTA |
| **True Shooting (TS%)** | $N=0$ TSA | $< 30$ TSA | $30	ext{--}89$ TSA | $90	ext{--}179$ TSA | $\ge 180$ TSA |
| **Rebounding (REB/40)** | $N=0$ Min | $< 40$ Minutes | $40	ext{--}99$ Minutes | $100	ext{--}249$ Minutes | $\ge 250$ Minutes |
| **Playmaking (AST/40, AST/TOV)**| $N=0$ Min | $< 40$ Minutes | $40	ext{--}99$ Minutes | $100	ext{--}249$ Minutes | $\ge 250$ Minutes |
| **Rim Protection (BLK/40)** | $N=0$ Min | $< 50$ Minutes | $50	ext{--}119$ Minutes | $120	ext{--}299$ Minutes | $\ge 300$ Minutes |
| **Rolling Trend ($\Delta$ Baseline)**| $N < 4$ G | $N = 4$ Games | $5	ext{--}7$ Games | $8	ext{--}11$ Games | $\ge 12$ Games |

---

## 4. Normative League Benchmark Distributions (Isolated SEA_2025 JBBL Universe)

Empirical quantiles derived strictly from all **34 qualified JBBL players in season 2025/26 (`SEA_2025`) with $\ge 100$ minutes played in official competition**:

| Metric | Min | 10th %ile | 25th %ile | Median (50th) | 75th %ile | 90th %ile | Max | Mean $\pm$ Std |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Points / Game (PPG)** | 0.5 | 3.0 | 6.5 | **9.8** | 14.0 | 19.1 | 24.4 | $10.3 \pm 6.3$ |
| **Points / 40 (PTS/40)** | 2.7 | 5.9 | 10.9 | **16.9** | 22.1 | 28.1 | 39.1 | $17.2 \pm 8.7$ |
| **True Shooting (TS%)** | 26.8%| 38.5%| 42.7%| **49.1%** | 55.8%| 63.3%| 71.5%| $49.3\% \pm 10.5\%$ |
| **3-Point % (3P%)** | 0.0% | 7.1% | 17.0%| **25.0%** | 34.8%| 37.5%| 48.9%| $24.4\% \pm 12.8\%$ |
| **Rebounds / 40 (REB/40)** | 2.6 | 3.9 | 5.2 | **8.4** | 10.1 | 16.9 | 20.7 | $8.7 \pm 4.8$ |
| **Assists / 40 (AST/40)** | 0.2 | 1.3 | 2.4 | **3.5** | 4.8 | 5.6 | 7.9 | $3.6 \pm 1.8$ |
| **AST / TOV Ratio** | 0.2 | 0.3 | 0.6 | **0.8** | 1.1 | 1.3 | 1.9 | $0.8 \pm 0.4$ |
| **Steals / 40 (STL/40)** | 0.0 | 1.3 | 2.0 | **3.1** | 4.6 | 5.0 | 6.3 | $3.2 \pm 1.6$ |
| **Blocks / 40 (BLK/40)** | 0.0 | 0.0 | 0.0 | **0.2** | 1.1 | 2.0 | 2.4 | $0.6 \pm 0.8$ |

### Benchmark Isolation Guarantees:
- **Season Isolation**: `game.season_id == player.season_id` (zero cross-season pooling).
- **Competition Isolation**: `game.competition_id == 'CMP_JBBL'`.
- **Game Type Isolation**: `game.game_type == 'OFFICIAL'`.
- **Temporal Cutoff**: `game.game_date <= as_of_date` (when specified).
- **Placeholder Exclusion**: `bp.player_id != 'PLY_None'`.
- **Qualification Filtering**: `SUM(seconds_played)/60.0 >= 100.0` applied *after* partition filtering.

---

## 5. Dynamic Context Sentence Generation Rules

The Context Engine dynamically constructs human-readable coach sentences using deterministic parameter mapping:

```python
def generate_metric_card(metric_name, observed_val, count_val, exposure_val, percentile_val, stability_tier):
    # 1. Volume Descriptor
    if percentile_val >= 90:
        tier_desc = "elite"
    elif percentile_val >= 75:
        tier_desc = "above-average"
    elif percentile_val >= 40:
        tier_desc = "league-average"
    else:
        tier_desc = "below-average"
        
    # 2. Sample Caution Note
    if stability_tier == "DESCRIPTIVE_ONLY":
        caution = "Note: Very small sample; descriptive only, do not extrapolate."
    elif stability_tier == "EMERGING_SIGNAL":
        caution = "Note: Emerging signal across limited volume; maintain monitoring."
    else:
        caution = "Established sample."
        
    return {
        "display_value": f"{observed_val}",
        "context_sentence": f"Performs in the {tier_desc} tier ({percentile_val:.0f}th percentile) with {count_val} occurrences across {exposure_val}.",
        "sample_warning": caution
    }
```
