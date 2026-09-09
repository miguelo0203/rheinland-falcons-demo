# Rheinland Falcons Basketball — Metric Semantics & Epistemic Catalog

**Version:** 1.0 (Post-Audit Specification)  
**Date:** 2026-09-02  
**Scope:** JBBL / NBBL Longitudinal Basketball Intelligence Platform (`F:\Rheinland Falcons Prueba`)  
**Reference Domain Agent:** Basketball Quantitative Analytics & Epistemic Decision Support  

---

## 1. Executive Overview & Semantic Architecture

This catalog serves as the canonical single source of truth for all analytical metrics utilized across the Rheinland Falcons Basketball Intelligence application. It defines the mathematical derivation, basketball semantic direction, percentile orientation, color semantics, and coach-facing explanations for every metric.

### Semantic Direction Taxonomy

1. **`HIGHER_IS_BETTER`**: Numerical increase represents superior performance (e.g., Offensive Rating, True Shooting %, Assist-to-Turnover Ratio).
2. **`LOWER_IS_BETTER`**: Numerical decrease represents superior performance (e.g., Defensive Rating, Turnover Rate, Opponent PPG). **Requires inverted percentile calculations so that superior defense/ball security maps to higher percentiles.**
3. **`CONTEXT_DEPENDENT`**: Numerical magnitude reflects style of play, tactical role, or opportunity volume rather than intrinsic quality (e.g., Pace, Minutes, 3-Point Attempt Rate). **Never color-coded as green/red or labeled with evaluative tiers.**
4. **`TARGET_RANGE`**: Optimal performance is situated within a defined bounded interval (e.g., Assist-to-Turnover ratio 1.5–3.5, Shot Diet shares).
5. **`DESCRIPTIVE_ONLY`**: Raw contextual traits and counting totals (e.g., Games Played, Height, Age, Jersey Number).

---

## 2. Complete Metric Inventory & Semantic Dictionary

### 2.1. Team Efficiency & Rating Metrics

| Canonical Metric | UI Display Label | Category | Direction | Formula | Denominator | Unit | Sorting | Coach Explanation |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `ortg` | Offensive Rating (ORTG) | Team Efficiency | `HIGHER_IS_BETTER` | $100 \times \frac{\text{Points}}{\text{Possessions}}$ | Team Possessions | Pts / 100 poss | `DESC` | Points produced per 100 offensive possessions. Evaluates scoring efficiency adjusted for tempo. |
| `drtg` | Defensive Rating (DRTG) | Team Efficiency | `LOWER_IS_BETTER` | $100 \times \frac{\text{Opp Points}}{\text{Opp Possessions}}$ | Opponent Possessions | Opp Pts / 100 poss | `ASC` | Points allowed per 100 opponent possessions. **LOWER IS BETTER.** Evaluates defensive stinginess adjusted for tempo. |
| `net_rtg` | Net Rating (NetRtg) | Team Efficiency | `HIGHER_IS_BETTER` | $\text{ORTG} - \text{DRTG}$ | 100 Possessions | Pts / 100 poss | `DESC` | Net point differential per 100 possessions. The definitive measure of overall team dominance. |
| `ppg` | Points Per Game | Scoring Volume | `HIGHER_IS_BETTER` | $\frac{\sum \text{Points}}{\text{Games}}$ | Games Played | PTS | `DESC` | Average points scored per game. Influenced by pace and minutes. |
| `opp_ppg` | Opponent Points Per Game | Team Defense | `LOWER_IS_BETTER` | $\frac{\sum \text{Opp Points}}{\text{Games}}$ | Games Played | Opp PTS | `ASC` | Average points conceded per game. **LOWER IS BETTER.** Influenced by game pace. |
| `point_diff` | Score Margin (+/-) | Match Outcome | `HIGHER_IS_BETTER` | $\text{Points} - \text{Opp Points}$ | Game | PTS | `DESC` | Net scoring margin in a game or across a season. |
| `win_pct` | Win Percentage (Win %) | Match Outcome | `HIGHER_IS_BETTER` | $\frac{\text{Wins}}{\text{Games Played}} \times 100$ | Games Played | % | `DESC` | Proportion of matches won. |

---

### 2.2. Dean Oliver Four Factors & Empirical Significance (JBBL Universe)

