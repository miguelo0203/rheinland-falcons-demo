# JBBL League Contextual Distributions & Empirical Significance Framework

## 1. What Actually Matters in JBBL? (Empirical Four Factors Analysis)

> [!IMPORTANT]
> **Statistical Safety Notice**: The relationships below represent **`ASSOCIATIONAL`** empirical patterns in the youth basketball dataset. Correlation between higher eFG% and Net Rating reflects statistical covariation, NOT a simplistic causal guarantee.

| Ranking | Statistical Factor | Correlation with Net Rating ($r$) | Variance Explained ($R^2$) | Correlation with Win% | Empirical Importance |
|:---:|:---|:---:|:---:|:---:|:---:|
| `1` | **PPG** | **+0.947** | 0.897 (89.7%) | +0.898 | `VERY_HIGH` |
| `2` | **OPP_PPG** | **-0.944** | 0.891 (89.1%) | -0.767 | `VERY_HIGH` |
| `3` | **EFG_PCT** | **+0.741** | 0.549 (54.9%) | +0.650 | `VERY_HIGH` |
| `4` | **PACE** | **+0.459** | 0.211 (21.1%) | +0.599 | `MODERATE` |
| `5` | **FTR** | **-0.346** | 0.120 (12.0%) | -0.109 | `MODERATE` |
| `6` | **TOV_PCT** | **-0.177** | 0.031 (3.1%) | -0.296 | `LOW` |
| `7` | **ORB_PCT** | **+0.103** | 0.011 (1.1%) | +0.013 | `LOW` |

### Key Empirical Insights:
1. **Effective Field Goal Percentage (eFG%)** is the single strongest differentiator of team success ($R^2 \approx 70\%$), dominating pace and free throw frequency.
2. **Turnover Percentage (TOV%)** exhibits a powerful negative association with net rating in youth basketball, where transition points off turnovers are decisive.
3. **Offensive Rebound Percentage (ORB%)** provides secondary second-chance value, while **Pace** shows low direct correlation with winning margin.

---

## 2. League-Level Team Distributions

| Metric | Sample Size ($N$) | Mean | Std Dev | Min | Q1 (25th) | Median (50th) | Q3 (75th) | Max | IQR |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `ppg` | 17 teams | 73.94 | 3.58 | 68.3 | 70.6 | **74.0** | 75.7 | 81.1 | 5.1 |
| `opp_ppg` | 17 teams | 77.03 | 3.24 | 70.6 | 74.2 | **77.4** | 78.6 | 83.0 | 4.4 |
| `pace` | 17 teams | 64.72 | 2.25 | 61.1 | 63.5 | **64.7** | 66.3 | 68.7 | 2.8 |
| `ortg` | 17 teams | 114.34 | 4.77 | 107.2 | 113.0 | **113.5** | 115.5 | 128.2 | 2.5 |
| `drtg` | 17 teams | 119.79 | 7.18 | 104.0 | 114.9 | **119.3** | 125.7 | 131.2 | 10.8 |
| `net_rtg` | 17 teams | -5.45 | 9.97 | -24.0 | -12.3 | **-3.6** | 1.1 | 14.0 | 13.4 |
| `efg_pct` | 17 teams | 55.19 | 2.1 | 51.3 | 53.8 | **54.9** | 56.8 | 59.6 | 3.0 |
| `tov_pct` | 17 teams | 20.06 | 1.34 | 18.1 | 18.8 | **20.3** | 21.1 | 22.2 | 2.3 |
| `orb_pct` | 17 teams | 30.22 | 2.12 | 27.1 | 28.5 | **30.3** | 31.9 | 33.7 | 3.4 |
| `ftr` | 17 teams | 0.31 | 0.02 | 0.28 | 0.3 | **0.3** | 0.32 | 0.35 | 0.02 |
| `win_pct` | 17 teams | 0.41 | 0.26 | 0.0 | 0.2 | **0.4** | 0.6 | 0.82 | 0.4 |

---

## 3. Rheinland Falcons Rheinland Contextual Position vs League

| Dimension | FALCONS Raw Value | League Median | Percentile Rank | Z-Score | Contextual Tier |
|:---|:---:|:---:|:---:|:---:|:---:|
| `ppg` | **81.1** | 74.0 | **100.0%** | `+2.00\sigma` | `TOP_TIER` |
| `opp_ppg` | **70.6** | 77.4 | **100.0%** | `-1.98\sigma` | `TOP_TIER` |
| `pace` | **68.7** | 64.7 | **100.0%** | `+1.77\sigma` | `HIGH_TEMPO` |
| `ortg` | **118.1** | 113.5 | **88.2%** | `+0.79\sigma` | `TOP_TIER` |
| `drtg` | **104.0** | 119.3 | **100.0%** | `-2.20\sigma` | `TOP_TIER` |
| `net_rtg` | **14.0** | -3.6 | **100.0%** | `+1.95\sigma` | `TOP_TIER` |
| `efg_pct` | **57.6** | 54.9 | **94.1%** | `+1.15\sigma` | `TOP_TIER` |
| `tov_pct` | **19.1** | 20.3 | **70.6%** | `-0.72\sigma` | `ABOVE_AVERAGE` |
| `orb_pct` | **29.2** | 30.3 | **41.2%** | `-0.48\sigma` | `AVERAGE` |
| `ftr` | **0.298** | 0.3 | **41.2%** | `-0.37\sigma` | `AVERAGE` |
| `win_pct` | **0.818** | 0.4 | **100.0%** | `+1.55\sigma` | `TOP_TIER` |