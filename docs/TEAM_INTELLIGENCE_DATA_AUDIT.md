# Rheinland Falcons Basketball — Team Intelligence V1 Data Capability Audit

**Version:** 1.0  
**Date:** 2026-09-02  
**Target Active Development:** `F:\Rheinland Falcons Prueba`  
**Protected Production Snapshot:** `F:\Rheinland Falcons\BACKUP_DEPLOYED_MVP_2026-09-02` (**100% UNTOUCHED & FROZEN**)  
**Analytical Scope:** Team Intelligence, Play-by-Play Substitution Streams, Lineup Stints, and Quintet Complementarity Modeling  

---

## 1. Executive Summary

Before implementing Team Intelligence V1, an exhaustive forensic data audit was conducted on the underlying DuckDB database (`database/jbbl_sandbox.duckdb`) and normalized parquet datasets (`data/normalized/`).

The audit revealed that the Rheinland Falcons dataset is a **hybrid analytical environment**:
* **Season 2024/25 (`SEA_2025`):** Contains **24 total games** for Rheinland Falcons Basketball.
  - **14 games (58.3%)** have complete Play-by-Play (`pbp_event`) feeds including quarter-by-quarter starting fives (`lineup_stint`) and explicit substitution events (`SUB`). These 14 games permit exact, deterministic reconstruction of simultaneous 5-man on-court stints (**Mode A: Observed Lineup Intelligence**).
  - **10 games (41.7%)** are Boxscore-only or Score-only without event-level PBP timestamps.
* **Season 2023/24 (`SEA_2023`):** Contains **17 games**, all boxscore/score records without granular event-level PBP streams.

### Core Architectural Principle:
The platform must strictly distinguish:
* **OBSERVED LINEUP INTELLIGENCE (Mode A):** Applied when PBP substitution streams exist. Calculates actual on-court minutes, possessions, Net Rating, and Four Factors for simultaneous five-man units.
* **PROFILE-BASED QUINTET INTELLIGENCE (Mode B):** Applied when PBP is unavailable or when building hypothetical player combinations. Evaluates statistical complementarity, role balance, and spacing across the selected players without fabricating on-court minutes or Net Rating.

---

## 2. Comprehensive Data Capability Matrix

| Capability Dimension | Available | Coverage in SEA_2025 | Coverage in SEA_2023 | Reliability Level | Derivable Analytics & Bounds |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Game Outcomes & Final Scores** | ✅ YES | 24 / 24 Games (100%) | 17 / 17 Games (100%) | **EXACT (Official)** | Win/Loss, Point Differential, Game Phase, Opponent context. |
| **Team Boxscore & Ratings** | ✅ YES | 24 / 24 Games (100%) | 17 / 17 Games (100%) | **EXACT** | Possessions, ORTG, DRTG, NetRtg, Four Factors (eFG%, TOV%, ORB%, FTR), Pace. |
| **Player Boxscore Production** | ✅ YES | 24 / 24 Games (100%) | 17 / 17 Games (100%) | **EXACT** | Minutes, PTS, FGA, FG%, 3PA, 3P%, FTA, FT%, TRB, ORB, DRB, AST, STL, BLK, TOV, PF. |
| **Spatial Shot Coordinates** | ✅ YES | 24 / 24 Games (100%) | 0 / 17 Games (0%) | **HIGH (99.7% with (X,Y))** | 2D Court Maps, Tactical Zone Conversion, Shot Diet Shares, Expected Points Per Attempt. |
| **Quarter Starting 5s** | ✅ YES | 14 / 24 Games (58.3%) | 0 / 17 Games (0%) | **EXACT (Socket Stream)** | Starting lineups for Q1, Q2, Q3, Q4. |
| **Play-by-Play Event Stream** | ✅ YES | 14 / 24 Games (58.3%) | 0 / 17 Games (0%) | **EXACT (17,634 events)** | Clock display, game seconds remaining, points scored, fouls, turnovers, free throws. |
| **Substitution Events (SUB)** | ✅ YES | 14 / 24 Games (58.3%) | 0 / 17 Games (0%) | **EXACT (2,258 sub events)** | Player exiting (`player_id`) and player entering (`secondary_player_id`). |
| **5-Man On-Court Lineup Stints** | ✅ YES (Reconstructible) | 14 / 24 Games (58.3%) | 0 / 17 Games (0%) | **EXACT (358 stints, 516.1m)** | Exact simultaneous on-court duration, points for/against, possessions, lineup Net Rating. |
| **2-Man Pair & 3-Man Trio Overlap** | ✅ YES (Reconstructible) | 14 / 24 Games (58.3%) | 0 / 17 Games (0%) | **EXACT** | Real simultaneous overlap minutes, on-court plus/minus, pair/trio Net Rating. |
| **Video Tracking / Sync Clips** | ❌ NO | 0 / 24 Games (0%) | 0 / 17 Games (0%) | **NOT_AVAILABLE** | Video clips are not ingested; video hypotheses serve as coach film-review questions. |