| Canonical Metric | UI Display Label | Four Factor Domain | Direction | Formula | Empirical $r$ with Win Margin | Empirical $R^2$ Variance Explained | JBBL Impact Level |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `efg_pct` | Effective FG% (eFG%) | Shooting Efficiency | `HIGHER_IS_BETTER` | $\frac{\text{FGM} + 0.5 \times \text{3PM}}{\text{FGA}} \times 100$ | $+0.835$ | $69.8\%$ | **CRITICAL (Dominant Factor)** |
| `tov_pct` | Turnover Rate (TOV%) | Ball Security | `LOWER_IS_BETTER` | $\frac{\text{TOV}}{\text{FGA} + 0.44 \times \text{FTA} + \text{TOV}} \times 100$ | $-0.667$ | $44.5\%$ | **HIGH (Decisive Transition Points)** |
| `orb_pct` | Offensive Rebound % (ORB%) | Second Possessions | `HIGHER_IS_BETTER` | $\frac{\text{ORB}}{\text{ORB} + \text{Opp DRB}} \times 100$ | $+0.510$ | $26.0\%$ | **MODERATE (Extra Possessions)** |
| `ftr` | Free Throw Rate (FTR) | Drawing Fouls | `HIGHER_IS_BETTER` | $\frac{\text{FTA}}{\text{FGA}}$ | $+0.320$ | $10.2\%$ | **SECONDARY** |
| `pace` | Pace (Possessions / 40m) | Game Tempo | `CONTEXT_DEPENDENT` | $\frac{\text{Possessions} \times 40}{\text{Minutes}}$ | $-0.090$ | $0.8\%$ | **NEUTRAL (Style, Not Quality)** |

---

### 2.3. Individual Player Production & Rate Metrics (Per-40 Regulation Minutes)

| Canonical Metric | UI Display Label | Category | Direction | Formula | Denominator | Unit | Sorting | Coach Explanation |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `pts_per_40` | Points Per 40 Min (PTS/40) | Scoring Rate | `HIGHER_IS_BETTER` | $\text{PTS} \times \frac{40}{\text{MIN}}$ | Regulation Minutes | PTS / 40m | `DESC` | Normalized scoring rate removing playing-time bias. Evaluates per-minute offensive output. |
| `ts_pct` | True Shooting % (TS%) | Scoring Efficiency | `HIGHER_IS_BETTER` | $\frac{\text{PTS}}{2 \times (\text{FGA} + 0.44 \times \text{FTA})} \times 100$ | True Shooting Attempts | % | `DESC` | Complete individual shooting efficiency capturing 2PT, 3PT, and FT conversion. |
| `reb_per_40` | Rebounds Per 40 Min (REB/40) | Glass Control | `HIGHER_IS_BETTER` | $\text{TRB} \times \frac{40}{\text{MIN}}$ | Regulation Minutes | REB / 40m | `DESC` | Normalized rebounding production per 40 regulation minutes. |
| `ast_per_40` | Assists Per 40 Min (AST/40) | Playmaking Creation | `HIGHER_IS_BETTER` | $\text{AST} \times \frac{40}{\text{MIN}}$ | Regulation Minutes | AST / 40m | `DESC` | Normalized shot-creation and distribution rate for teammates. |
| `ast_to_tov` | Assist-to-Turnover Ratio | Decision Security | `HIGHER_IS_BETTER` | $\frac{\text{AST}}{\text{TOV}}$ | Turnovers | Ratio | `DESC` | Facilitation quality and ball security. $>1.5$ indicates strong decision-making; $>2.0$ is elite. |
| `def_disruption` | Defensive Disruption Rate | Event Defense | `HIGHER_IS_BETTER` | $(\text{STL} + \text{BLK}) \times \frac{40}{\text{MIN}}$ | Regulation Minutes | Events / 40m | `DESC` | Defensive playmaking event rate combining passing-lane steals and rim protection blocks. |
| `tov_per_40` | Turnovers Per 40 Min (TOV/40) | Ball Security | `LOWER_IS_BETTER` | $\text{TOV} \times \frac{40}{\text{MIN}}$ | Regulation Minutes | TOV / 40m | `ASC` | Turnover rate per 40 minutes. **LOWER IS BETTER.** Evaluates ball security under minutes exposure. |
| `f3a_rate` | 3-Point Attempt Rate (3PAr) | Shot Diet & Role | `CONTEXT_DEPENDENT` | $\frac{\text{3PA}}{\text{FGA}} \times 100$ | Total Field Goals | % | `DESC` | Perimeter shot share. Indicates offensive role (perimeter spacing vs interior driving). |
| `min_share_pct` | Team Minutes Share % | Rotation Role | `CONTEXT_DEPENDENT` | $\frac{\text{Player MIN}}{\text{Games} \times 200} \times 100$ | Team 200-Min Game Pool | % | `DESC` | Percentage of total team court minutes captured by the player. |
| `mpg` | Minutes Per Game (MPG) | Rotation Volume | `CONTEXT_DEPENDENT` | $\frac{\sum \text{MIN}}{\text{Games Played}}$ | Games Played | MIN | `DESC` | Average court exposure per game. Indicates coaching rotation hierarchy. |

