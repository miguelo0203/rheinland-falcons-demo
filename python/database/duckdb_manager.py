"""DuckDB Database Manager for Canonical Storage & Querying."""

from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import duckdb
import pandas as pd

from python.config import Settings


class DuckDBManager:
    """Manages connections, schema initialization, and transactional table operations."""

    def __init__(self, db_path: Optional[Union[str, Path]] = None, in_memory: bool = False, read_only: bool = False):
        self.read_only = read_only
        if in_memory:
            self.db_path = ":memory:"
        else:
            self.db_path = str(db_path or Settings.DATABASE_PATH)
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        self._conn: Optional[duckdb.DuckDBPyConnection] = None

    @property
    def conn(self) -> duckdb.DuckDBPyConnection:
        """Provide active connection."""
        if self._conn is None:
            if self.db_path == ":memory:":
                self._conn = duckdb.connect(self.db_path)
            else:
                try:
                    self._conn = duckdb.connect(self.db_path, read_only=self.read_only)
                except Exception:
                    try:
                        self._conn = duckdb.connect(self.db_path, read_only=True)
                        self.read_only = True
                    except Exception:
                        raise
        return self._conn

    def close(self):
        """Close connection cleanly."""
        if self._conn is not None:
            try:
                self._conn.close()
            except Exception:
                pass
            self._conn = None

    def __del__(self):
        self.close()

    def execute(self, query: str, params: Optional[List[Any]] = None):
        """Execute raw SQL statement safely."""
        try:
            if params:
                return self.conn.execute(query, params)
            return self.conn.execute(query)
        except Exception:
            try:
                self._conn = None
                if params:
                    return self.conn.execute(query, params)
                return self.conn.execute(query)
            except Exception:
                return None

    def initialize_schema(self, ddl_path: Optional[Union[str, Path]] = None) -> None:
        """Run canonical SQL DDL to create tables and indexes."""
        path = Path(ddl_path or (Settings.ROOT_DIR / "schemas" / "ddl" / "canonical_schema.sql"))
        if not path.exists():
            raise FileNotFoundError(f"Canonical DDL file not found at {path}")

        sql_script = path.read_text(encoding="utf-8")
        self.conn.execute(sql_script)

    def table_exists(self, table_name: str) -> bool:
        """Check if a table exists."""
        res = self.conn.execute(
            "SELECT count(*) FROM information_schema.tables WHERE table_name = ?",
            [table_name]
        ).fetchone()
        return bool(res and res[0] > 0)

    def insert_records(self, table_name: str, records: List[Dict[str, Any]], pk_col: Optional[str] = None) -> int:
        """Insert records from list of dicts without silent overwrite or duplicate key violations."""
        if not records:
            return 0
        df = pd.DataFrame(records)
        return self.insert_dataframe(table_name, df, pk_col=pk_col)

    def insert_dataframe(self, table_name: str, df: pd.DataFrame, pk_col: Optional[str] = None) -> int:
        """Append records from pandas DataFrame, ignoring already inserted primary keys."""
        if df.empty:
            return 0

        # Get table columns
        table_cols = [
            row[0] for row in self.conn.execute(
                f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table_name}'"
            ).fetchall()
        ]
        insert_cols = [col for col in df.columns if col in table_cols]
        cols_str = ", ".join(insert_cols)

        # Identify primary key column if not explicitly given
        if not pk_col:
            candidates = [
                f"{table_name}_id",
                "alias_id",
                "conflict_id",
                "validation_id",
                "sync_id",
                "provenance_id",
                "game_id",
            ]
            for c in candidates:
                if c in insert_cols:
                    pk_col = c
                    break

        self.conn.register("tmp_insert_df", df)

        if pk_col and pk_col in insert_cols:
            self.conn.execute(
                f"INSERT INTO {table_name} ({cols_str}) "
                f"SELECT DISTINCT {cols_str} FROM tmp_insert_df "
                f"WHERE {pk_col} NOT IN (SELECT {pk_col} FROM {table_name})"
            )
        else:
            self.conn.execute(
                f"INSERT INTO {table_name} ({cols_str}) SELECT {cols_str} FROM tmp_insert_df"
            )

        self.conn.unregister("tmp_insert_df")
        return len(df)

    def query_df(self, query: str, params: Optional[List[Any]] = None) -> pd.DataFrame:
        """Execute SQL query and return pandas DataFrame."""
        if params:
            return self.conn.execute(query, params).df()
        return self.conn.execute(query).df()

    def get_table_count(self, table_name: str) -> int:
        """Get row count of a table."""
        res = self.conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()
        return res[0] if res else 0

    def export_to_parquet(self, table_name: str, output_path: Union[str, Path]) -> Path:
        """Export table contents to Parquet file."""
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        self.conn.execute(
            f"COPY {table_name} TO '{out.as_posix()}' (FORMAT PARQUET, CODEC 'SNAPPY')"
        )
        return out

    def insert_normalized_payload(self, payload: Any) -> Dict[str, int]:
        """Inserts all entities from a NormalizedPayload into their respective DuckDB tables."""
        counts = {}
        if getattr(payload, "competitions", None):
            counts["competition"] = self.insert_records("competition", [c.model_dump() for c in payload.competitions])
        if getattr(payload, "seasons", None):
            counts["season"] = self.insert_records("season", [s.model_dump() for s in payload.seasons])
        if getattr(payload, "teams", None):
            counts["team"] = self.insert_records("team", [t.model_dump() for t in payload.teams])
        if getattr(payload, "players", None):
            counts["player"] = self.insert_records("player", [p.model_dump() for p in payload.players])
        if getattr(payload, "player_teams", None):
            counts["player_team"] = self.insert_records("player_team", [pt.model_dump() for pt in payload.player_teams])
        if getattr(payload, "games", None):
            counts["game"] = self.insert_records("game", [g.model_dump() for g in payload.games])
        if getattr(payload, "provenance", None):
            counts["source_provenance"] = self.insert_records("source_provenance", [payload.provenance.model_dump()])
        if getattr(payload, "game_rosters", None):
            counts["game_roster"] = self.insert_records("game_roster", [gr.model_dump() for gr in payload.game_rosters])
        if getattr(payload, "boxscore_teams", None):
            counts["boxscore_team"] = self.insert_records("boxscore_team", [bt.model_dump() for bt in payload.boxscore_teams])
        if getattr(payload, "boxscore_players", None):
            counts["boxscore_player"] = self.insert_records("boxscore_player", [bp.model_dump() for bp in payload.boxscore_players])
        if getattr(payload, "pbp_events", None):
            counts["pbp_event"] = self.insert_records("pbp_event", [e.model_dump() for e in payload.pbp_events])
        if getattr(payload, "shots", None):
            counts["shot"] = self.insert_records("shot", [s.model_dump() for s in payload.shots])
        if getattr(payload, "lineup_stints", None):
            counts["lineup_stint"] = self.insert_records("lineup_stint", [ls.model_dump() for ls in payload.lineup_stints])
        if getattr(payload, "aliases", None):
            counts["entity_alias"] = self.insert_records("entity_alias", [a.model_dump() for a in payload.aliases])
        return counts

    def insert_validation_logs(self, logs: List[Any]) -> int:
        """Inserts validation log entries."""
        if not logs:
            return 0
        return self.insert_records("validation_log", [l.model_dump() for l in logs])

    def upsert_game_sources(
        self,
        game_id: str,
        boxscore_available: bool = False,
        pbp_available: bool = False,
        video_available: bool = False,
        shot_chart_available: bool = False,
        boxscore_path: Optional[str] = None,
        pbp_path: Optional[str] = None,
        video_path: Optional[str] = None,
        val_status: Any = "UNVALIDATED",
        comp_tier: Any = "MINIMAL",
        qual_tier: Any = "LOW",
    ):
        """Insert or replace game_sources metadata record."""
        val_status_str = getattr(val_status, "value", str(val_status))
        comp_tier_str = getattr(comp_tier, "value", str(comp_tier))
        qual_tier_str = getattr(qual_tier, "value", str(qual_tier))

        from datetime import datetime, timezone
        record = {
            "game_id": game_id,
            "boxscore_available": boxscore_available,
            "pbp_available": pbp_available,
            "video_available": video_available,
            "shot_chart_available": shot_chart_available,
            "boxscore_file_path": boxscore_path,
            "pbp_file_path": pbp_path,
            "video_file_path": video_path,
            "validation_status": val_status_str,
            "completeness_score": comp_tier_str,
            "overall_quality": qual_tier_str,
            "updated_at": datetime.now(timezone.utc),
        }
        self.conn.execute("DELETE FROM game_sources WHERE game_id = ?", [game_id])
        self.insert_records("game_sources", [record])

    def export_all_to_parquet(self, output_dir: Optional[Union[str, Path]] = None) -> Dict[str, str]:
        """Export all non-empty tables to Parquet files in the normalized data directory."""
        out_dir = Path(output_dir or (Settings.ROOT_DIR / "data" / "normalized"))
        out_dir.mkdir(parents=True, exist_ok=True)
        
        tables = [
            "competition", "season", "team", "player", "player_team", "game",
            "game_sources", "source_provenance", "game_roster", "boxscore_team",
            "boxscore_player", "pbp_event", "shot", "lineup_stint", "video",
            "video_event_sync", "entity_alias", "source_conflict_log", "validation_log"
        ]
        
        exported = {}
        for t in tables:
            if self.table_exists(t) and self.get_table_count(t) > 0:
                target_file = out_dir / f"{t}.parquet"
                self.export_to_parquet(t, target_file)
                exported[t] = str(target_file.as_posix())
        return exported

    def clear_tables(self):
        """Truncate all data tables (useful for isolated tests)."""
        tables = [
            "validation_log", "source_conflict_log", "entity_alias", "video_event_sync",
            "video", "lineup_stint", "shot", "pbp_event", "boxscore_player",
            "boxscore_team", "game_roster", "source_provenance", "game_sources",
            "game", "player_team", "player", "team", "season", "competition"
        ]
        for t in tables:
            if self.table_exists(t):
                self.conn.execute(f"DELETE FROM {t}")
