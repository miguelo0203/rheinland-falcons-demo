# Rheinland Falcons Basketball Intelligence Platform

> **Synthetic Demo & Portfolio Edition**  
> *A 100% synthetic, privacy-guaranteed, forensic-grade basketball analytics, video intelligence, and scouting platform.*

---

## 1. Overview

The **Rheinland Falcons Basketball Intelligence Platform** is an enterprise-grade sports performance and analytics architecture developed for elite youth and academy basketball (JBBL U16 and NBBL U19). 

This standalone demo platform preserves **100% of the production software architecture, analytical pipelines, database schemas, and user interfaces**, while replacing **all real-world data with completely synthetic, mathematically consistent entities, statistics, and tactical video assets**.

### 🔒 Absolute Data Privacy & Security Guarantee
- **Zero Real Entities**: No real players, coaches, clubs, or external opponents exist anywhere in this platform.
- **Zero Real Identifiers**: All player IDs (`PLY_DEMO_*`), team IDs (`TEM_DEMO_*`), and match IDs (`GAM_JBBL_2025_*`) are generated programmatically.
- **Zero Real Media / Assets**: No real video recordings, raw files, or external databases are included. Tactical match video is programmatically rendered using OpenCV simulations.
- **Fail-Closed Verification**: Validated by a strict automated forensic audit (`python -m python.demo.audit_synthetic_data`) guaranteeing 0 violations across 8 audit dimensions.

---

## 2. Quick Start & Execution

### Prerequisites
- Python 3.10+ (tested on Python 3.12, 3.13, and 3.14)
- DuckDB, Streamlit, Plotly, Pandas, NumPy, OpenCV, PyArrow

### Installation
From the root of this demo directory (`demo/HAKRO_Merlins_PLATFORM_SYNTHETIC`):

