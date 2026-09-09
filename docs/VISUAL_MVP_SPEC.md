# Visual MVP Specification: Coach & Prospect Intelligence Interface
## Rheinland Falcons Basketball — JBBL / NBBL Longitudinal Intelligence Platform

---

## 1. Executive Objective

> **"If Miguel wants to show Ferran something impressive, rigorous, and immediately actionable tomorrow using ONLY the existing repository, what should he show?"**

### Target Deliverable
An interactive, high-ergonomics **Streamlit + Plotly Coach Intelligence Interface** dedicated to the Rheinland Falcons youth program, featuring deep individual prospect evaluation, tactical spatial shot maps, matchday momentum trackers, and JBBL league benchmark radars.

---

## 2. Core UI Layout & Visual Navigation Structure

```text
========================================================================================
 🏀 RHEINLAND FALCONS BASKETBALL — PROSPECT & COACH INTELLIGENCE PLATFORM v2
========================================================================================
 [Sidebar: Season Selector (SEA_2025) | Population Filter (Official vs All) | Freshness]
────────────────────────────────────────────────────────────────────────────────────────
 📑 VIEW 1: PROSPECT SCOUTING & DEVELOPMENT DOSSIER (The Core Deliverable for Ferran)
 📑 VIEW 2: HEAD-TO-HEAD PLAYER COMPARISON LAB
 📑 VIEW 3: TACTICAL COURT & SPATIAL SHOT LAB (5,138 Court Shots)
 📑 VIEW 4: GAME FLOW & MOMENTUM TRACKER (17,634 PBP Events)
 📑 VIEW 5: JBBL LEAGUE BENCHMARK EXPLORER & METHODOLOGY EVIDENCE
========================================================================================
```

---

## 3. Detailed Specifications for the Five Views

### VIEW 1: Prospect Scouting & Development Dossier (The "Ferran Special")
- **Header Card**:
  - Player Dropdown: Pre-loaded with **Maximilian Becker** (Center, 202 cm, age 14), **Lukas Weber** (Guard, 175 cm, age 14), **Henry Keller** (Guard), **Levi Richter** (Wing).
  - Profile Bio Pill: Age (exact from birth date), Height, Primary Rotation Role, Games, Minutes.
- **Visual 1: 6-Axis JBBL Percentile Radar**:
  - Interactive Plotly spider chart plotting player's percentile rank against qualified JBBL players in:
    1. *Scoring Volume* (`pts_per_40`)
    2. *Shooting Efficiency* (`ts_pct`)
    3. *Rebounding Power* (`reb_per_40`)
    4. *Playmaking Creation* (`ast_per_40`)
    5. *Ball Security* (`ast_to_tov`)
    6. *Defensive Disruption* (`stl_per_40` + `blk_per_40`)
- **Visual 2: 4-Game Rolling Trajectory & Baseline Comparison**:
  - Interactive line chart showing the player's 4-game rolling PPG and True Shooting % over time vs their season mean baseline.
  - Callouts for `POSITIVE_TREND` / `STABLE` with explicit `SHORT_SAMPLE_DEMONSTRATION` badges.
- **Visual 3: Personal 2D Court Shot Map**:
  - Interactive court scatter plot ($[1, 279] 	imes [5, 198]$) displaying green circles (makes) and red X's (misses).
  - Tooltip: Shot distance in meters, period, clock, score differential, and assist source.
- **Expandable Evidence Drawer**:
  - Full game-by-game chronological log with dates, opponents, minutes, and shooting splits.

---

### VIEW 2: Head-to-Head Player Comparison Lab
- **Dual Selector**: Compare any two players (e.g. *Lukas Weber vs Henry Keller* or *Maximilian Becker vs Chris Fokam*).
- **Overlaid Percentile Radar**: Two-color transparent radar polygon overlay.
- **Rate-Normalized Comparison Table**: Side-by-side Per-40 statistics eliminating minutes-played distortion.
- **Shot Diet Differential**: 3P attempt rate vs Rim attempt rate comparison.

---

### VIEW 3: Tactical Court & Spatial Shot Lab
- **Game / Season Filter**: Select FALCONS entire season (5,138 shots) or inspect a specific opponent match.
- **Visual 1: Interactive Court Scatter Plot**: Filterable by 2PT vs 3PT, Makes vs Misses, and Assisted vs Unassisted.
- **Visual 2: Court Zone Frequency & Conversion Matrix**:
  - Restricted Area ($\le 1.5$m)
  - Paint (non-RA)
  - Mid-Range
  - Left/Right Corner 3
  - Above-the-Break 3
- **Table**: Attempts, Makes, FG%, Frequency Share%, and Expected Points per Attempt.

---

### VIEW 4: Matchday Game Flow & Lead Tracker
- **Match Selector**: Choose any of the 36 full PBP games (e.g. *vs Bavaria Hawks*, *vs Neckar academy Ulm*).
- **Visual 1: Continuous Score Margin Tracker**: Line chart from 0:00 to 40:00 tracking FALCONS's lead/deficit.
- **Visual 2: Scoring Run Highlighter**: Automatic shaded callouts for scoring runs $\ge 8	ext{-}0$.
- **Event Breakdown Timeline**: Filterable event table (turnovers, fouls, made shots, substitutions).

---

### VIEW 5: JBBL League Benchmark Explorer & Methodology
- **Interactive Distribution Curves**: ECDF and Histogram distributions across all JBBL qualified players.
- **Scatter Plot: Usage vs Efficiency**: PTS/40 vs TS% with FALCONS players highlighted in gold.
- **Methodology & Formula Explainer**: Dynamic drawer showing exact formulas and denominators for every metric.

---

## 4. UI/UX & Cognitive Ergonomics Guidelines

1. **The 10-Second Test**: The primary message of every card must be clear within 10 seconds.
2. **Visual Honesty**: Zero truncated y-axes; radars always scaled 0 to 100.
3. **No Wall of Text**: Use metric pills, colored badges, and collapsible evidence drawers.
4. **Epistemic Color Coding**:
   - 🟢 `DESCRIPTIVE`: Solid green / blue.
   - 🟡 `EMERGING SIGNAL`: Amber badge.
   - 🔴 `CAUTION / N < 4`: Red alert badge.
