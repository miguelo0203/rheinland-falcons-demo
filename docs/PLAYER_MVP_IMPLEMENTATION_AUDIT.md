# Pre-Implementation Audit: Coach-Facing Player Intelligence MVP
## Rheinland Falcons Basketball — JBBL / NBBL Longitudinal Intelligence Platform

---

## 1. Existing Functionality in Repository

1. **Database & Data Store**:
   - `database/jbbl_sandbox.duckdb` (19 tables) contains:
     - `player` (767 rows) with `canonical_name`, `birth_date`, `height_cm`, `nationality`.
     - `boxscore_player` (1,455 rows) with traditional counting stats (PTS, REB, AST, STL, BLK, TOV, PF, FGM, FGA, FG3M, FG3A, FTM, FTA).
     - `shot` (5,138 rows, 5,024 with 2D court coordinates in $[1, 279] 	imes [5, 198]$, made/missed, period, clock, assisted by).
     - `pbp_event` (17,634 rows with clock, period, team, player, scores).
   - 27 derived Parquet files in `data/derived/` including:
     - `player_intelligence.parquet` (473 player profiles with role proxies, season totals, per-40 rates, and trend tags).
     - `player_evolution.parquet` (1,345 player-game rows with rolling 4-game metrics and delta vs baseline).
     - `shot_intelligence.parquet` (5,138 shots with zone classification).
     - `falcons_vs_league_context.parquet` (league percentile distributions).

2. **Data Access Layer (`app/services/data_service.py`)**:
   - Manages DuckDB connection, dynamic season discovery, population filtering (`OFFICIAL_ONLY` vs `ALL_GAMES`), Parquet dataframe loaders, and data freshness metadata.

3. **Streamlit Base Application (`app/main.py`)**:
   - Fully functioning multi-view application (wide layout, sidebar with dynamic season and population mode selector, data freshness card).

---

## 2. Reusable Functionality

- **DuckDB Manager & Query Engine**: Direct SQL aggregations for boxscores, shots, game logs, and biometrics.
- **Population Filtering (`python/analytics/population_filter.py`)**: Ensures official match isolation when requested.
- **Dynamic Season Discovery**: Automatically lists seasons (`SEA_2025`, etc.) from data.
- **Mathematical Formulations**: Existing TS%, eFG%, per-40 rates, and rolling 4-game linear slopes.

---

## 3. Missing Functionality (To Implement in MVP)

1. **Comprehensive Backend Player Dossier API (`DataService`)**:
   - Method to fetch a complete single-player dossier in one unified structure:
     - Biometrics (derived exact chronological age on matchday, height in cm, nationality).
     - Exposure & workload (% of available team regulation minutes, starts, MPG).
     - Volume & efficiency paired metrics (PTS/40, TS%, eFG%, 3PAr, FTr, AST/TOV).
     - Qualified JBBL benchmark percentiles (Min >= 100, 47 players) across 6 core axes.
     - Metric stability tier assignments (ESTABLISHED_SIGNAL, EMERGING_SIGNAL, DESCRIPTIVE_ONLY).
     - Dynamic natural-language contextual interpretation (Observation -> Context -> Volume -> Interpretation -> Sample Warning -> Video Hypothesis).
   - Method to retrieve player-filtered 2D court shots with coordinate boundaries, distance in meters, period, clock, and assist attribution.
   - Method to calculate tactical zone frequency and conversion with expected points per attempt.
   - Method to retrieve chronological game logs with rolling 4-game moving averages.

2. **Interactive Plotly Visual Components**:
   - `app/components/court_plot.py`: 2D FIBA half-court renderer with interactive scatter points (makes as green circles, misses as red Xs, tooltips with shot distance and game context).
   - `app/components/radar_plot.py`: 6-Axis JBBL Percentile Spider/Radar Chart with benchmark reference at 50th percentile.
   - `app/components/trajectory_plot.py`: Dual-axis or multi-line Plotly trajectory curves (Rolling 4-game PPG & TS% vs Season Baseline).

3. **Coach-Facing Player Scouting Dossier UI in `app/main.py`**:
   - Transform the primary view into an interactive, high-ergonomics Player Scouting Dossier:
     - Section A: Player Header & Bio Pills (Age, Height, Role, GP, MPG).
     - Section B: "What Should I Know About This Player?" (3–5 dynamic evidence-backed findings).
     - Section C: KPI Summary Cards with league percentile badges and sample stability tags.
     - Section D: 6-Axis JBBL Percentile Radar.
     - Section E: Interactive 2D Half-Court Shot Map with interactive filters (2P/3P, make/miss, game).
     - Section F: Tactical Shot Zone Table (Attempts, makes, FG%, frequency%, expected points/shot).
     - Section G: Recent Performance Trajectory vs Season Baseline.
     - Section H: Chronological Match Log Table.
     - Section I: Questions for Film Review.

4. **Testing Suite & Documentation**:
   - `tests/test_player_intelligence_mvp.py` (covering edge cases, small samples, missing biometrics, zero TOV, percentile bounds).
   - `docs/DEPLOYMENT_OPTIONS.md` (simple, cost-effective hosting options for Ferran).
   - `docs/PLAYER_MVP_FINAL_REPORT.md` (completion report).

---

## 4. Implementation Plan

- **Step 1**: Implement Plotly visualization components in `app/components/` (`court_plot.py`, `radar_plot.py`, `trajectory_plot.py`).
- **Step 2**: Enhance `app/services/data_service.py` with the complete Player Dossier, Shot Chart, and Dynamic Interpretation Engine.
- **Step 3**: Integrate the premier Player Dossier view into `app/main.py`.
- **Step 4**: Create `docs/DEPLOYMENT_OPTIONS.md`.
- **Step 5**: Write and execute comprehensive test suite in `tests/test_player_intelligence_mvp.py`.
- **Step 6**: Execute full repository regression suite (`pytest tests/`).
- **Step 7**: Verify production workspace isolation (`F:\Rheinland Falcons`).
- **Step 8**: Produce final validation report in `docs/PLAYER_MVP_FINAL_REPORT.md`.