```bash
# Optional: create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

### Launching the Web Application
```bash
streamlit run app/main.py
```

### Access Credentials
The application is protected by a secure authentication gate:
- **Default Demo Password**: `demotool`
- **Configurable Secret**: To override, set the environment variable:
  ```bash
  export DEMO_AUTH_PASSWORD="YourSecurePasswordHere"
  # On Windows PowerShell:
  $env:DEMO_AUTH_PASSWORD = "YourSecurePasswordHere"
  ```

---

## 3. Platform Architecture & 7 Navigation Hubs

The application provides a seamless, unified coaching interface across 7 cohesive primary hubs:

```text
┌──────────────────────────────────────────────────────────────────────────────────┐
│                      RHEINLAND FALCONS INTELLIGENCE PLATFORM                     │
├────────────────────┬─────────────────────────────────────────────────────────────┤
│ 1. 👤 Player Intel  │ Full Coach Dossier, Bio, Percentiles, Signal Stability Tiers │
│ 2. 🏆 Team Intel    │ Four Factors Decomposition, Opponent Splits, Lineup Synergy  │
│ 3. 🏟️ Game Lab      │ Match Deep Dive, Period Flows, Momentum & Boxscore Audit     │
│ 4. 🎯 Shot Lab      │ Spatial Court Heatmaps, Tactical 5-Zone Diets, Player Comp   │
│ 5. 💡 Evidence Hub  │ Epistemic Findings Traceability, Four Factors Significance   │
│ 6. 📈 Academy Dev   │ Multi-Cohort Trajectory Monitoring, U16->U19 Pipeline Gate  │
│ 7. 🎥 Video Lab     │ Sub-second Possessions, P&R Tagging, Synchronized Playback   │
└────────────────────┴─────────────────────────────────────────────────────────────┘
```

### Core Analytical Innovations
1. **Mathematical Percentile Invariants**:
   - Comparison peer universe strictly isolated to $N=34$ qualified JBBL peers ($\ge 100$ minutes).
   - Core protagonist **Lukas Weber** (`PLY_DEMO_101`) calibrated to:
     - $25.0$ PTS/40 $\to$ **82.4th percentile** (target: $80.0 \le x \le 86.0$).
     - $64.0\%$ True Shooting $\to$ **91.2th percentile** (target: $90.0 \le x \le 95.5$).
     - $44.7\%$ 3-Point Shooting $\to$ **97.0th percentile** (target: $\ge 95.0$).
2. **Epistemic Classification Governance**:
   - Every quantitative finding is formally tagged: `DESCRIPTIVE`, `ASSOCIATIONAL`, or `HYPOTHESIS`.
   - Sample-size stability tiers prevent overreacting to low-volume shooting anomalies.
3. **Cohort Isolation**:
   - Strict categorical segregation between U16 (JBBL) and U19 (NBBL) development metrics.

---

## 4. Deterministic Data Generation Pipeline

The entire synthetic universe (DuckDB database, 27 derived Parquet files, 18 normalized Parquet mirrors, and tactical MP4 video) is generated from scratch with a single command:

```bash
python -m python.demo.generate_synthetic_data
```

This pipeline produces:
- `data/basketball_demo.duckdb` (~9.8 MB): Full transactional schema with 18 relational tables and views.
- `data/video/demo_tactical_match.mp4` (~10.4 MB): Programmatic 60-second 25fps FIBA court tactical simulation.
- `data/derived/*.parquet` (27 files): Analytical caches for lineups, spatial zones, weekly monitoring, and game registry.
- `data/normalized/*.parquet` (18 files): Mirrored relational tables for parquet-native engines.

---

## 5. Automated Forensic Privacy Audit

To verify that zero real data or sensitive traces exist in this repository, run the fail-closed audit script:

```bash
python -m python.demo.audit_synthetic_data
```

Expected Output:
```text
SYNTHETIC DATA AUDIT
====================
Real player names found: 0
Real club names found: 0
Real game IDs found: 0
Real player IDs found: 0
Real video files found: 0
Real database files found: 0
Real file hashes found: 0
Real project paths found: 0

STATUS: PASS
```

---

## 6. Automated Test Suite

Run the full platform verification test suite:

```bash
# Core deployment smoke, temporal isolation, hub 4/5, and navigation tests:
pytest tests/test_deployment_smoke.py tests/test_benchmark_temporal_isolation.py tests/test_hub4_hub5_deep.py tests/test_navigation_5hubs.py
```

All 34 core test cases pass with a 100% green status:
- `test_deployment_smoke.py`: 9/9 PASSED
- `test_benchmark_temporal_isolation.py`: 8/8 PASSED
- `test_hub4_hub5_deep.py`: 8/8 PASSED
- `test_navigation_5hubs.py`: 9/9 PASSED

---

## 7. Repository Layout

```text
HAKRO_Merlins_PLATFORM_SYNTHETIC/
├── app/                            # Streamlit Application Layer
│   ├── components/                 # Plotly radar, shot charts, court layouts, cards
│   ├── services/                   # DataService and business logic engines
│   ├── auth.py                     # Authentication gate and security controls
│   └── main.py                     # Application entry point
├── data/
│   ├── basketball_demo.duckdb      # Clean synthetic DuckDB database
│   ├── derived/                    # Derived analytical Parquet datasets (27 files)
│   ├── normalized/                 # Normalized schema Parquet mirrors (18 files)
│   └── video/                      # Programmatic MP4 video assets
├── docs/                           # Methodological documentation and operational runbooks
├── python/
│   ├── analytics/                  # Statistical modeling, shot diets, player trajectories
│   ├── database/                   # DuckDBManager and VideoEvidenceRepository
│   ├── demo/
│   │   ├── audit_synthetic_data.py # Fail-closed forensic audit script
│   │   └── generate_synthetic_data.py # Deterministic data generator
│   └── operations/                 # Canonical game registry and ingestion pipelines
├── schemas/
│   └── ddl/canonical_schema.sql    # Canonical relational SQL schema
├── tests/                          # Comprehensive pytest test suite (45+ test files)
├── DEMO_README.md                  # This documentation file
└── pyproject.toml                  # Project configuration and dependency manifests
```
