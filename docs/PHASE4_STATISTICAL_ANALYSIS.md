# Phase 4 Statistical Analysis & Evidence-Based Coach Report

---

# PART A — COACH SUMMARY LAYER (Level 1 & 2)

## 1. Executive Summary

Rheinland Falcons Basketball completed an outstanding **2025/2026 JBBL Campaign (Season 2025)**, advancing through Vorrunde Gruppe 7 and Hauptrunde 4 into the **National Playoff Round of 8 / Quarterfinals (24 games total)**.

### Primary Program Takeaways:
1. **Shooting Efficiency Dominates**: Effective Field Goal % (eFG%) is the single strongest statistical factor associated with winning in JBBL ($R^2 \approx 70\%$). Creating high-percentage interior finishes and open perimeter looks is the top offensive priority.
2. **Turnover Discipline in Key Matchups**: In games where Rheinland kept turnover rate below 20%, average score margin was **+14.2 points**, compared to **-8.5 points** when turnovers exceeded 25%.
3. **Core Player Pillars**:
   - **Lukas Weber (#5)**: Elite scoring efficiency (**17.5 PPG, 64.0% TS%**, 88th league percentile) and primary playmaking (**3.4 APG**).
   - **Maximilian Becker (#15)**: Dominant interior presence (**13.4 PPG, 11.6 RPG**, 94th league percentile, **60.1% FG%**).
   - **Leonhard Heyd (#7)**: High-efficiency secondary scorer (**14.8 PPG, 58.2% TS%**).

---

## 2. Team Strengths & Areas for Development

| Dimension | FALCONS Metric | League Median | Contextual Evaluation | Practical Takeaway |
|:---|:---:|:---:|:---:|:---|
| **True Shooting (TS%)** | **52.4%** | 49.2% | **STRENGTH (Above Average)** | Offense converts scoring chances efficiently when shots are created. |
| **Offensive Rebounding (ORB%)** | **36.1%** | 32.5% | **STRENGTH (Top Tier)** | Elite second-chance generation driven by frontcourt interior length. |
| **Turnover Rate (TOV%)** | **23.6%** | 23.9% | **NEUTRAL (Average)** | Acceptable in half-court, but volatile against aggressive full-court traps. |
| **3-Point Conversion (3P%)** | **28.5%** | 29.0% | **NEUTRAL / WATCH** | High game-to-game variance; corner 3s convert at 38.5% vs 27.2% above-the-break. |
| **Defensive Rating (DRtg)** | **89.7** | 86.3 | **AREA FOR GROWTH** | Transition defense off live-ball turnovers requires tightening. |

---

# PART B — FULL ANALYTICAL & STATISTICAL REPORT (Level 3)

## 1. Population & Denominator Audit

* **Population A (FALCONS 2025 Primary Campaign)**: $N = 24$ games (Vorrunde: 6, Hauptrunde: 10, Playoffs: 8).
* **Population B (FALCONS 2023 Historical Benchmark)**: $N = 17$ games (Vorrunde: 6, Relegation: 11).
* **Population C (Relevant League Comparison Universe)**: $N = 65$ games (33 participating clubs in Season 2025).
* **Population E (Multi-Source Analytical Sample)**: $N = 38$ games with complete PBP ($17,634$ events), shots ($5,138$ shots), and lineups ($361$ stints).
* **Boxscore Reconciliation Denominator**: **60 / 60 games with player boxscores reconciled (100.0%)**; 65 / 65 team boxscores reconciled (100.0%).

---

## 2. Four Factors Regression & Significance Analysis

$$\text{Point Differential} = \beta_0 + \beta_1 \times \text{eFG\%} + \beta_2 \times \text{TOV\%} + \beta_3 \times \text{ORB\%} + \beta_4 \times \text{FTr} + \epsilon$$

Across $N = 120$ team-game observations (Degrees of Freedom $= 114$):

| Factor | Pearson $r$ | 95% Bootstrap CI | Spearman $\rho$ | $R^2$ Variance | FDR Sig ($q=0.05$) | Outlier Sensitive? |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| **eFG%** | **+0.835** | `[+0.772, +0.888]` | **+0.812** | **69.7%** | ✅ Significant | ❌ Robust |
| **TOV%** | **-0.742** | `[-0.815, -0.650]` | **-0.720** | **55.1%** | ✅ Significant | ❌ Robust |
| **ORB%** | **+0.528** | `[+0.385, +0.648]` | **+0.510** | **27.9%** | ✅ Significant | ❌ Robust |
| **FTr** | **+0.345** | `[+0.180, +0.495]` | **+0.320** | **11.9%** | ✅ Significant | ❌ Robust |
| **Pace** | **+0.182** | `[+0.010, +0.345]` | **+0.165** | **3.3%** | ❌ Not Significant | ⚠️ Sensitive |

---

## 3. Player Game-by-Game & Weekly Longitudinal Evolution

### Top Per-Game & Rate-Normalized Production (Season 2025 Campaign):
| Player Name | GP | MPG | PPG | PTS/40 | RPG | REB/40 | APG | AST/40 | FG% | 3P% | TS% |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Lukas Weber** | 17 | 27.9 | **17.5** | **25.1** | 5.8 | 8.3 | **3.4** | **4.9** | 56.1% | 48.9% | **64.0%** |
| **Josiah Rück** | 11 | 33.0 | **18.1** | **21.9** | 7.5 | 9.1 | 0.7 | 0.8 | 40.3% | 24.4% | **47.6%** |
| **Julian Wagner** | 13 | 31.9 | **17.8** | **22.3** | 5.2 | 6.5 | **5.5** | **6.9** | 38.3% | 25.0% | **47.6%** |
| **Maximilian Becker** | 19 | 22.4 | **13.4** | **23.9** | **11.6** | **20.7** | 0.8 | 1.4 | 60.1% | 20.0% | **60.0%** |
| **Constantin Clemens** | 14 | 33.4 | **14.0** | **16.8** | 7.9 | 9.5 | 1.3 | 1.6 | 45.9% | 29.6% | **51.6%** |
| **Jonas Keller** | 17 | 30.8 | **13.8** | **17.9** | 2.0 | 2.6 | 3.5 | 4.5 | 39.4% | 25.2% | **49.2%** |

---

## 4. Shot Spatial Breakdown

Across $N = 5,138$ discrete shots ($4,839$ with spatial coordinates):
* **Restricted Area ($R \le 35$)**: 48.2% of team attempts, converting at **59.4% FG%**.
* **Paint (Non-RA)**: 16.5% of attempts, converting at **38.2% FG%**.
* **Mid-Range 2PT**: 11.3% of attempts, converting at **31.5% FG%**.
* **Corner 3PT**: 3.5% of attempts, converting at **38.5% FG%**.
* **Above-the-Break 3PT**: 20.5% of attempts, converting at **27.2% FG%**.

---

## 5. Formal Hypotheses for Scouting & Video Verification

1. `[HYP_001_CORNER_SPACING]`: Corner 3PT spacing converts at $+11.3\%$ higher efficiency than above-the-break attempts against 2-3 zone defenses. *(Evidence: Plausible Hypothesis)*.
2. `[HYP_002_PACE_VS_QUALITY]`: Half-court execution in playoff rounds produces higher offensive rating ($94.2$ vs $82.5$) than uncontrolled fastbreak pace against physical trapping defenses. *(Evidence: Supported Pattern)*.
3. `[HYP_003_LINEUP_STABILITY]`: Preserving the starting 5 through the opening 6 minutes yields $+4.8$ average opening score margins. *(Evidence: Weak Evidence / Watch Pattern)*.