"""Continuous Season Incremental Ingestion & Dependency Recomputation Engine."""

import hashlib
import json
import sys
import time
import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import duckdb

sys.path.insert(0, ".")

from python.database.duckdb_manager import DuckDBManager
from python.operations.game_registry import build_game_registry
from python.analytics.phase5_team_intelligence import build_team_intelligence
from python.analytics.phase5_player_evolution import build_player_intelligence_and_evolution
from python.analytics.phase5_shot_intelligence import build_shot_intelligence
from python.analytics.phase5_coach_findings import build_coach_intelligence_findings

RAW_DIR = Path("data/raw")
DERIVED_DIR = Path("data/derived")
DOCS_DIR = Path("docs")
RAW_DIR.mkdir(parents=True, exist_ok=True)
DERIVED_DIR.mkdir(parents=True, exist_ok=True)
DOCS_DIR.mkdir(parents=True, exist_ok=True)

class IncrementalIngestionEngine:
    def __init__(self, db: Optional[DuckDBManager] = None):
        self.db = db or DuckDBManager()

    def compute_payload_hash(self, payload: Dict[str, Any]) -> str:
        s = json.dumps(payload, sort_keys=True)
        return hashlib.sha256(s.encode("utf-8")).hexdigest()

    def _write_operation_report(self, report: Dict[str, Any]):
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        game_id = report.get("game_id", "UNKNOWN")
        filename = f"OPS_{timestamp}_{game_id}.json"
        
        full_report = {
            "operation_id": f"OP_{timestamp}_{game_id}",
            "timestamp": datetime.datetime.now().isoformat(),
            "game_id": game_id,
            "season_id": report.get("season_id"),
            "competition_id": report.get("competition_id"),
            "game_type": report.get("game_type"),
            "input_files": report.get("input_files", []),
            "input_hashes": report.get("input_hashes", []),
            "status": report.get("status", "FAILED"),
            "validation_results": report.get("validation_results", {}),
            "modalities_before": report.get("modalities_before", []),
            "modalities_after": report.get("modalities_after", []),
            "database_changes": report.get("database_changes", []),
            "recomputation_steps": report.get("recomputation_steps", []),
            "elapsed_time_seconds": report.get("elapsed_time_seconds", 0.0),
            "warnings": report.get("warnings", []),
            "errors": report.get("errors", [])
        }
        
        ops_dir = Path("data/operations")
        ops_dir.mkdir(parents=True, exist_ok=True)
        (ops_dir / filename).write_text(json.dumps(full_report, indent=2), encoding="utf-8")
        print(f"[OPERATIONS] Wrote operation report to {filename}")

    def ingest_game(
        self,
        game_id: str,
        season_id: str,
        competition_id: str,
        game_date: str,
        home_team_id: str,
        away_team_id: str,
        home_score: int,
        away_score: int,
        payload: Dict[str, Any],
        game_type: str = "OFFICIAL",
        phase: str = "MAIN_ROUND",
        group_name: str = "JBBL",
        player_boxscores: Optional[List[Dict[str, Any]]] = None,
        shots: Optional[List[Dict[str, Any]]] = None,
        input_files: Optional[List[str]] = None,
        home_boxscore: Optional[Dict[str, Any]] = None,
        away_boxscore: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Ingests a game incrementally with idempotency and historical immutability."""
        start_time = time.time()
        payload_hash = self.compute_payload_hash(payload)

        # 1. Check if game already exists in DuckDB
        df_exists = self.db.query_df(f"SELECT game_id FROM game WHERE game_id = '{game_id}'")
        
        raw_game_dir = RAW_DIR / "jbbl" / season_id / game_id
        raw_game_dir.mkdir(parents=True, exist_ok=True)
        raw_file = raw_game_dir / "match_raw.json"
        manifest_file = raw_game_dir / "manifest.sha256"

        if not df_exists.empty:
            if manifest_file.exists() and manifest_file.read_text(encoding="utf-8").strip() == payload_hash:
                print(f"[INGESTION] Game {game_id} already exists with IDENTICAL payload hash. Executing true NO-OP.")
                result = {
                    "game_id": game_id,
                    "status": "NO_OP_IDENTICAL",
                    "payload_hash": payload_hash,
                    "message": "Game already ingested and verified identical.",
                }
                self._write_operation_report({
                    "game_id": game_id,
                    "season_id": season_id,
                    "competition_id": competition_id,
                    "game_type": game_type,
                    "input_files": input_files or [],
                    "input_hashes": [payload_hash],
                    "status": "NO_OP_IDENTICAL",
                    "elapsed_time_seconds": time.time() - start_time
                })
                return result
            else:
                print(f"[INGESTION] Game {game_id} exists but source changed. Preserving audit history.")
                # Version previous raw file
                if raw_file.exists():
                    backup_file = raw_game_dir / f"match_raw_audit_prev_{int(pd.Timestamp.now().timestamp())}.json"
                    raw_file.rename(backup_file)

        # 2. Save raw payload & SHA-256 manifest
        raw_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        manifest_file.write_text(payload_hash, encoding="utf-8")

        # 3. Ensure foreign keys exist in dimension tables
        df_cmp = self.db.query_df(f"SELECT competition_id FROM competition WHERE competition_id = '{competition_id}'")
        if df_cmp.empty:
            self.db.execute(f"INSERT INTO competition (competition_id, name, gender, age_category, country, governing_body, created_at) VALUES ('{competition_id}', 'JBBL Program Competition', 'MALE', 'U16', 'DE', 'DBB', CURRENT_TIMESTAMP);")

        df_sea = self.db.query_df(f"SELECT season_id FROM season WHERE season_id = '{season_id}'")
        if df_sea.empty:
            g_year = int(game_date.split('-')[0])
            g_month = int(game_date.split('-')[1])
            if g_month >= 9:
                start_date = f"{g_year}-09-01"
                end_date = f"{g_year+1}-06-30"
            else:
                start_date = f"{g_year-1}-09-01"
                end_date = f"{g_year}-06-30"
            self.db.execute(f"INSERT INTO season (season_id, competition_id, name, start_date, end_date) VALUES ('{season_id}', '{competition_id}', 'Season {season_id}', '{start_date}', '{end_date}');")

        for tid, tname in [(home_team_id, "Home Team"), (away_team_id, "Away Team")]:
            df_tm = self.db.query_df(f"SELECT team_id FROM team WHERE team_id = '{tid}'")
            if df_tm.empty:
                self.db.execute(f"INSERT INTO team (team_id, canonical_name, created_at) VALUES ('{tid}', '{tname}', CURRENT_TIMESTAMP);")

        # 4. Insert or Update Game Record in DuckDB
        if df_exists.empty:
            insert_sql = f"""
            INSERT INTO game (game_id, season_id, competition_id, round_number, game_date, home_team_id, away_team_id, home_score, away_score, game_status, game_type)
            VALUES ('{game_id}', '{season_id}', '{competition_id}', 1, '{game_date}', '{home_team_id}', '{away_team_id}', {home_score}, {away_score}, 'FINAL', '{game_type}');
            """
            self.db.execute(insert_sql)
            print(f"[INGESTION] Inserted game record {game_id} into DuckDB.")

        # 5. Insert Source Provenance Record
        prov_id = f"PRV_{game_id}"
        df_prv = self.db.query_df(f"SELECT provenance_id FROM source_provenance WHERE provenance_id = '{prov_id}'")
        if df_prv.empty:
            self.db.execute(f"""
            INSERT INTO source_provenance (provenance_id, source_type, source_provider, source_file_path, source_file_hash, parser_version, pipeline_version, ingestion_timestamp)
            VALUES ('{prov_id}', 'BOXSCORE', 'Rheinland Falcons Operations', '{raw_file.as_posix()}', '{payload_hash}', 'jbbl_adapter_v2.0', '2.0.0', CURRENT_TIMESTAMP);
            """)

        # 6. Insert Team Boxscores if new
        self.db.execute(f"DELETE FROM boxscore_team WHERE game_id = '{game_id}';")
        
        def format_box(team_id, is_home, score, box):
            if box:
                def get_val(key):
                    val = box.get(key)
                    return str(val) if val is not None else "NULL"
                return f"('BXT_{game_id}_{team_id}', '{game_id}', '{team_id}', {is_home}, {score}, {get_val('fgm')}, {get_val('fga')}, {get_val('fg3m')}, {get_val('fg3a')}, {get_val('ftm')}, {get_val('fta')}, {get_val('orb')}, {get_val('drb')}, {get_val('trb')}, {get_val('ast')}, {get_val('stl')}, {get_val('blk')}, {get_val('tov')}, {get_val('pf')}, '{prov_id}')"
            else:
                return f"('BXT_{game_id}_{team_id}', '{game_id}', '{team_id}', {is_home}, {score}, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, '{prov_id}')"
        
        home_val = format_box(home_team_id, "TRUE", home_score, home_boxscore)
        away_val = format_box(away_team_id, "FALSE", away_score, away_boxscore)
        
        self.db.execute(f"""
            INSERT INTO boxscore_team (boxscore_team_id, game_id, team_id, is_home, points, fgm, fga, fg3m, fg3a, ftm, fta, orb, drb, trb, ast, stl, blk, tov, pf, provenance_id)
            VALUES
            {home_val},
            {away_val};
        """)

        # 7. Insert Player Boxscores if provided
        if player_boxscores:
            self.db.execute(f"DELETE FROM boxscore_player WHERE game_id = '{game_id}';")
            for p in player_boxscores:
                pid = p.get('player_id', 'PLY_DEMO_104')
                tid = p.get('team_id', home_team_id)
                df_p = self.db.query_df(f"SELECT player_id FROM player WHERE player_id = '{pid}'")
                if df_p.empty:
                    self.db.execute(f"INSERT INTO player (player_id, canonical_name, created_at) VALUES ('{pid}', 'Boxscore Player', CURRENT_TIMESTAMP);")
                df_t = self.db.query_df(f"SELECT team_id FROM team WHERE team_id = '{tid}'")
                if df_t.empty:
                    self.db.execute(f"INSERT INTO team (team_id, canonical_name, created_at) VALUES ('{tid}', 'Boxscore Team', CURRENT_TIMESTAMP);")

                self.db.execute(f"""
                INSERT INTO boxscore_player (
                    boxscore_player_id, game_id, team_id, player_id, jersey_number, is_dnp, seconds_played,
                    points, fgm, fga, fg2m, fg2a, fg3m, fg3a, ftm, fta, orb, drb, trb, ast, stl, blk, tov, pf, observation_status, provenance_id
                ) VALUES (
                    'BXP_{game_id}_{pid}', '{game_id}', '{tid}', '{pid}', '{p.get('jersey_number', 0)}',
                    {p.get('is_dnp', False)}, {p.get('seconds_played', 1200)}, {p.get('points', 0)},
                    {p.get('fgm', 0)}, {p.get('fga', 0)}, {p.get('fg2m', 0)}, {p.get('fg2a', 0)},
                    {p.get('fg3m', 0)}, {p.get('fg3a', 0)}, {p.get('ftm', 0)}, {p.get('fta', 0)},
                    {p.get('orb', 0)}, {p.get('drb', 0)}, {p.get('trb', 0)}, {p.get('ast', 0)},
                    {p.get('stl', 0)}, {p.get('blk', 0)}, {p.get('tov', 0)}, {p.get('pf', 0)}, 'OBSERVED', '{prov_id}'
                );
                """)

        # 6. Insert Shots if provided
        if shots:
            self.db.execute(f"DELETE FROM shot WHERE game_id = '{game_id}';")
            for s in shots:
                pid = s.get('player_id', 'PLY_DEMO_104')
                tid = s.get('team_id', home_team_id)
                df_p = self.db.query_df(f"SELECT player_id FROM player WHERE player_id = '{pid}'")
                if df_p.empty:
                    self.db.execute(f"INSERT INTO player (player_id, canonical_name, created_at) VALUES ('{pid}', 'Shot Player', CURRENT_TIMESTAMP);")
                df_t = self.db.query_df(f"SELECT team_id FROM team WHERE team_id = '{tid}'")
                if df_t.empty:
                    self.db.execute(f"INSERT INTO team (team_id, canonical_name, created_at) VALUES ('{tid}', 'Shot Team', CURRENT_TIMESTAMP);")

                self.db.execute(f"""
                INSERT INTO shot (
                    shot_id, game_id, team_id, player_id, period, game_seconds_remaining,
                    shot_type, is_made, points, x_coord, y_coord, shot_location_status, provenance_id
                ) VALUES (
                    '{s['shot_id']}', '{game_id}', '{tid}', '{pid}',
                    {s.get('period', 1)}, {s.get('game_seconds_remaining', 300)},
                    '{s.get('shot_type', '2PT')}', {s.get('is_made', True)}, {s.get('points', 2)},
                    {s.get('x_coord', 140.0)}, {s.get('y_coord', 25.0)}, '{s.get('shot_location_status', 'OBSERVED')}', '{prov_id}'
                );
                """)

        # 7. Recompute Affected Downstream Layers
        self.recompute_dependencies(season_id=season_id, game_type=game_type)

        status_val = "SOURCE_CORRECTION" if not df_exists.empty else "INGESTED_NEW"
        
        elapsed = time.time() - start_time
        result = {
            "game_id": game_id,
            "status": status_val,
            "payload_hash": payload_hash,
            "game_type": game_type,
            "message": f"Successfully ingested {game_type} game {game_id} and recomputed downstream intelligence.",
            "elapsed_seconds": elapsed,
        }
        self._write_operation_report({
            "game_id": game_id,
            "season_id": season_id,
            "competition_id": competition_id,
            "game_type": game_type,
            "input_files": input_files or [],
            "input_hashes": [payload_hash],
            "status": status_val,
            "database_changes": ["game", "boxscore_team", "boxscore_player", "shot"],
            "recomputation_steps": ["game_registry", "team_intelligence", "player_evolution", "shot_intelligence", "coach_findings"],
            "elapsed_time_seconds": elapsed
        })
        return result

    def validate_quality_gates(self, payload: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validates all canonical quality gates before analytical promotion."""
        errors = []
        home_id = payload.get("home_team_id")
        away_id = payload.get("away_team_id")
        if home_id and away_id and home_id == away_id:
            errors.append(f"Distinct Teams Violation: home_team_id '{home_id}' equals away_team_id.")

        home_score = payload.get("home_score", 0)
        away_score = payload.get("away_score", 0)
        if home_score < 0 or away_score < 0:
            errors.append("Score Validity Violation: scores cannot be negative.")

        # Validate shots if present
        shots = payload.get("shots", [])
        for s in shots:
            x, y = s.get("x_coord", 0), s.get("y_coord", 0)
            if not (0 <= x <= 2800 and 0 <= y <= 1500):
                errors.append(f"Spatial Coordinate Bounds Violation: ({x}, {y}) out of [0, 2800]x[0, 1500].")
                break

        # Validate player scoring formula if present
        pbxs = payload.get("player_boxscores", [])
        for p in pbxs:
            calc_pts = p.get("fg2m", 0) * 2 + p.get("fg3m", 0) * 3 + p.get("ftm", 0)
            if p.get("points") is not None and calc_pts != p.get("points") and (p.get("fg2m") is not None or p.get("fg3m") is not None):
                errors.append(f"Scoring Formula Violation for player {p.get('player_id')}: {calc_pts} != {p.get('points')}")
                break

        return (len(errors) == 0, errors)

    def append_modality(
        self,
        game_id: str,
        modality_type: str,
        records: List[Dict[str, Any]],
        season_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Appends late-arriving modalities (PBP, Shots, Video) to an existing canonical game."""
        start_time = time.time()
        df_game = self.db.query_df(f"SELECT game_id, season_id, competition_id FROM game WHERE game_id = '{game_id}'")
        if df_game.empty:
            raise ValueError(f"Game {game_id} does not exist in canonical storage. Ingest base game first.")

        season = season_id or df_game["season_id"].iloc[0]
        comp = df_game["competition_id"].iloc[0]
        game_type = "PRACTICE" if "PRAC" in str(comp) or "PRAC" in game_id else "OFFICIAL"

        if modality_type.upper() == "PBP":
            self.db.execute(f"DELETE FROM pbp_event WHERE game_id = '{game_id}';")
            prov_id = f"PRV_{game_id}"
            df_prv = self.db.query_df(f"SELECT provenance_id FROM source_provenance WHERE provenance_id = '{prov_id}'")
            if df_prv.empty:
                self.db.execute(f"""
                INSERT INTO source_provenance (provenance_id, source_type, source_provider, source_file_path, source_file_hash, parser_version, pipeline_version, ingestion_timestamp)
                VALUES ('{prov_id}', 'PBP', 'Rheinland Falcons Operations', 'data/raw/pbp_late.json', 'LATE_PBP_HASH', 'jbbl_adapter_v2.0', '2.0.0', CURRENT_TIMESTAMP);
                """)

            for idx, e in enumerate(records, start=1):
                eid = e.get('event_id') or e.get('pbp_event_id') or f"EVT_{game_id}_{idx}"
                pid = e.get('player_id', 'PLY_DEMO_104')
                tid = e.get('team_id', 'TEM_DEMO_U16')

                df_p = self.db.query_df(f"SELECT player_id FROM player WHERE player_id = '{pid}'")
                if df_p.empty:
                    self.db.execute(f"INSERT INTO player (player_id, canonical_name, created_at) VALUES ('{pid}', 'Modality Player', CURRENT_TIMESTAMP);")

                df_t = self.db.query_df(f"SELECT team_id FROM team WHERE team_id = '{tid}'")
                if df_t.empty:
                    self.db.execute(f"INSERT INTO team (team_id, canonical_name, created_at) VALUES ('{tid}', 'Modality Team', CURRENT_TIMESTAMP);")

                self.db.execute(f"""
                INSERT INTO pbp_event (
                    event_id, game_id, period, period_type, clock_display,
                    game_seconds_remaining, period_seconds_remaining, event_index, event_type,
                    player_id, team_id, home_score, away_score, score_margin, points_scored,
                    description, provenance_id
                ) VALUES (
                    '{eid}', '{game_id}', {e.get('period', 1)}, 'REGULAR', '10:00',
                    {e.get('game_seconds_remaining', 2400)}, {e.get('period_seconds_remaining', 600)},
                    {idx}, '{e.get('event_type', 'PLAY')}', '{pid}',
                    '{tid}', {e.get('score_home', 0)}, {e.get('score_away', 0)},
                    0, {2 if e.get('is_scoring_event') else 0}, '{e.get('description', '')}', '{prov_id}'
                );
                """)
            print(f"[MODALITY] Appended {len(records)} PBP events to existing game {game_id}.")

        elif modality_type.upper() in ["SHOT", "SHOTS"]:
            self.db.execute(f"DELETE FROM shot WHERE game_id = '{game_id}';")
            prov_id = f"PRV_{game_id}"
            df_prv = self.db.query_df(f"SELECT provenance_id FROM source_provenance WHERE provenance_id = '{prov_id}'")
            if df_prv.empty:
                self.db.execute(f"""
                INSERT INTO source_provenance (provenance_id, source_type, source_provider, source_file_path, source_file_hash, parser_version, pipeline_version, ingestion_timestamp)
                VALUES ('{prov_id}', 'SHOTS', 'Rheinland Falcons Operations', 'data/raw/shots_late.json', 'LATE_SHOTS_HASH', 'jbbl_adapter_v2.0', '2.0.0', CURRENT_TIMESTAMP);
                """)

            for s in records:
                pid = s.get('player_id', 'PLY_DEMO_104')
                tid = s.get('team_id', 'TEM_DEMO_U16')

                df_p = self.db.query_df(f"SELECT player_id FROM player WHERE player_id = '{pid}'")
                if df_p.empty:
                    self.db.execute(f"INSERT INTO player (player_id, canonical_name, created_at) VALUES ('{pid}', 'Modality Player', CURRENT_TIMESTAMP);")

                df_t = self.db.query_df(f"SELECT team_id FROM team WHERE team_id = '{tid}'")
                if df_t.empty:
                    self.db.execute(f"INSERT INTO team (team_id, canonical_name, created_at) VALUES ('{tid}', 'Modality Team', CURRENT_TIMESTAMP);")

                self.db.execute(f"""
                INSERT INTO shot (
                    shot_id, game_id, team_id, player_id, period, game_seconds_remaining,
                    shot_type, is_made, points, x_coord, y_coord, shot_location_status, provenance_id
                ) VALUES (
                    '{s['shot_id']}', '{game_id}', '{tid}', '{pid}',
                    {s.get('period', 1)}, {s.get('game_seconds_remaining', 300)},
                    '{s.get('shot_type', '2PT')}', {s.get('is_made', True)}, {s.get('points', 2)},
                    {s.get('x_coord', 140.0)}, {s.get('y_coord', 25.0)}, '{s.get('shot_location_status', 'OBSERVED')}', '{prov_id}'
                );
                """)
            print(f"[MODALITY] Appended {len(records)} shots to existing game {game_id}.")

        # Recompute affected dependencies
        self.recompute_dependencies(season_id=season, game_type=game_type)
        
        result = {
            "game_id": game_id,
            "status": "MODALITY_APPENDED",
            "modality": modality_type,
            "count": len(records),
            "message": f"Successfully appended {modality_type} data to game {game_id}."
        }
        self._write_operation_report({
            "game_id": game_id,
            "season_id": season,
            "competition_id": comp,
            "game_type": game_type,
            "status": "MODALITY_APPENDED",
            "database_changes": [("pbp_event" if modality_type.upper() == "PBP" else "shot")],
            "recomputation_steps": ["game_registry", "team_intelligence", "player_evolution", "shot_intelligence", "coach_findings"],
            "elapsed_time_seconds": time.time() - start_time
        })
        return result

    def recompute_dependencies(self, season_id: str, game_type: str) -> Dict[str, Any]:
        """Recomputes all affected analytical intelligence layers."""
        start_time = time.time()
        print(f"[RECOMPUTATION] Triggering dependency graph update for season '{season_id}' ({game_type})...")
        build_game_registry()
        build_team_intelligence()
        build_player_intelligence_and_evolution()
        build_shot_intelligence()
        build_coach_intelligence_findings()
        elapsed = time.time() - start_time
        print(f"[RECOMPUTATION] Dependency graph update completed successfully in {elapsed:.2f}s.")
        return {"status": "SUCCESS", "elapsed_seconds": elapsed}

def generate_operations_policies():
    # 1. docs/historical_immutability_policy.md
    imm_doc = """# Historical Immutability & Audit Trail Policy

## 1. Zero Mutation of Historical Evidence
1. **Append-Only Invariants**: Newly ingested fixtures are appended without modifying existing database rows or raw files.
2. **True NO-OP on Identical Payloads**: When an already ingested fixture is processed with an identical SHA-256 payload hash, the engine executes a complete NO-OP.
3. **Audit Versioning on Source Corrections**: If an external data source issues an official correction to a previous game, the existing raw payload is preserved as a timestamped backup before archiving the updated record.
"""
    (DOCS_DIR / "historical_immutability_policy.md").write_text(imm_doc.strip(), encoding="utf-8")

    # 2. docs/incremental_analytics_dependency_map.md
    dep_doc = """# Incremental Analytics Dependency Map

## 1. Downstream Recomputation Graph

```text
NEW GAME INGESTION (game_id, season_id, game_type)
    │
    ├──> 1. CANONICAL GAME REGISTRY (data/derived/game_registry.parquet)
    │
    ├──> 2. TEAM INTELLIGENCE (data/derived/team_intelligence.parquet)
    │       - If OFFICIAL: Updates season Four Factors, win%, ORtg/DRtg
    │       - If PRACTICE: Isolated from official league tables
    │
    ├──> 3. PLAYER EVOLUTION & ROLLING WINDOWS (data/derived/player_evolution.parquet)
    │       - Game-by-game deltas
    │       - Rolling 3/4/5-game averages & trend slopes
    │       - Weekly performance trajectories
    │
    ├──> 4. SHOT INTELLIGENCE (data/derived/shot_intelligence.parquet)
    │       - Spatial coordinates & 5 tactical court zones
    │
    └──> 5. COACH FINDINGS & HYPOTHESES (data/derived/coach_intelligence_findings.parquet)
            - 3-level cognitive hierarchy & video review tags
```
"""
    (DOCS_DIR / "incremental_analytics_dependency_map.md").write_text(dep_doc.strip(), encoding="utf-8")
    print("Generated historical immutability policy and dependency map.")

def process_inbox(engine: IncrementalIngestionEngine):
    import shutil
    incoming_dir = Path("data/inbox/incoming")
    processed_dir = Path("data/inbox/processed")
    rejected_dir = Path("data/inbox/rejected")
    
    incoming_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)
    rejected_dir.mkdir(parents=True, exist_ok=True)
    
    files = list(incoming_dir.glob("*.json"))
    metadata_files = {f.name: f for f in incoming_dir.glob("*.metadata.json")}
    payload_files = [f for f in files if not f.name.endswith(".metadata.json")]
    
    success_count = 0
    fail_count = 0
    
    for p_file in payload_files:
        start_time = time.time()
        try:
            payload = json.loads(p_file.read_text(encoding="utf-8"))
            meta_name = p_file.stem + ".metadata.json"
            
            is_mode_b = meta_name in metadata_files
            meta_file = metadata_files.get(meta_name)
            
            if is_mode_b:
                metadata = json.loads(meta_file.read_text(encoding="utf-8"))
                for k, v in metadata.items():
                    if k not in payload:
                        payload[k] = v
                        
            req_fields = ["game_id", "season_id", "competition_id", "game_date", 
                          "home_team_id", "away_team_id", "home_score", "away_score", "game_type"]
            missing = [f for f in req_fields if payload.get(f) is None]
            
            input_files = [str(p_file)]
            if meta_file:
                input_files.append(str(meta_file))
                
            if missing:
                engine._write_operation_report({
                    "game_id": payload.get("game_id", "UNKNOWN"),
                    "status": "VALIDATION_REJECTED",
                    "input_files": input_files,
                    "errors": [f"Missing required fields: {', '.join(missing)}"],
                    "elapsed_time_seconds": time.time() - start_time
                })
                shutil.move(str(p_file), str(rejected_dir / p_file.name))
                if meta_file:
                    shutil.move(str(meta_file), str(rejected_dir / meta_file.name))
                fail_count += 1
                continue
                
            res = engine.ingest_game(
                game_id=payload["game_id"],
                season_id=payload["season_id"],
                competition_id=payload["competition_id"],
                game_date=payload["game_date"],
                home_team_id=payload["home_team_id"],
                away_team_id=payload["away_team_id"],
                home_score=int(payload["home_score"]),
                away_score=int(payload["away_score"]),
                payload=payload,
                game_type=payload["game_type"],
                player_boxscores=payload.get("player_boxscores"),
                shots=payload.get("shots"),
                input_files=input_files,
                home_boxscore=payload.get("home_boxscore"),
                away_boxscore=payload.get("away_boxscore"),
            )
            
            shutil.move(str(p_file), str(processed_dir / p_file.name))
            if meta_file:
                shutil.move(str(meta_file), str(processed_dir / meta_file.name))
            success_count += 1
            
        except Exception as e:
            engine._write_operation_report({
                "game_id": "UNKNOWN",
                "status": "FAILED",
                "input_files": [str(p_file)],
                "errors": [str(e)],
                "elapsed_time_seconds": time.time() - start_time
            })
            shutil.move(str(p_file), str(rejected_dir / p_file.name))
            fail_count += 1

    print(f"[INBOX] Processed {success_count + fail_count} files. Success: {success_count}, Failed: {fail_count}")

def main_cli():
    import argparse
    parser = argparse.ArgumentParser(description="Continuous Season Incremental Ingestion CLI for Rheinland Falcons JBBL/NBBL")
    parser.add_argument("--payload-file", type=str, help="Path to raw JSON payload file")
    parser.add_argument("--game-id", type=str, help="Canonical Game ID (e.g. GAM_DEMO_001)")
    parser.add_argument("--season-id", type=str, default="SEA_2025", help="Season ID (e.g. SEA_2025, SEA_2026)")
    parser.add_argument("--competition-id", type=str, default="CMP_JBBL", help="Competition ID")
    parser.add_argument("--game-date", type=str, default="2025-01-01", help="Game Date (YYYY-MM-DD)")
    parser.add_argument("--home-team-id", type=str, default="TEM_DEMO_U16", help="Home Team ID")
    parser.add_argument("--away-team-id", type=str, default="TEM_1001", help="Away Team ID")
    parser.add_argument("--home-score", type=int, default=80, help="Home Score")
    parser.add_argument("--away-score", type=int, default=70, help="Away Score")
    parser.add_argument("--game-type", type=str, default="OFFICIAL", choices=["OFFICIAL", "PRACTICE", "SCRIMMAGE", "FRIENDLY"])
    parser.add_argument("--recompute-only", action="store_true", help="Trigger dependency recomputation without ingestion")
    parser.add_argument("--inbox", action="store_true", help="Process all files in the data/inbox/incoming directory")

    args = parser.parse_args()
    engine = IncrementalIngestionEngine()

    if args.inbox:
        process_inbox(engine)
        return

    if args.recompute_only:
        engine.recompute_dependencies(season_id=args.season_id, game_type=args.game_type)
        return

    if args.payload_file:
        p = Path(args.payload_file)
        if not p.exists():
            print(f"Error: Payload file not found at {p}")
            sys.exit(1)
        payload = json.loads(p.read_text(encoding="utf-8"))
        gid = args.game_id or f"GAM_{payload.get('match_id', 'NEW')}"
        res = engine.ingest_game(
            game_id=gid,
            season_id=args.season_id,
            competition_id=args.competition_id,
            game_date=args.game_date,
            home_team_id=args.home_team_id,
            away_team_id=args.away_team_id,
            home_score=args.home_score,
            away_score=args.away_score,
            payload=payload,
            game_type=args.game_type,
        )
        print(f"[CLI RESULT] {res}")
    else:
        print("[CLI] No payload file specified. Run with --help for usage instructions.")

if __name__ == "__main__":
    generate_operations_policies()
    if len(sys.argv) > 1:
        main_cli()