---

## 3. Forensic Details on Missing Capabilities & Methodological Safeguards

### 3.1. What CANNOT Be Claimed Without PBP:
1. **Never Claim Simultaneous Minutes:** In games without PBP (or for player combinations that never shared the floor), the platform must **never display a minutes figure** implying they played together.
2. **Never Fabricate Net Rating:** Net Rating requires exact points scored and points conceded while five specific players were on the floor. In Mode B, Net Rating is withheld and replaced with the **Quintet Fit Index (0–100)** and individual dimension profiles.
3. **Never Claim "Observed Synergy":** Profile-based analysis evaluates structural traits (e.g. spacing, playmaking volume, rim protection), which must always be framed as statistical potential and tactical fit.

### 3.2. What CAN Be Derived With High Statistical Integrity:
1. **In Mode A (Observed Lineup Intelligence):**
   - 358 distinct on-court stints across 14 official matches.
   - Core starting lineup (`Lukas Weber + Jonas Keller + Levi Richter + Julian Wagner + Maximilian Becker`) has **70.6 minutes** of verified simultaneous play with $+46$ score differential and Net Rating of $+25.7$.
   - Sample confidence tiers strictly communicate sample reliability ($\ge 30$ min = Strong Evidence, $15-29$ min = Moderate, $5-14$ min = Emerging, $<5$ min = Insufficient Sample).
2. **In Mode B (Profile-Based Quintet Intelligence):**
   - Aggregate shooting volume and conversion (Combined TS%, 3P Attempt Rate).
   - Playmaking distribution (AST/40, Assist-to-Turnover ratio).
   - Rebounding balance (Offensive & Defensive glass control).
   - Ball security and turnover risk profile.
   - Positional and role balance (Creators, Spacers, Finishers, Anchors).
   - Progressive 1 $
ightarrow$ 5 player addition tracking with exact change-by-addition delta analysis.

---

## 4. Lineup Evidence Hierarchy & Confidence Thresholds

To prevent over-interpreting small sample noise (e.g. a lineup with 2 minutes having an artificial $+80$ Net Rating), the following evidence hierarchy is enforced:

| Evidence Tier | Minimum Observed Minutes | Minimum Possessions | Coaching Interpretation Standard | Visual Badge |
| :--- | :--- | :--- | :--- | :--- |
| **`STRONG_EVIDENCE`** | $\ge 30.0	ext{ min}$ | $\ge 60	ext{ poss}$ | High reliability. Representative of recurring tactical unit performance. | `🟢 STRONG EVIDENCE` |
| **`MODERATE_EVIDENCE`** | $15.0 - 29.9	ext{ min}$ | $30 - 59	ext{ poss}$ | Meaningful rotation sample. Usable for tactical planning with caution. | `🔵 MODERATE EVIDENCE` |
| **`EMERGING_SIGNAL`** | $5.0 - 14.9	ext{ min}$ | $10 - 29	ext{ poss}$ | Small rotational sample. Watch pattern; verify on game film. | `🟡 EMERGING SIGNAL` |
| **`INSUFFICIENT_SAMPLE`** | $< 5.0	ext{ min}$ | $< 10	ext{ poss}$ | Extreme volatility. Metrics displayed with explicit disclaimer; no definitive claims. | `⚪ INSUFFICIENT SAMPLE` |

---

## 5. Conclusion & Technical Roadmap

This audit validates that the database has the required event data to power both **Mode A (Observed Lineup Reconstruction)** and **Mode B (Profile-Based Quintet Builder)**. Team Intelligence V1 will seamlessly support both modes within a unified, interactive coaching interface.
