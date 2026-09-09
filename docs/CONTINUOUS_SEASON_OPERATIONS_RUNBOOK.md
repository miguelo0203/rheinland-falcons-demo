# Continuous Season Operations Runbook & Matchday Ingestion Guide

## Rheinland Falcons Basketball — JBBL / NBBL Longitudinal Intelligence Platform

---

## 1. System Scope & Single-Club Operational Invariant

### Single-Club Dedication
This analytics platform is built exclusively for **Rheinland Falcons Basketball** (JBBL U16 and NBBL U19 programs). The system is not a multi-tenant or generic league platform. It is engineered as a **living longitudinal single-club intelligence system** that grows continuously across seasons (`2024/25`, `2025/26`, `2026/27`, and beyond).

### Core Operational Principles
1. **Append-Only Invariant**: New games arrive and append to the database without rebuilding historical tables.
2. **Deterministic Idempotency**: Submitting an identical payload produces a true `NO_OP_IDENTICAL` with zero database writes.
3. **Audit Trail Retention**: Official corrections create a timestamped raw backup (`match_raw_audit_prev_<ts>.json`) before applying updates.
4. **Mathematical Population Isolation**: `OFFICIAL` league fixtures are strictly segregated from `PRACTICE`, `SCRIMMAGE`, and `FRIENDLY` games to prevent benchmark contamination.
5. **Modality Elasticity**: Games remain analytically usable with boxscore-only data, while late-arriving PBP, shot coordinates, or video automatically activate advanced analytical tiers.
6. **Zero Data Fabrication (GAP-06)**: The system never invents missing boxscore statistics. Unavailable values are explicitly stored as `NULL`.
7. **Explicit Game Type Taxonomy (GAP-07)**: Every game is stored with an explicit `game_type` (`OFFICIAL`, `PRACTICE`, `SCRIMMAGE`, `FRIENDLY`, `UNKNOWN`).

---

## 2. Matchday Ingestion Workflows & Practical Examples

### Scenario A — Ingesting a New Official JBBL/NBBL Match
When a new official match is completed and its raw JSON payload is available:

```bash
python -m python.operations.incremental_ingestion \
    --payload-file data/raw/incoming_match_2005586.json \
    --game-id GAM_2005586 \
    --season-id SEA_2025 \
    --competition-id CMP_JBBL \
    --game-date 2025-02-15 \
    --home-team-id TEM_DEMO_U16 \
    --away-team-id TEM_1002 \
    --home-score 88 \
    --away-score 76 \
    --game-type OFFICIAL
```

**Expected Operational Output**:
```text
[INGESTION] Inserted game record GAM_2005586 into DuckDB.
[RECOMPUTATION] Triggering dependency graph update for season 'SEA_2025' (OFFICIAL)...
Exported 'game_registry.parquet': 67 canonical game registry records.
Exported 'team_intelligence.parquet': 146 team intelligence records.
Exported 'player_intelligence.parquet': 473 player intelligence profiles.
Exported 'player_evolution.parquet': 1362 player evolution trajectory records.
Exported 'shot_intelligence.parquet': 5188 shot intelligence records.
Exported 'coach_intelligence_findings.parquet': 5 coach intelligence findings.
[RECOMPUTATION] Dependency graph update completed successfully in 3.42s.
[OPERATIONS] Wrote operation report to OPS_20260901_103811_GAM_2005586.json
```

---

### Scenario B — Ingesting an Internal Practice Match / Scrimmage
When coach Ferran provides an internal academy scrimmage or friendly match boxscore:

```python
from python.operations.incremental_ingestion import IncrementalIngestionEngine

engine = IncrementalIngestionEngine()
engine.ingest_game(
    game_id="GAM_20250310_PRAC_01",
    season_id="SEA_2025",
    competition_id="JBBL_PRACTICE",
    game_date="2025-03-10",
    home_team_id="TEM_DEMO_U16",
    away_team_id="TEM_ACADEMY_B",
    home_score=75,
    away_score=68,
    payload={"type": "PRACTICE_SCRIMMAGE", "notes": "Full 40-min live scrimmage"},
    game_type="PRACTICE",
    player_boxscores=[
        {"team_id": "TEM_DEMO_U16", "player_id": "PLR_SERIGNE_FALL", "jersey_number": "14", "points": 18, "seconds_played": 1500, "orb": 4, "drb": 6, "trb": 10, "ast": 2, "stl": 1, "blk": 2, "tov": 3, "pf": 2},
    ]
)
```

**Population Policy Verification**:
- Player minutes, points, and physical workloads update in `player_evolution.parquet`.
- Official team Win%, net rating, and Four Factors in `team_intelligence.parquet` remain **strictly unchanged**.

---

### Scenario C — Handling Duplicate Ingestion (True NO-OP)
If an automated script or operator runs ingestion for an already ingested match:

```bash
python -m python.operations.incremental_ingestion --payload-file data/raw/incoming_match_2005586.json
```

**Output**:
```text
[INGESTION] Game GAM_2005586 already exists with IDENTICAL payload hash. Executing true NO-OP.
[CLI RESULT] {'game_id': 'GAM_2005586', 'status': 'NO_OP_IDENTICAL', 'payload_hash': '...'}
```

---

### Scenario D — Official Source Correction / Boxscore Update
If the league issues an official correction (e.g. adjust 2 points or 1 rebound):

1. The engine computes the new SHA-256 hash.
2. It detects the mismatch with `manifest.sha256`.
3. It creates a backup of the original raw JSON: `match_raw_audit_prev_<ts>.json`.
4. It updates the database record with status `SOURCE_CORRECTION` and regenerates dependent Parquet tables.

---

### Scenario E — Late-Arriving Data Modalities (PBP / Shot Coordinates)
When a match was initially recorded as boxscore-only, and play-by-play or shot tracking arrives days later:

```python
from python.operations.incremental_ingestion import IncrementalIngestionEngine

engine = IncrementalIngestionEngine()

# Late-arriving Play-by-Play
engine.append_modality(
    game_id="GAM_2005586",
    modality_type="PBP",
    records=[
        {"pbp_event_id": "EVT_001", "period": 1, "game_seconds_remaining": 2385, "period_seconds_remaining": 585, "event_type": "2FGM", "player_id": "PLR_SERIGNE_FALL", "team_id": "TEM_DEMO_U16", "score_home": 2, "score_away": 0, "is_scoring_event": True}
    ]
)
```

**Result**:
- The game's `analytical_tier` upgrades from `TIER_2_BOXSCORE_ROSTER` to `TIER_1_ADVANCED_SPATIAL_PBP`.
- `pbp_available` switches to `True` in `game_registry.parquet`.

---

### Scenario F — Launching a New Season (Auto-Discovery)
When the first fixture of a new season (e.g. `SEA_2026` or `SEA_2027`) is ingested:

1. Dynamic season start and end dates are derived automatically from `game_date`.
2. The dimension tables (`season`, `competition`) are auto-populated if not previously registered.
3. `DataService.get_available_seasons()` queries `SELECT DISTINCT season_id FROM game`.
4. The Streamlit sidebar automatically adds `SEA_2026` to the dropdown menu without editing any UI source code.

---

## 3. Automated Quality Gates & Validation Rules

| Gate ID | Rule Description | Threshold / Condition | Action on Failure |
| :--- | :--- | :--- | :--- |
| **QG-01** | Distinct Teams | `home_team_id != away_team_id` | Hard Error (`Distinct Teams Violation`) |
| **QG-02** | Valid Scores | `score >= 0` and total > 0 | Hard Error (`Score Validity Violation`) |
| **QG-03** | Scoring Reconciliation | `2*FGM + 3*FG3M + FTM = PTS` | Error Flagged & Logged |
| **QG-04** | Coordinate Bounds | `x in [0, 2800], y in [0, 1500]` | Coordinates Rejected / Flagged |
| **QG-05** | Clock Monotonicity | Game seconds non-increasing | Chronological Inversion Warning |
| **QG-06** | Sample Threshold | `N < 4` -> `INSUFFICIENT_DATA` | Trend Classification Suppressed |
| **QG-07** | Zero Fabrication | Missing stats must be `NULL` | Inventions Rejected |

