# Rheinland Falcons Basketball Intelligence Platform — Technical Architecture (v2.0)

## System Architecture, Data Flow & Engineering Specification
**Target Audience:** Analytics Engineers, Software Developers, Data Engineers, and Infrastructure Maintainers.  
**Version:** `v2.0.0`

---

# 1. High-Level Architecture Overview

The platform uses a modern, lightweight, high-performance Python analytics stack built around **DuckDB**, **Streamlit**, and **Plotly**, operating entirely with zero external database dependencies.

```
+-------------------------------------------------------------------------+
|                      STREAMLIT PRESENTATION LAYER                       |
|  Hub 1 (Player) | Hub 2 (Team) | Hub 3 (Game) | Hub 4 (Shot) | Hub 5 (Ev) |
+-------------------------------------------------------------------------+
                                    |
+-------------------------------------------------------------------------+
|                       APPLICATION SERVICES & UI                         |
|   DataService (DuckDB Interface) | Components (Court, Radar, Trajectory)|
+-------------------------------------------------------------------------+
                                    |
+-------------------------------------------------------------------------+
|                      ANALYTICAL & STATISTICAL ENGINES                    |
|  - TeamIntelligenceEngine (5-man stints, 2/3/4 combinations)            |
|  - CourtPlotEngine (10 FIBA contiguous zones, Bayesian shrinkage)       |
|  - PlayerTrendsEngine (Rolling averages, volatility, stability)         |
|  - UniversalEvidenceEngine (Traceability, hypothesis validation, CI)    |
|  - MetricSemanticsCatalog (Metadata, units, sample-size guidelines)     |
+-------------------------------------------------------------------------+
                                    |
+-------------------------------------------------------------------------+
|                      PERSISTENT DATA FOUNDATION                         |
|   DuckDB Sandbox (database/jbbl_sandbox.duckdb) | Parquet Gold Layer    |
+-------------------------------------------------------------------------+
```

---

# 2. Directory & Module Structure

```text
├── app/
│   ├── components/
│   │   ├── court_plot.py        # 2D FIBA court maps, 10 continuous hot zones, Bayesian shrinkage
│   │   ├── radar_plot.py        # 8-dimensional percentile radar charts
│   │   ├── trajectory_plot.py   # Longitudinal trend & volatility charts
│   │   └── ui.py                # Design tokens, custom CSS, badges, KPI cards
│   ├── services/
│   │   └── data_service.py      # High-performance DuckDB query facade with TTL caching
│   ├── auth.py                  # Session authentication & security guardrails
│   └── main.py                  # 5-hub Streamlit orchestrator and responsive layout
├── data/
│   ├── derived/                 # Gold analytics parquet tables (lineups, trends, findings)
│   └── normalized/              # Silver normalized entity parquet tables (shot, pbp_event, etc.)
├── database/
│   └── jbbl_sandbox.duckdb      # Primary embedded analytics database
├── docs/
│   ├── USER_MANUAL.md           # Coach-facing operational user manual
│   ├── TECHNICAL_OVERVIEW.md    # Engineering architecture specification
│   ├── CHANGELOG.md             # Semantic version history
│   └── METRIC_SEMANTICS_CATALOG.md # Exhaustive metric definitions & stability guidelines
├── python/
│   ├── analytics/
│   │   ├── team_intelligence_engine.py  # Lineup stints, pairs, trios, quartets, Four Factors
│   │   ├── player_trends.py             # Trajectory smoothing, rolling form, volatility
│   │   ├── metric_semantics.py          # Universal metric metadata and guidelines
│   │   ├── phase4_shot_engine.py        # Spatial shot coordinate categorization
│   │   └── phase5_shot_intelligence.py  # Advanced spatial analytics
│   └── database/
│       └── duckdb_manager.py            # Thread-safe DuckDB connection manager
└── tests/
    ├── test_hub4_spatial_hotzones.py    # 100% court coverage, shoelace area, perturbation tests
    ├── test_hub4_hub5_deep.py           # Shot Lab, Evidence Hub, and Traceability tests
    ├── test_navigation_5hubs.py         # 5-hub navigation & 14-player visual journey tests
    └── run_full_visual_qa.py            # Automated visual QA runner
```

---

# 3. Data Pipeline & Schema Specification

### Primary Normalized Tables in DuckDB
1. `game`: Game metadata, date, competition ID, season ID, home/away scores.
2. `team`: Team canonical names, codes, aliases.
3. `player`: Athlete metadata, canonical names, birthdates, heights.
4. `game_roster`: Game-specific roster registrations and jersey numbers.
5. `boxscore_player`: Traditional boxscores (PTS, FGM/FGA, 3PM/3PA, REB, AST, STL, BLK, TOV, MIN).
6. `boxscore_team`: Team-level Four Factors and game totals.
7. `pbp_event`: Fine-grained play-by-play events (SHOT, FOUL, SUB, REB, TOV) with timestamps and event sequences.
8. `shot`: Discrete field goal attempts with coordinate tracking $(x, y)$, shot type (2PT/3PT), outcome, and assist links.

---

# 4. Mathematical Algorithms & Implementations

### 1. Continuous FIBA Half-Court Geometry
- **Dimensions:** $X \in [0, 280]$, $Y \in [0, 200]$ ($56,000\text{ units}^2$).
- **Basket Center:** $(x_0, y_0) = (140.0, 25.0)$.
- **3PT Arc Radius:** $R_{3P} = \sqrt{115^2 + 25^2} \approx 117.68602$.
- **10 Contiguous Polygons:** Restricted Area, Paint (Non-RA), Mid-Range Left, Mid-Range Center, Mid-Range Right, Corner 3 Left, Corner 3 Right, Wing 3 Left, Above Break 3 Center, Wing 3 Right.
- **Area Conservation:** Sum of polygon areas strictly verified via shoelace formula to equal $56,000.0\text{ units}^2$.

### 2. Empirical Bayes Smoothed Hot Zones
$$\Delta_{\text{shrunk}} = (\text{FG\%}_{\text{obs}} - \text{Baseline}_{\text{league}}) \times \left(\frac{N}{N + M}\right), \quad M = 5$$
Shrinks small samples toward league baselines while giving full weight to high-volume zones.

### 3. Bootstrap Uncertainty Quantification
Non-parametric resampling ($B = 1,000$) generating empirical $95\%$ Confidence Intervals:
$$\text{CI}_{95} = \left[ \hat{\theta}_{(0.025)}^{*}, \hat{\theta}_{(0.975)}^{*} \right]$$

---

# 5. Deployment & Execution

### Local Development
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run automated test suite
python -m pytest tests/ -v

# 3. Launch Streamlit application
streamlit run app/main.py
```

### Production Deployment
- **Hugging Face Spaces / Streamlit Cloud:**
  - Branch: `main`
  - Entrypoint: `app/main.py`
  - Python Version: `>= 3.10`
  - Dependencies: `requirements.txt`
  - Embedded Database: `database/jbbl_sandbox.duckdb` bundled in repo.
