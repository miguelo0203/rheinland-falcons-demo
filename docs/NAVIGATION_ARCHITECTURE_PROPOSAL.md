# Rheinland Falcons Basketball — Navigation Architecture & Information Hierarchy Proposal

**Version:** 1.0 (Architecture Proposal & Migration Roadmap)  
**Date:** 2026-09-02  
**Target:** `F:\Rheinland Falcons Prueba`  
**Status:** PROPOSAL READY FOR REVIEW (No destructive navigation changes applied during audit)  

---

## 1. Current Navigation Audit & Redundancy Analysis

The current application contains **10 top-level navigation views** in the sidebar. An exhaustive inventory of these views was conducted:

| Current View | Primary Purpose | Unique Information | Duplicated / Overlapping Information | Related Views | Assessment |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **1. Player Intelligence (Coach Dossier)** | Complete player scouting dossier & evaluation | Biometrics, rate KPIs, dynamic evidence cards, 6-axis radar, 2D shot map, tactical zone table, 4-game trajectory, game log, film hypotheses | Player stats appear in Views 3, 6, 7, 8 | Views 4, 6, 7 | **CORE HERO VIEW** (Keep & enrich) |
| **2. Coach Overview** | Executive summary of team strengths & weaknesses | Quick Four Factor metric cards, Top strengths & Areas requiring monitoring | Repeats findings from View 8 and Four Factors from View 5 | Views 5, 8 | **FRAGMENTED** (Natural tab in Team Intelligence) |
| **3. Game Lab & Match Deep Dive** | Match-by-match analysis & boxscores | Match selector, Modality Availability Matrix, full team player boxscore table | Game registry metadata overlaps with View 9 | Views 9, 10 | **CORE GAME VIEW** (Keep as dedicated Match Hub) |
| **4. Shot Lab & Spatial Court Analytics** | Team-wide court shot distribution | Team-level aggregated shot zone frequency & conversion table, coordinate coverage | Zone logic identical to Section F in View 1 | Views 1, 3 | **SUPPORTING** (Can live as Shot Lab tab) |
| **5. Team Performance & Four Factors** | Game-by-game Four Factors evolution | Chronological team ratings table (ORTG, DRTG, eFG%, TOV%, ORB%, FTR) | Overlaps with Coach Overview (View 2) and League Context (View 6) | Views 2, 6 | **FRAGMENTED** (Natural tab in Team Intelligence) |
| **6. League Context & Benchmarks** | Benchmark FALCONS team and players vs JBBL universe | 11 Team Benchmarks vs League Median/Percentiles, Player rankings pivot, Four Factors empirical $R^2$ table | Player percentiles duplicate View 1; Four Factors duplicate View 5 | Views 1, 5, 8 | **SUPPORTING / CONTEXT** (Natural tab in Team Intelligence) |
| **7. Weekly Player Monitoring** | Longitudinal weekly player tracking | Week-by-week aggregation table with $\Delta$ PPG WoW | Completely redundant with View 1 Player Dossier | View 1 | **REDUNDANT / FRAGMENTED** (Should be merged into View 1) |
| **8. Findings & Tactical Hypotheses** | Registry of coach intelligence findings | Tabular finding registry and video hypotheses list | Directly duplicates findings cards in View 1 and View 2 | Views 1, 2, 9 | **FRAGMENTED** (Consolidate with Evidence Explorer) |
| **9. Evidence Explorer** | Traceability from finding to raw match data | Parquet evidence link table, canonical game registry | Registry overlaps with View 3 & 10 | Views 3, 8, 10 | **TECHNICAL** (Consolidate into Methodology & Evidence) |
| **10. Data Quality & Methodology** | Multi-source modality quality matrix | Composite data quality score table across ingested matches | Modality table overlaps with View 3 | Views 3, 9 | **TECHNICAL** (Consolidate into Methodology & Evidence) |

---

## 2. The Basketball Coach Workflow Problem

A professional head coach (such as Ferran) or assistant coach approaches analytical intelligence with a clear hierarchical decision path:

```text
┌────────────────────────────────────────────────────────┐
│ 1. WHO ARE MY PLAYERS & HOW ARE THEY EVOLVING?         │  --> Player Intelligence (Dossier + Trends)
└───────────────────────────┬────────────────────────────┘
                            │
┌───────────────────────────▼────────────────────────────┐
│ 2. HOW IS THE TEAM PERFORMING AS A COLLECTIVE?         │  --> Team Intelligence (Overview + Four Factors + Benchmarks)
└───────────────────────────┬────────────────────────────┘
                            │
┌───────────────────────────▼────────────────────────────┐
│ 3. WHAT HAPPENED IN A SPECIFIC MATCH?                  │  --> Game Lab & Match Deep Dive
└───────────────────────────┬────────────────────────────┘
                            │
┌───────────────────────────▼────────────────────────────┐
│ 4. WHERE ARE WE GENERATING OUR SHOTS?                  │  --> Shot Lab & Spatial Court Analytics
└───────────────────────────┬────────────────────────────┘
                            │
┌───────────────────────────▼────────────────────────────┐
│ 5. WHAT EVIDENCE & METHODOLOGY BACKS THIS UP?          │  --> Evidence, Methodology & Film Registry
└────────────────────────────────────────────────────────┘
```

**Current Friction:** Currently, to understand the team, a coach must click View 2 (Coach Overview), then View 5 (Team Performance), then View 6 (League Context), and then View 8 (Findings). This creates unnecessary cognitive switching and disjointed context.