---

## 4. File Inbox & Operations Reports Infrastructure

### Inbox Directory Hierarchy
```text
data/inbox/
├── incoming/    # Drop incoming raw JSON match payloads here
├── processed/   # Successfully ingested payloads (archived with timestamp)
└── rejected/    # Malformed or invalid payloads (preserved for audit)
```

### Ingestion Modes Supported
- **Mode A (Self-Contained Payload)**: `incoming/<filename>.json` containing both top-level metadata (`game_id`, `season_id`, `game_date`, `home_team_id`, etc.) and boxscore/modality event data.
- **Mode B (Payload + Companion Metadata)**: `incoming/<filename>.json` accompanied by `incoming/<filename>.metadata.json`.

### Processing the Inbox via CLI
```bash
# Ingest all files currently in incoming/
python -m python.operations.incremental_ingestion --inbox
# Or via installed entrypoint
falcons-ingest --inbox
```

### Persistent Operations Reports
Every ingestion attempt automatically generates a structured JSON report in `data/operations/`:
- **Path format**: `data/operations/OPS_YYYYMMDD_HHMMSS_<game_id>.json`
- **Fields recorded**: `operation_id`, `timestamp_utc`, `game_id`, `status` (`INGESTED_NEW`, `NO_OP_IDENTICAL`, `SOURCE_CORRECTION`, `VALIDATION_REJECTED`, `FAILED`), `sha256_hash`, `elapsed_time_seconds`, `affected_tables`, `recomputation_summary`, `validation_errors`.

---

## 5. Zero Fabrication Policy & Score-Only Handling (GAP-06)

When only final scores are available for a match:
1. **Never fabricate team shooting stats**: Do not invent default values.
2. **Store explicit `NULL`**: Shooting percentages, rebounds, assists, and turnovers are recorded as `NULL`.
3. **Analytical Usability Tier**: The fixture is assigned `TIER_3_METADATA_ONLY`.
4. **UI Safety**: Streamlit and DataService gracefully render `N/A` for missing metrics without crashing.

---

## 6. Dynamic Season Derivation & Explicit Game Types (GAP-07)

### Dynamic Season Derivation
Seasons boundaries are calculated dynamically from `game_date`:
- Month >= 9 (September-December): Season start is `YYYY-09-01`, season end is `(YYYY+1)-06-30`.
- Month < 9 (January-August): Season start is `(YYYY-1)-09-01`, season end is `YYYY-06-30`.

### Canonical Game Types
The `game` table includes an explicit `game_type` column with validated canonical values:
- `OFFICIAL`: Official league games (JBBL / NBBL regular season and playoffs).
- `PRACTICE`: Internal team training games and intra-squad scrimmages.
- `SCRIMMAGE`: Inter-club practice matches and friendly scrimmages.
- `FRIENDLY`: Pre-season or exhibition matches.
- `UNKNOWN`: Unclassified source payloads.

---

## 7. Data Freshness Monitoring & Streamlit Integration

The UI provides continuous operational visibility into the state of the analytics engine:
- **Latest Game Date**: Date of the most recently played game in the database.
- **DuckDB Modified**: Last write timestamp of the underlying DuckDB database.
- **Registry Synced**: Timestamp of the latest `game_registry.parquet` build.
- **Total Games**: Total game count indexed in the canonical registry.
- **Latest Operation Report**: Link to the most recent ingestion audit report.

Access this data programmatically:
```python
from app.services.data_service import DataService
ds = DataService()
freshness = ds.get_data_freshness()
print(freshness)
```
