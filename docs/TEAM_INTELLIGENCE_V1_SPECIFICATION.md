# Rheinland Falcons Basketball — Team Intelligence V1 Technical Specification

**Version:** 1.0  
**Date:** 2026-09-02  
**Target Development Workspace:** `F:\Rheinland Falcons Prueba`  
**Protected Snapshot:** `F:\Rheinland Falcons\BACKUP_DEPLOYED_MVP_2026-09-02` (**100% UNTOUCHED & FROZEN**)  

---

## 1. System Architecture Overview

Team Intelligence V1 elevates the Rheinland Falcons Basketball Intelligence platform from an individual player scouting tool into a comprehensive **team-level tactical decision support system**.

The platform is architected around a dual analytical engine:

```text
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                               TEAM INTELLIGENCE V1 ENGINE                              │
├───────────────────────────────────────────┬────────────────────────────────────────────┤
│   MODE A: OBSERVED LINEUP INTELLIGENCE    │  MODE B: PROFILE-BASED QUINTET BUILDER     │
│   (When PBP & Substitution Feeds Exist)   │  (When PBP Is Absent or Hypothetical Unit) │
├───────────────────────────────────────────┼────────────────────────────────────────────┤
│ • Exact simultaneous on-court stints      │ • Progressive 1 -> 5 Player Builder UX     │
│ • True 5-man possession tracking          │ • 6-Dimensional Structural Fit Index       │
│ • Observed Points For & Allowed           │ • Dynamic Change-by-Addition Tracker       │
│ • Net Rating & Dean Oliver Four Factors   │ • Spacing, Creation, Rebounding, Security  │
│ • Sample Confidence Tiers (30m/15m/5m/<5m)│ • Strict Evidence Banner (No False NetRtg) │
└───────────────────────────────────────────┴────────────────────────────────────────────┘
```

---

## 2. Data Capabilities & Modality Bounds

* **Verified PBP Games (14 Matches in Season 2024/25):** Contain 17,634 event timestamps, quarter starting fives (`stream['starting_five']`), and 2,258 substitution events (`SUB`). These enable exact reconstruction of 358 distinct on-court stints and 516.1 regulation minutes.
* **Boxscore-Only Games (10 Matches in 2024/25, 17 Matches in 2023/24):** Supported exclusively through **Mode B (Profile-Based Quintet Intelligence)**.
* **Methodological Boundary:** Under no circumstances does the system fabricate simultaneous on-court minutes, possessions, or Net Rating when PBP event streams are absent.

---

## 3. Mode A: Observed Lineup Intelligence Methodology

### 3.1. Stint Reconstruction Algorithm:
1. **Initial State:** Quarter starting five is initialized from `lineup_stint` (`period = 1..4`).
2. **Event Parsing:** PBP events are processed chronologically. Point events increment stint points scored or conceded.
3. **Substitution Transition:** When a `SUB` event occurs on the team:
   - Current stint is closed: $	ext{Duration} = 	ext{Stint Start Seconds} - 	ext{Game Seconds Remaining}$.
   - Stint stats are recorded ($FGA, FGM, 3PA, 3PM, FTA, TOV, ORB, PTS_{for}, PTS_{against}$).
   - Roster state transition: Exiting player is removed; entering player is added.
   - New stint clock starts.

### 3.2. Advanced Lineup Metrics:
* **Possessions:** $	ext{Poss} = FGA + 0.44 	imes FTA - ORB + TOV$
* **Offensive Rating (ORTG):** $	ext{ORTG} = rac{PTS_{for}}{	ext{Poss}} 	imes 100$
* **Defensive Rating (DRTG):** $	ext{DRTG} = rac{PTS_{against}}{	ext{Poss}} 	imes 100$
* **Net Rating (NetRtg):** $	ext{NetRtg} = 	ext{ORTG} - 	ext{DRTG}$
* **Effective Field Goal % (eFG%):** $	ext{eFG\%} = rac{FGM + 0.5 	imes 3PM}{FGA} 	imes 100$
* **Turnover Rate (TOV%):** $	ext{TOV\%} = rac{TOV}{FGA + 0.44 	imes FTA + TOV} 	imes 100$
* **Free Throw Rate (FTr):** $	ext{FTr} = rac{FTA}{FGA}$

---

## 4. Mode B: Progressive Quintet Complementarity Engine

When evaluating any combination of 1 to 5 players without observed PBP overlap:

### 4.1. 6-Dimensional Structural Evaluation:
1. **Shooting & Spacing ($0-100$):** Weighted True Shooting % ($50\%$), 3PA Attempt Rate ($30\%$), and 3PT Conversion ($20\%$).
2. **Creation & Playmaking ($0-100$):** AST/40 volume ($50\%$), AST/TO ratio ($30\%$), and secondary playmaking depth ($20\%$).
3. **Rebounding & Glass Control ($0-100$):** Total REB/40 volume ($50\%$), offensive putback rate ($30\%$), and interior anchor presence ($20\%$).
4. **Ball Security & Turnover Control ($0-100$):** Inverted TOV/40 volume ($50\%$) and AST/TO ball protection ($50\%$).
5. **Defensive Event Disruption ($0-100$):** Steals and blocks per 40 min ($60\%$) and defensive rebounding ($40\%$).
6. **Role & Positional Balance ($0-100$):** Structural diversity covering primary creators, perimeter spacers, physical anchors, and primary scorers.

### 4.2. Decomposable Quintet Fit Index:
$$	ext{Fit Index} = 0.22 	imes 	ext{Shooting} + 0.18 	imes 	ext{Creation} + 0.18 	imes 	ext{Rebound} + 0.15 	imes 	ext{Security} + 0.15 	imes 	ext{Defense} + 0.12 	imes 	ext{Role}$$

---

## 5. Progressive Analysis & Change-by-Addition Tracking

When a coach selects player $N$ into an existing group of $N-1$ players:
* The engine evaluates both the state before ($	ext{State}_{N-1}$) and after ($	ext{State}_N$).
* Computes exact dimension deltas: $\Delta 	ext{Fit}$, $\Delta 	ext{Shooting}$, $\Delta 	ext{Creation}$, $\Delta 	ext{Rebounding}$, $\Delta 	ext{Defense}$, $\Delta 	ext{Security}$, $\Delta 	ext{Role}$.
* Generates an automated, tactical takeaway (e.g., *"Adding **Lukas Weber** elevates perimeter spacing, amplifies shot creation."*).

---

## 6. Sample-Size & Evidence Confidence Tiers

| Evidence Tier | Minimum Observed Minutes | Minimum Possessions | Visual Representation |
| :--- | :--- | :--- | :--- |
| **`STRONG_EVIDENCE`** | $\ge 30.0	ext{ min}$ | $\ge 60	ext{ poss}$ | `🟢 STRONG EVIDENCE` |
| **`MODERATE_EVIDENCE`** | $15.0 - 29.9	ext{ min}$ | $30 - 59	ext{ poss}$ | `🔵 MODERATE EVIDENCE` |
| **`EMERGING_SIGNAL`** | $5.0 - 14.9	ext{ min}$ | $10 - 29	ext{ poss}$ | `🟡 EMERGING SIGNAL` |
| **`INSUFFICIENT_SAMPLE`** | $< 5.0	ext{ min}$ | $< 10	ext{ poss}$ | `⚪ INSUFFICIENT SAMPLE` |

---

## 7. Pair & Trio On-Court Chemistry

* **2-Man Pairs (75 Observed Combinations):**
  - Top pair: `Julian Wagner + Lukas Weber` (262.1 minutes, Net Rating $+23.1$, `STRONG_EVIDENCE`).
  - `Maximilian Becker + Julian Wagner` (241.3 minutes, Net Rating $+24.3$, `STRONG_EVIDENCE`).
* **3-Man Trios (219 Observed Combinations):**
  - Top trio: `Maximilian Becker + Julian Wagner + Lukas Weber` (185.4 minutes, Net Rating $+26.8$, `STRONG_EVIDENCE`).

---

## 8. UI Architecture in Hub 2

1. **`Tab 1: 📊 Executive Overview & Team Profile`:** Offensive/Defensive profile, Four Factors, Strengths, Areas to Monitor, Video Hypotheses.
2. **`Tab 2: 🏀 Interactive Quintet Builder (Hero Feature)`:** Progressive 1 $
ightarrow$ 5 builder, presets (Starting 5, Spacing, Glass), Mode A/B Evidence Banner, Fit Index gauge, 6-dimension bars, Change-by-Addition card, Strengths, Risks, and Coach Film Questions.
3. **`Tab 3: 📋 Observed 5-Man Lineup Registry`:** Searchable table of all 137 observed lineups with minute slider filter.
4. **`Tab 4: 👥 Pair & Trio Chemistry`:** 2-man and 3-man overlap tables with confidence tiers.
5. **`Tab 5: 📈 Four Factors Evolution & Benchmarks`:** Chronological game ratings, Team Profile against JBBL league percentiles, and Four Factors $R^2$ regression table.

---

## 9. Verification & Quality Assurance

* **Automated Tests:** 55/55 tests passing in `tests/test_team_intelligence_v1.py` and `tests/test_navigation_5hubs.py`.
* **Zero Production Touches:** `F:\Rheinland Falcons` remains 100% frozen.
