# Current Analytical Capabilities Inventory
## Rheinland Falcons Basketball — JBBL / NBBL Longitudinal Intelligence Platform

---

## 1. Summary of Validated Capabilities

The analytical engine currently operates directly on validated DuckDB tables (`jbbl_sandbox.duckdb`) and 27 derived Parquet datasets (`data/derived/`).

### Empirical Data Scope
- **65 Total Matches**: 41 Rheinland Falcons Basketball games + 24 JBBL League Universe games.
- **36 Tier 1 Spatial PBP Matches**: Complete Play-by-Play event streams (17,634 events) and spatial shot charts (5,138 shots with 2D coordinates).
- **767 Unique Players**: 473 players with boxscores, including 25 longitudinal FALCONS profiles.

---

## 2. Capability Matrix Across Analytical Domains

| Analytical Domain | Specific Capability | Implementation Status | Storage / Module | Sample Requirement |
| :--- | :--- | :--- | :--- | :--- |
| **Team Efficiency** | Four Factors (eFG%, TOV%, ORB%, FTr) | **100% OPERATIONAL** | `team_intelligence.parquet` | $\ge 1$ Game |
| **Team Ratings** | Offensive, Defensive, and Net Rating | **100% OPERATIONAL** | `team_season_analysis.parquet` | $\ge 1$ Game |
| **Player Production** | Traditional Boxscore Totals & Per-Game | **100% OPERATIONAL** | `boxscore_player` (DuckDB) | $\ge 1$ Game |
| **Player Normalization**| Per-40 Minute Rate Stats (PTS/40, REB/40, AST/40) | **100% OPERATIONAL** | `player_intelligence.parquet` | $\ge 10$ Minutes |
| **Player Efficiency** | True Shooting % (TS%) & Effective FG% (eFG%) | **100% OPERATIONAL** | `player_intelligence.parquet` | $\ge 10$ FGA |
| **Shooting Diet** | 3P Attempt Rate (3PAr) & Free Throw Rate (FTr) | **100% OPERATIONAL** | `player_intelligence.parquet` | $\ge 10$ FGA |
| **Spatial Court Maps**| 2D Court Scatter & Hexbin Density ($[1, 279]	imes [5, 198]$)| **100% OPERATIONAL** | `shot` (DuckDB) / Plotly | $\ge 1$ Shot |
| **Zone Breakdown** | Restricted Area, Paint, Mid-Range, 3PT Zones | **100% OPERATIONAL** | `shot_intelligence.parquet` | $\ge 1$ Shot |
| **Shot Creation** | Assisted vs Unassisted Field Goals | **100% OPERATIONAL** | `shot_analysis.parquet` | $\ge 1$ Made FG |
| **Player Trends** | Rolling 4-Game Moving Averages & Deltas | **100% OPERATIONAL** | `player_evolution.parquet` | $\ge 4$ Games |
| **Weekly Monitoring** | Calendar Week Aggregations & WoW Deltas | **100% OPERATIONAL** | `player_weekly_analysis.parquet`| $\ge 1$ Week |
| **League Benchmarking**| Percentile Ranks vs 47 Qualified JBBL Players | **100% OPERATIONAL** | `falcons_vs_league_context.parquet`| $\ge 100$ Minutes |
| **Game Flow & Runs** | PBP Lead Trackers & $\ge 8	ext{-}0$ Scoring Runs | **100% OPERATIONAL** | `pbp_event` (DuckDB) / Plotly | PBP match |
| **Coach Findings** | Automated Evidence-Supported Insight Generation | **100% OPERATIONAL** | `coach_intelligence_findings.parquet`| Season data |
| **Video Hypotheses** | Structured Prompts for Film Review | **100% OPERATIONAL** | `coach_hypotheses.parquet` | Season data |

---

## 3. Real Player Profiles from the Database

### Profile 1: Maximilian Becker (Center, 202 cm, Age 14)
- **Exposure**: 21 Games Played, 426.1 Total Minutes (20.3 MPG).
- **Physical Demographics**: Born `2010-09-21` (age 14 in 2024/25 U16 season), 202.0 cm standing height.
- **Production**: 12.1 PPG, 10.5 RPG, 0.7 APG, 1.5 BLK/40, 2.3 STL/40.
- **Normalized Rates**: **23.8 PTS/40** (91st percentile), **20.7 REB/40** (99th percentile — League Best!).
- **Efficiency**: **60.1% FG** (113/188), **59.97% True Shooting %** (88th percentile).
- **Shot Diet**: 97.3% 2PT attempts (183 2PA, 112 2PM), 2.7% 3PT attempts (1/5). Over 85% of attempts in restricted area/paint.

### Profile 2: Lukas Weber (Guard/Wing, 175 cm, Age 14)
- **Exposure**: 19 Games Played, 474.9 Total Minutes (25.0 MPG).
- **Physical Demographics**: Born `2010-04-07`, 175.0 cm standing height.
- **Production**: **15.6 PPG**, 5.2 RPG, 3.0 APG, 3.0 STL/40.
- **Normalized Rates**: **25.0 PTS/40** (94th percentile), **4.8 AST/40** (81st percentile).
- **Efficiency**: **56.1% FG** (110/196), **48.9% 3P** (23/47 — 94th percentile!), **64.0% True Shooting %** (96th percentile).
- **Shot Diet**: Balanced perimeter-interior split: 76.0% 2PA (87/149 2P = 58.4%), 24.0% 3PA (23/47 3P = 48.9%).

### Profile 3: Jonas Keller (Guard)
- **Exposure**: 19 Games Played, 523.1 Total Minutes (27.5 MPG — Team Leader).
- **Production**: **12.4 PPG**, 1.8 RPG, **3.1 APG** (Team Leader), 1.8 STL/40.
- **Normalized Rates**: 18.0 PTS/40 (64th percentile), **4.5 AST/40** (77th percentile).
- **Efficiency**: 39.4% FG (80/203), 25.2% 3P (27/107), 49.2% TS% (57th percentile).
- **Role**: Primary ball-handler, high-volume perimeter initiator (107 3PA = 52.7% 3PAr).

---

## 4. Boundaries of Current Evidence (What NOT to Show)

1. **Do NOT show permanent 4-game talent ratings**: A 4-game streak is explicitly marked as `SHORT_SAMPLE_DEMONSTRATION`.
2. **Do NOT show 5-man lineup net ratings**: Current PBP lacks complete starting 5 lineup declarations in certain matches, creating 4-player stint artifacts.
3. **Do NOT show synthetic prospect potential scores**: Maintain empirical percentile radars rather than unverified 0–100 pseudo-ratings.