---

## 3. Evaluation of Three Navigation Architectures

### Option A: Minimal Architecture (3 Primary Views)
* **Structure:**
  1. `Player Intelligence` (Dossier, Zones, Trajectory, Weekly Monitoring)
  2. `Team & Game Intelligence` (Team Overview, Four Factors, Game Lab, League Benchmarks, Shot Lab)
  3. `Evidence & Methodology` (Findings, Video Hypotheses, Data Quality)
* **Pros:** Minimalist sidebar; zero menu clutter.
* **Cons:** Overloads View 2 with too many disparate sub-concepts (Game Lab mixed with Team Season Four Factors).
* **Usability Score:** 6.5/10

---

### Option B: Balanced Architecture [RECOMMENDED] (5 Cohesive Primary Hubs)
* **Structure:**
  1. `👤 1. Player Intelligence & Coach Dossier`
     - *Tabs:* `Scouting Dossier (Hero)` | `Trajectory & Longitudinal Dynamics` | `Weekly Monitoring & Game Logs`
  2. `🏆 2. Team Intelligence & Performance Overview` *(Ready for upcoming Team module)*
     - *Tabs:* `Executive Overview & Strengths` | `Game-by-Game Four Factors` | `JBBL League Benchmarks & Context`
  3. `🏟️ 3. Game Lab & Match Deep Dive`
     - *Subsections:* Match Overview, Modality Availability Matrix, Full Boxscores
  4. `🎯 4. Shot Lab & Spatial Court Analytics`
     - *Subsections:* Interactive Team Court Map, Tactical Zone Conversion & Diet Shares
  5. `💡 5. Evidence, Hypotheses & Methodology Hub`
     - *Tabs:* `Coach Findings & Video Hypotheses` | `Finding-to-Game Evidence Traceability` | `Data Quality & Provenance`
* **Pros:**
  - Mirrors natural coaching cognitive hierarchy.
  - Reduces sidebar complexity by **50%** (from 10 items down to 5).
  - Perfectly pre-configured for the future **Team Intelligence** expansion (Lineups, Chemistry, PBP will slot directly into Hub 2 without creating new sidebar clutter).
  - Preserves 100% of existing functionality with zero loss of depth.
* **Usability Score:** **9.8/10 (Coach-Optimal)**

---

### Option C: Analyst-Oriented Architecture (7 Primary Views)
* **Structure:**
  1. Player Dossier
  2. Player Longitudinal Monitoring
  3. Team Overview & Ratings
  4. Game Lab
  5. Shot Lab
  6. League Benchmarks
  7. Evidence & Data Quality
* **Pros:** Highly granular.
* **Cons:** Keeps player and team information somewhat fragmented across multiple clicks.
* **Usability Score:** 7.5/10

---

## 4. Current → Future Migration Roadmap (Option B)

| Current View | Proposed Future Location (Option B) | Transition Action |
| :--- | :--- | :--- |
| **1. Player Intelligence (Coach Dossier)** | `1. Player Intelligence & Coach Dossier` → Tab 1: *Scouting Dossier* | **Keep as Hero View** |
| **2. Coach Overview** | `2. Team Intelligence & Overview` → Tab 1: *Executive Overview* | **Consolidate into Team Hub** |
| **3. Game Lab & Match Deep Dive** | `3. Game Lab & Match Deep Dive` | **Keep as Dedicated Match Hub** |
| **4. Shot Lab & Spatial Court Analytics** | `4. Shot Lab & Spatial Court Analytics` | **Keep as Dedicated Spatial Hub** |
| **5. Team Performance & Four Factors** | `2. Team Intelligence & Overview` → Tab 2: *Game-by-Game Four Factors* | **Consolidate into Team Hub** |
| **6. League Context & Benchmarks** | `2. Team Intelligence & Overview` → Tab 3: *JBBL League Benchmarks* | **Consolidate into Team Hub** |
| **7. Weekly Player Monitoring** | `1. Player Intelligence & Coach Dossier` → Tab 2: *Weekly Monitoring & Game Logs* | **Merge into Player Hub** |
| **8. Findings & Tactical Hypotheses** | `5. Evidence & Methodology Hub` → Tab 1: *Coach Findings & Hypotheses* | **Consolidate into Evidence Hub** |
| **9. Evidence Explorer** | `5. Evidence & Methodology Hub` → Tab 2: *Evidence Traceability Matrix* | **Consolidate into Evidence Hub** |
| **10. Data Quality & Methodology** | `5. Evidence & Methodology Hub` → Tab 3: *Data Quality & Methodology* | **Consolidate into Evidence Hub** |

---

## 5. Future Scalability for the Team Intelligence Phase

When the next development phase begins (**Team Intelligence: Lineup Analysis, Pair/Trio Combinations, On/Off Stints, Play-by-Play & Game State Dynamics**), it will seamlessly integrate into **Hub 2 (Team Intelligence)** via dedicated tabs:

```text
2. TEAM INTELLIGENCE
   ├── Tab 1: Executive Overview & Ratings
   ├── Tab 2: Four Factors Evolution
   ├── Tab 3: Lineup Intelligence & 5-Man Combinations (FUTURE)
   ├── Tab 4: Pair / Trio Chemistry & On-Off Differentials (FUTURE)
   ├── Tab 5: Play-by-Play & Game State Momentum (FUTURE)
   └── Tab 6: JBBL League Benchmarks
```

This prevents the application from ballooning into 15+ unmanageable navigation items, preserving executive elegance and ergonomic clarity.