---

### 2.4. Shooting Diet & Tactical Court Zones

| Zone Identifier | UI Display Name | Physical Geometry | Expected Points (JBBL Baseline) | Tactical Meaning & Coaching Interpretation |
| :--- | :--- | :--- | :--- | :--- |
| `RESTRICTED_AREA` | Restricted Area ($d \le 1.5\text{m}$) | Under basket circle | 1.25 – 1.35 EPPA | Highest-value half-court shot. Direct metric of rim pressure and paint penetration. |
| `PAINT_NON_RA` | Paint (Non-RA) | Key outside 1.5m | 0.80 – 0.95 EPPA | Floaters, short push shots, post hooks. Moderate efficiency. |
| `MID_RANGE` | Mid-Range (2PT) | 2PT area outside paint | 0.65 – 0.75 EPPA | Lowest-value shot in youth basketball. High defensive contest, low return. |
| `CORNER_3PT` | Corner 3PT | 3PT line ($y \le 5.5\text{m}$) | 1.10 – 1.20 EPPA | High-value perimeter shot ($+11.3\%$ higher conversion than above-the-break in JBBL). Created via drive-and-kick. |
| `ABOVE_THE_BREAK_3PT` | Above the Break 3PT | Top of key & wings | 0.80 – 0.90 EPPA | Standard perimeter attempt. Requires high mechanical consistency. |

---

## 3. Percentile Inversion & Contextual Tier Rules

### 3.1. Non-Parametric Empirical Percentile Calculation

Percentiles are computed non-parametrically across strictly isolated season populations:

1. **Standard `HIGHER_IS_BETTER` Formula:**
   $$\text{Percentile}(x) = \frac{\sum_{i=1}^N \mathbb{I}(X_i \le x)}{N} \times 100$$

2. **Inverted `LOWER_IS_BETTER` Formula (DRTG, TOV%, Opp PPG, TOV/40):**
   $$\text{Percentile}(x) = \frac{\sum_{i=1}^N \mathbb{I}(X_i \ge x)}{N} \times 100$$
   *Example:* Team allowing 80 DRTG in a league where median is 87 receives the **95th percentile (elite defense)** rather than the 5th percentile.

### 3.2. Contextual Tier Assignment

* **Evaluative Metrics (`HIGHER_IS_BETTER` or `LOWER_IS_BETTER`):**
  - $\ge 80\text{th}$ %ile: `🟢 TOP_TIER`
  - $60 - 79\text{th}$ %ile: `🔵 ABOVE_AVERAGE`
  - $40 - 59\text{th}$ %ile: `⚪ AVERAGE`
  - $20 - 39\text{th}$ %ile: `🟡 BELOW_AVERAGE`
  - $< 20\text{th}$ %ile: `🔴 BOTTOM_TIER`

* **Context-Dependent Metrics (`Pace`, `Minutes`, `3PAr`):**
  - `Pace > 75th %ile`: `⚡ HIGH_TEMPO`
  - `Pace 25th - 75th %ile`: `⚖️ BALANCED_TEMPO`
  - `Pace < 25th %ile`: `🛡️ HALF_COURT_TEMPO`
  - `Minutes >= 80th %ile`: `⭐ CORE_ROTATION_STARTER`
  - `Minutes 40th - 79th %ile`: `🔄 ROTATIONAL_CONTRIBUTOR`
  - `Minutes < 40th %ile`: `🌱 DEVELOPMENTAL_DEPTH`

---

## 4. Visual & Color Semantics Reference

* **Rule:** Visual color signals **desirability**, NOT numerical magnitude.
* **Positive (`#16a34a` / Green):** Performance in the top quartile of desirable outcomes (e.g., ORTG $\ge 80$th %ile, DRTG $\ge 80$th %ile, TS% $\ge 80$th %ile).
* **Negative (`#dc2626` / Red):** Performance in the bottom quartile of desirable outcomes (e.g., ORTG $< 25$th %ile, DRTG $< 25$th %ile, TOV% $< 25$th %ile).
* **Neutral (`#64748b` / Slate):** Stylistic, role-based, or average performance (e.g., Pace, Minutes, 50th percentile benchmarks).
