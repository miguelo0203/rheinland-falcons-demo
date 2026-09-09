"""Execute Phase 2 Controlled Real-Match Ingestion Pilot for Match 9995585."""

import json
import sys
from pathlib import Path

sys.path.insert(0, ".")

from python.database.duckdb_manager import DuckDBManager
from python.ingestion.jbbl_adapter import JBBLAdapter
from python.ingestion.entity_resolver import EntityResolver
from python.ingestion.provenance import ProvenanceTracker
from python.ingestion.conflict_detector import ConflictDetector
from python.validation.engine import ValidationEngine

def run_pilot():
    print("==========================================================================")
    print("   [PHASE 2] EXECUTING CONTROLLED INGESTION PILOT FOR JBBL MATCH 9995585  ")
    print("==========================================================================")
    
    raw_dir = Path("data/raw/jbbl/9995585")
    if not raw_dir.exists():
        print(f"Error: Raw directory {raw_dir} does not exist. Run acquire_raw_pilot.py first.")
        return

    # 1. Initialize Components
    db = DuckDBManager()
    db.initialize_schema()
    db.clear_tables()
    
    resolver = EntityResolver()
    prov_tracker = ProvenanceTracker()
    conflict_detector = ConflictDetector()
    validator = ValidationEngine(conflict_detector=conflict_detector)
    
    adapter = JBBLAdapter(entity_resolver=resolver, provenance_tracker=prov_tracker)

    # 2. Extract Stage
    print("\n--- [STAGE 1: EXTRACT] Parsing RAW files ---")
    raw_data = adapter.extract(raw_dir)
    print(f"  Header parsed: Game {raw_data['header'].get('gameId')} between {raw_data['header']['homeTeam']['name']} and {raw_data['header']['guestTeam']['name']}")
    print(f"  Socket stream parsed: TeamStats={len(raw_data['stream']['team_stats'])}, PlayerStats={len(raw_data['stream']['player_stats'])}, Actions={len(raw_data['stream']['actions'])}, Lineups={len(raw_data['stream']['starting_five'])}")

    # 3. Normalize Stage
    print("\n--- [STAGE 2: NORMALIZE] Transforming to Canonical Entities ---")
    payload = adapter.normalize(
        raw_data=raw_data,
        file_path=raw_dir / "raw_socket_stream_9995585.txt",
        game_id="GAM_DEMO_001",
        season_id="SEA_2024_2025",
        competition_id="CMP_JBBL",
    )

    print(f"  Competitions:     {len(payload.competitions)}")
    print(f"  Seasons:          {len(payload.seasons)}")
    print(f"  Teams:            {len(payload.teams)}")
    print(f"  Players:          {len(payload.players)}")
    print(f"  PlayerTeams:      {len(payload.player_teams)}")
    print(f"  Game:             {len(payload.games)}")
    print(f"  GameRosters:      {len(payload.game_rosters)}")
    print(f"  BoxscoreTeams:    {len(payload.boxscore_teams)}")
    print(f"  BoxscorePlayers:  {len(payload.boxscore_players)}")
    print(f"  PBPEvents:        {len(payload.pbp_events)}")
    print(f"  Shots:            {len(payload.shots)}")
    print(f"  LineupStints:     {len(payload.lineup_stints)}")
    print(f"  EntityAliases:    {len(payload.aliases)}")

    # 4. Validation Stage
    print("\n--- [STAGE 3: VALIDATION] Running Multi-Source Integrity Rules Engine ---")
    val_out = validator.validate_game(
        game_id="GAM_DEMO_001",
        game=payload.games[0] if payload.games else None,
        boxscore_teams=payload.boxscore_teams,
        boxscore_players=payload.boxscore_players,
        pbp_events=payload.pbp_events,
        shots=payload.shots,
        boxscore_path=str((raw_dir / "raw_socket_stream_9995585.txt").as_posix()),
        pbp_path=str((raw_dir / "raw_socket_stream_9995585.txt").as_posix()),
    )
    game_src = val_out["game_sources"]
    val_results = val_out["validation_results"]
    val_logs = val_out["validation_logs"]
    
    passed_count = sum(1 for r in val_results if r.passed)
    failed_count = sum(1 for r in val_results if not r.passed)
    
    print(f"  Validation Status:    {game_src.validation_status.value}")
    print(f"  Completeness Tier:    {game_src.completeness_score.value}")
    print(f"  Quality Tier:         {game_src.overall_quality.value}")
    print(f"  Total Rules Checked:  {len(val_results)}")
    print(f"  Passed Checks:        {passed_count}")
    print(f"  Failed Checks:        {failed_count}")

    if val_logs:
        print("\n  Validation Log Sample:")
        for log in val_logs[:6]:
            print(f"    [{log.severity.value}] {log.rule_id}: {log.message}")

    # 5. DuckDB Database Insertion
    print("\n--- [STAGE 4: DUCKDB LOAD] Ingesting into relational tables ---")
    inserted_counts = db.insert_normalized_payload(payload)
    for table_name, count in inserted_counts.items():
        print(f"  Inserted into '{table_name:18}': {count:4d} rows")

    # Log validation entries into DuckDB
    val_logs_inserted = db.insert_validation_logs(val_logs)
    print(f"  Inserted into 'validation_log     ': {val_logs_inserted:4d} rows")

    # Update GameSources table
    db.upsert_game_sources(
        game_id="GAM_DEMO_001",
        boxscore_available=True,
        pbp_available=True,
        video_available=False,
        shot_chart_available=True,
        boxscore_path=str((raw_dir / "raw_socket_stream_9995585.txt").as_posix()),
        pbp_path=str((raw_dir / "raw_socket_stream_9995585.txt").as_posix()),
        val_status=game_src.validation_status,
        comp_tier=game_src.completeness_score,
        qual_tier=game_src.overall_quality,
    )
    print("  Upserted into 'game_sources' table.")

    # 6. Export to Parquet
    print("\n--- [STAGE 5: PARQUET EXPORT] Writing analytical Parquet files ---")
    parquet_files = db.export_all_to_parquet()
    for table, ppath in parquet_files.items():
        size_bytes = Path(ppath).stat().st_size
        print(f"  Exported '{table:18}' -> {ppath} ({size_bytes:,} bytes)")

    # 7. Database Verification Queries
    print("\n==========================================================================")
    print(" [STAGE 6: DATABASE VERIFICATION] Running SQL Queries in DuckDB           ")
    print("==========================================================================")
    
    # Query 1: Game record
    df_game = db.query_df("SELECT game_id, game_date, home_team_id, away_team_id, home_score, away_score, game_status FROM game")
    print("\nQuery: SELECT * FROM game:")
    print(df_game.to_string(index=False))

    # Query 2: Boxscore Teams
    df_bxt = db.query_df("SELECT team_id, is_home, points, fgm, fga, fg2m, fg2a, fg3m, fg3a, ftm, fta, trb, stl, blk, tov, pf FROM boxscore_team")
    print("\nQuery: SELECT * FROM boxscore_team:")
    print(df_bxt.to_string(index=False))

    # Query 3: Top 5 Scorers
    df_top5 = db.query_df("""
        SELECT p.canonical_name, bp.jersey_number, bp.points, bp.seconds_played / 60.0 AS minutes,
               bp.fg2m, bp.fg2a, bp.fg3m, bp.fg3a, bp.ftm, bp.fta, bp.trb, bp.ast, bp.stl
        FROM boxscore_player bp
        JOIN player p ON bp.player_id = p.player_id
        ORDER BY bp.points DESC
        LIMIT 6
    """)
    print("\nQuery: Top Scorers from match 9995585:")
    print(df_top5.to_string(index=False))

    # Query 4: PBP Event Summary
    df_pbp_summary = db.query_df("""
        SELECT event_type, COUNT(*) as count, SUM(points_scored) as total_points
        FROM pbp_event
        GROUP BY event_type
        ORDER BY count DESC
    """)
    print("\nQuery: PBP Event Type Distribution:")
    print(df_pbp_summary.to_string(index=False))

    # Query 5: Shot spatial summary
    df_shots_summary = db.query_df("""
        SELECT shot_type, is_made, shot_location_status, COUNT(*) as count
        FROM shot
        GROUP BY shot_type, is_made, shot_location_status
        ORDER BY shot_type, is_made
    """)
    print("\nQuery: Shot Location Status Breakdown:")
    print(df_shots_summary.to_string(index=False))

    print("\n==========================================================================")
    print("   PHASE 2 CONTROLLED PILOT INGESTION COMPLETED SUCCESSFULLY              ")
    print("==========================================================================")

if __name__ == "__main__":
    run_pilot()
