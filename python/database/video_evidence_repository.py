"""DuckDB Persistence Repository for Video Evidence & Clip Reference Layer.

Manages relational persistence for:
- Video recordings & technical metadata
- VideoEvidence clip entities with sub-second temporal boundaries
- Coach notes with attached evidence references
- Player development objectives with attached evidence references

Strictly follows project DuckDB conventions and ensures zero disruption to existing data.
"""

import json
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import duckdb
from python.database.duckdb_manager import DuckDBManager

logger = logging.getLogger("falcons.video.repository")


def get_utc_now() -> datetime:
    return datetime.now(timezone.utc)


class VideoEvidenceRepository:
    """Manages transactional DuckDB storage for the Video Evidence Layer."""

    def __init__(self, db_manager: Optional[DuckDBManager] = None):
        self.db_manager = db_manager or DuckDBManager(read_only=False)
        if not getattr(self.db_manager, 'read_only', False):
            try:
                self._init_tables()
            except Exception:
                pass

    @property
    def conn(self) -> duckdb.DuckDBPyConnection:
        return self.db_manager.conn

    def _init_tables(self):
        """Ensures all video, evidence, note, and objective tables exist with compatible schema."""
        con = self.conn
        if con is None:
            return

        # 1. Extend existing 'video' table if necessary
        try:
            con.execute("ALTER TABLE video ADD COLUMN IF NOT EXISTS filename VARCHAR;")
            con.execute("ALTER TABLE video ADD COLUMN IF NOT EXISTS analysis_focus VARCHAR;")
            con.execute("ALTER TABLE video ADD COLUMN IF NOT EXISTS notes VARCHAR;")
            con.execute("ALTER TABLE video ADD COLUMN IF NOT EXISTS processing_status VARCHAR DEFAULT 'READY';")
            con.execute("ALTER TABLE video ADD COLUMN IF NOT EXISTS readiness_status VARCHAR DEFAULT 'READY';")
            con.execute("ALTER TABLE video ADD COLUMN IF NOT EXISTS audio_present BOOLEAN DEFAULT TRUE;")
            con.execute("ALTER TABLE video ADD COLUMN IF NOT EXISTS created_by VARCHAR DEFAULT 'Staff';")
        except Exception:
            pass

        # 2. First-class VideoEvidence table
        con.execute("""
            CREATE TABLE IF NOT EXISTS video_evidence (
                evidence_id VARCHAR PRIMARY KEY,
                video_id VARCHAR NOT NULL,
                game_id VARCHAR NOT NULL,
                start_time_s DOUBLE NOT NULL,
                end_time_s DOUBLE NOT NULL,
                title VARCHAR NOT NULL,
                category VARCHAR NOT NULL,
                subcategory VARCHAR,
                tags VARCHAR,
                description VARCHAR,
                player_ids VARCHAR,
                team_id VARCHAR,
                source VARCHAR NOT NULL DEFAULT 'Coach',
                confidence DOUBLE,
                review_status VARCHAR NOT NULL DEFAULT 'CONFIRMED',
                created_by VARCHAR NOT NULL DEFAULT 'Coach',
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 3. Coach Notes table with attached evidence IDs
        con.execute("""
            CREATE TABLE IF NOT EXISTS coach_note (
                note_id VARCHAR PRIMARY KEY,
                author VARCHAR NOT NULL DEFAULT 'Coach',
                player_id VARCHAR,
                team_id VARCHAR,
                game_id VARCHAR,
                title VARCHAR NOT NULL,
                content VARCHAR NOT NULL,
                category VARCHAR,
                evidence_ids VARCHAR,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 4. Player Development Objectives table with attached evidence IDs
        con.execute("""
            CREATE TABLE IF NOT EXISTS player_development_objective (
                objective_id VARCHAR PRIMARY KEY,
                player_id VARCHAR NOT NULL,
                title VARCHAR NOT NULL,
                category VARCHAR NOT NULL,
                target_description VARCHAR NOT NULL,
                status VARCHAR NOT NULL DEFAULT 'IN_PROGRESS',
                evidence_ids VARCHAR,
                created_by VARCHAR NOT NULL DEFAULT 'Coach',
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
        """)

    # --------------------------------------------------------------------------
    # MATCH & GAME MANAGEMENT
    # --------------------------------------------------------------------------
    def register_match_if_not_exists(
        self,
        game_id: str,
        home_team_id: str,
        away_team_id: str,
        game_date: str,
        game_type: str = "OFFICIAL",
        season_id: str = "SEA_DEMO_2025",
        competition_id: str = "CMP_DEMO_U16",
        venue: Optional[str] = None,
        home_score: int = 0,
        away_score: int = 0,
    ) -> str:
        """Registers a game record if it does not yet exist.
        
        Strictly preserves game_type (OFFICIAL, PRACTICE, FRIENDLY, SCRIMMAGE, OTHER)
        to respect mathematical population isolation.
        """
        # Ensure competition, season, and team foreign keys exist
        try:
            self.conn.execute(f"""
                INSERT INTO competition (competition_id, name, age_category, country, governing_body, created_at)
                VALUES ('{competition_id}', '{competition_id}', 'U16', 'DEU', 'DBB', CURRENT_TIMESTAMP)
                ON CONFLICT DO NOTHING;
            """)
        except Exception:
            pass

        try:
            self.conn.execute(f"""
                INSERT INTO season (season_id, competition_id, name)
                VALUES ('{season_id}', '{competition_id}', '{season_id}')
                ON CONFLICT DO NOTHING;
            """)
        except Exception:
            pass

        for tid in [home_team_id, away_team_id]:
            try:
                t_name = "Neckar Wolves" if "NECKAR_WOLVES" in tid else ("Rheinland Falcons Basketball" if "2048" in tid else tid.replace("TEM_", "").replace("_", " "))
                self.conn.execute(f"""
                    INSERT INTO team (team_id, canonical_name, short_name, club_name, age_category, created_at)
                    VALUES ('{tid}', '{t_name}', '{tid[:6]}', '{t_name}', 'U16', CURRENT_TIMESTAMP)
                    ON CONFLICT DO NOTHING;
                """)
            except Exception:
                pass

        try:
            existing = self.conn.execute(f"SELECT game_id FROM game WHERE game_id = '{game_id}'").fetchone()
            if existing:
                return existing[0]

            self.conn.execute(f"""
                INSERT INTO game (
                    game_id, season_id, competition_id, game_date,
                    round_number, home_team_id, away_team_id, venue,
                    periods_played, home_score, away_score, game_status, game_type
                ) VALUES (
                    '{game_id}', '{season_id}', '{competition_id}', '{game_date}',
                    1, '{home_team_id}', '{away_team_id}', '{venue or "Main Arena"}',
                    4, {home_score}, {away_score}, 'FINAL', '{game_type.upper()}'
                );
            """)

            # Ensure game_sources row exists
            self.conn.execute(f"""
                INSERT INTO game_sources (
                    game_id, boxscore_available, pbp_available, video_available, shot_chart_available,
                    validation_status, completeness_score, overall_quality, updated_at
                ) VALUES (
                    '{game_id}', FALSE, FALSE, TRUE, FALSE,
                    'PASS', 'PARTIAL', 'MEDIUM', CURRENT_TIMESTAMP
                ) ON CONFLICT (game_id) DO UPDATE SET video_available = TRUE, updated_at = CURRENT_TIMESTAMP;
            """)
            logger.info("Match registered in DB: %s (%s vs %s, type=%s, date=%s)", game_id, home_team_id, away_team_id, game_type, game_date)
        except Exception as e:
            logger.error("Failed to register match: %s", e)

        return game_id

    # --------------------------------------------------------------------------
    # VIDEO RECORDINGS
    # --------------------------------------------------------------------------
    def register_video(self, video_data: Dict[str, Any]) -> str:
        """Inserts or updates a Video recording record."""
        video_id = video_data.get("video_id") or f"VID_{uuid.uuid4().hex[:10].upper()}"
        game_id = video_data["game_id"]
        file_path = video_data["file_path"]
        filename = video_data.get("filename") or Path(file_path).name
        duration_s = float(video_data.get("duration_seconds") or 0.0)
        container = video_data.get("container_format") or "MP4"
        codec = video_data.get("codec") or "h264"
        w = int(video_data.get("resolution_width") or 1920)
        h = int(video_data.get("resolution_height") or 1080)
        fps = float(video_data.get("fps") or 25.0)
        f_size = int(video_data.get("file_size_bytes") or 0)
        sha256 = video_data.get("checksum_sha256") or "UNVERIFIED"
        c_angle = video_data.get("camera_angle") or "Tactical High"
        focus_list = video_data.get("analysis_focus") or []
        focus_str = json.dumps(focus_list) if isinstance(focus_list, list) else str(focus_list)
        notes = (video_data.get("notes") or "").replace("'", "''")
        proc_status = video_data.get("processing_status") or "READY"
        read_status = video_data.get("readiness_status") or "READY"
        audio_pres = bool(video_data.get("audio_present", True))
        created_by = (video_data.get("created_by") or "Coach Staff").replace("'", "''")

        # Upsert Video
        self.conn.execute(f"""
            DELETE FROM video WHERE video_id = '{video_id}';
            INSERT INTO video (
                video_id, game_id, file_path, filename, duration_seconds,
                container_format, codec, resolution_width, resolution_height,
                fps, file_size_bytes, checksum_sha256, camera_angle,
                analysis_focus, notes, processing_status, readiness_status,
                audio_present, created_by, ingestion_timestamp
            ) VALUES (
                '{video_id}', '{game_id}', '{file_path.replace("'", "''")}', '{filename.replace("'", "''")}',
                {duration_s}, '{container}', '{codec}', {w}, {h},
                {fps}, {f_size}, '{sha256}', '{c_angle}',
                '{focus_str.replace("'", "''")}', '{notes}', '{proc_status}', '{read_status}',
                {audio_pres}, '{created_by}', CURRENT_TIMESTAMP
            );
        """)

        # Mark game_sources
        self.conn.execute(f"""
            UPDATE game_sources
            SET video_available = TRUE, video_file_path = '{file_path.replace("'", "''")}', updated_at = CURRENT_TIMESTAMP
            WHERE game_id = '{game_id}';
        """)

        logger.info("Video registered in DB: %s (game: %s, file: '%s', %.1fs, %dx%d, fps=%.1f)", video_id, game_id, filename, duration_s, w, h, fps)
        return video_id

    def get_video(self, video_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves a video record by its unique ID."""
        df = self.conn.execute(f"SELECT * FROM video WHERE video_id = '{video_id}'").df()
        if df.empty:
            return None
        row = df.iloc[0].to_dict()
        if "analysis_focus" in row and isinstance(row["analysis_focus"], str):
            try:
                row["analysis_focus"] = json.loads(row["analysis_focus"])
            except Exception:
                row["analysis_focus"] = [row["analysis_focus"]] if row["analysis_focus"] else []
        return row

    def get_videos_for_game(self, game_id: str) -> List[Dict[str, Any]]:
        """Retrieves all videos associated with a specific match."""
        df = self.conn.execute(f"SELECT * FROM video WHERE game_id = '{game_id}' ORDER BY ingestion_timestamp DESC").df()
        if df.empty:
            return []
        records = df.to_dict(orient="records")
        for r in records:
            if "analysis_focus" in r and isinstance(r["analysis_focus"], str):
                try:
                    r["analysis_focus"] = json.loads(r["analysis_focus"])
                except Exception:
                    r["analysis_focus"] = [r["analysis_focus"]] if r["analysis_focus"] else []
        return records

    def get_all_videos(self) -> List[Dict[str, Any]]:
        """Retrieves all registered videos."""
        df = self.conn.execute("SELECT * FROM video ORDER BY ingestion_timestamp DESC").df()
        if df.empty:
            return []
        records = df.to_dict(orient="records")
        for r in records:
            if "analysis_focus" in r and isinstance(r["analysis_focus"], str):
                try:
                    r["analysis_focus"] = json.loads(r["analysis_focus"])
                except Exception:
                    r["analysis_focus"] = [r["analysis_focus"]] if r["analysis_focus"] else []
        return records

    def delete_video(self, video_id: str) -> bool:
        """Deletes video and all attached clips."""
        try:
            self.conn.execute(f"DELETE FROM video_evidence WHERE video_id = '{video_id}';")
            self.conn.execute(f"DELETE FROM video WHERE video_id = '{video_id}';")
            return True
        except Exception as e:
            print(f"[ERROR] Delete video failed: {e}")
            return False

    # --------------------------------------------------------------------------
    # VIDEO EVIDENCE / CLIPS
    # --------------------------------------------------------------------------
    def create_evidence(self, evidence_data: Dict[str, Any]) -> str:
        """Creates an atomic VideoEvidence entity."""
        evidence_id = evidence_data.get("evidence_id") or f"EVD_{uuid.uuid4().hex[:10].upper()}"
        video_id = evidence_data["video_id"]
        game_id = evidence_data["game_id"]
        start_s = float(evidence_data["start_time_s"])
        end_s = float(evidence_data["end_time_s"])
        title = (evidence_data["title"] or "Match Clip").replace("'", "''")
        category = (evidence_data.get("category") or "General").replace("'", "''")
        subcategory = (evidence_data.get("subcategory") or "").replace("'", "''")
        
        tags_raw = evidence_data.get("tags") or []
        tags_str = ",".join(tags_raw) if isinstance(tags_raw, list) else str(tags_raw)
        
        p_ids_raw = evidence_data.get("player_ids") or []
        p_ids_str = ",".join(p_ids_raw) if isinstance(p_ids_raw, list) else str(p_ids_raw)

        desc = (evidence_data.get("description") or "").replace("'", "''")
        team_id = evidence_data.get("team_id")
        team_id_sql = f"'{team_id}'" if team_id else "NULL"
        source = (evidence_data.get("source") or "Coach").replace("'", "''")
        conf = evidence_data.get("confidence")
        conf_sql = f"{float(conf)}" if conf is not None else "NULL"
        review_st = (evidence_data.get("review_status") or ("CONFIRMED" if source == "Coach" else "PENDING_REVIEW")).replace("'", "''")
        created_by = (evidence_data.get("created_by") or "Coach").replace("'", "''")

        self.conn.execute(f"""
            INSERT INTO video_evidence (
                evidence_id, video_id, game_id, start_time_s, end_time_s,
                title, category, subcategory, tags, description,
                player_ids, team_id, source, confidence, review_status,
                created_by, created_at
            ) VALUES (
                '{evidence_id}', '{video_id}', '{game_id}', {start_s}, {end_s},
                '{title}', '{category}', '{subcategory}', '{tags_str.replace("'", "''")}', '{desc}',
                '{p_ids_str.replace("'", "''")}', {team_id_sql}, '{source}', {conf_sql}, '{review_st}',
                '{created_by}', CURRENT_TIMESTAMP
            );
        """)
        logger.info("VideoEvidence clip registered: %s [%.1fs - %.1fs] '%s' (video: %s, category: %s)", evidence_id, start_s, end_s, title, video_id, category)

        return evidence_id

    def get_evidence(self, evidence_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves a single VideoEvidence entity with enriched video and game metadata."""
        query = f"""
            SELECT 
                ve.*,
                v.file_path,
                v.filename,
                v.duration_seconds as video_duration_seconds,
                v.resolution_width,
                v.resolution_height,
                g.game_date,
                g.game_type,
                t1.canonical_name as home_team_name,
                t2.canonical_name as away_team_name
            FROM video_evidence ve
            JOIN video v ON ve.video_id = v.video_id
            JOIN game g ON ve.game_id = g.game_id
            LEFT JOIN team t1 ON g.home_team_id = t1.team_id
            LEFT JOIN team t2 ON g.away_team_id = t2.team_id
            WHERE ve.evidence_id = '{evidence_id}'
        """
        df = self.conn.execute(query).df()
        if df.empty:
            return None
        rec = df.iloc[0].to_dict()
        rec["tags"] = [t.strip() for t in rec["tags"].split(",") if t.strip()] if rec.get("tags") else []
        rec["player_ids"] = [p.strip() for p in rec["player_ids"].split(",") if p.strip()] if rec.get("player_ids") else []
        return rec

    def get_evidence_for_game(self, game_id: str) -> List[Dict[str, Any]]:
        """Retrieves all evidence clips recorded for a match."""
        query = f"""
            SELECT 
                ve.*,
                v.file_path,
                v.filename,
                v.duration_seconds as video_duration_seconds
            FROM video_evidence ve
            JOIN video v ON ve.video_id = v.video_id
            WHERE ve.game_id = '{game_id}'
            ORDER BY ve.start_time_s ASC
        """
        df = self.conn.execute(query).df()
        if df.empty:
            return []
        records = df.to_dict(orient="records")
        for r in records:
            r["tags"] = [t.strip() for t in r["tags"].split(",") if t.strip()] if r.get("tags") else []
            r["player_ids"] = [p.strip() for p in r["player_ids"].split(",") if p.strip()] if r.get("player_ids") else []
        return records

    def get_evidence_for_player(self, player_id: str) -> List[Dict[str, Any]]:
        """Retrieves all evidence clips where the player is tagged."""
        query = f"""
            SELECT 
                ve.*,
                v.file_path,
                v.filename,
                v.duration_seconds as video_duration_seconds,
                g.game_date,
                g.game_type,
                t1.canonical_name as home_team_name,
                t2.canonical_name as away_team_name
            FROM video_evidence ve
            JOIN video v ON ve.video_id = v.video_id
            JOIN game g ON ve.game_id = g.game_id
            LEFT JOIN team t1 ON g.home_team_id = t1.team_id
            LEFT JOIN team t2 ON g.away_team_id = t2.team_id
            WHERE ve.player_ids LIKE '%{player_id}%'
            ORDER BY g.game_date DESC, ve.start_time_s ASC
        """
        df = self.conn.execute(query).df()
        if df.empty:
            return []
        records = df.to_dict(orient="records")
        for r in records:
            r["tags"] = [t.strip() for t in r["tags"].split(",") if t.strip()] if r.get("tags") else []
            r["player_ids"] = [p.strip() for p in r["player_ids"].split(",") if p.strip()] if r.get("player_ids") else []
        return records

    def get_evidence_by_ids(self, evidence_ids: List[str]) -> List[Dict[str, Any]]:
        """Retrieves multiple VideoEvidence entities by their surrogate IDs."""
        if not evidence_ids:
            return []
        ids_sql = ", ".join(f"'{eid}'" for eid in evidence_ids if eid)
        if not ids_sql:
            return []
        query = f"""
            SELECT 
                ve.*,
                v.file_path,
                v.filename,
                v.duration_seconds as video_duration_seconds,
                g.game_date,
                g.game_type,
                t1.canonical_name as home_team_name,
                t2.canonical_name as away_team_name
            FROM video_evidence ve
            JOIN video v ON ve.video_id = v.video_id
            JOIN game g ON ve.game_id = g.game_id
            LEFT JOIN team t1 ON g.home_team_id = t1.team_id
            LEFT JOIN team t2 ON g.away_team_id = t2.team_id
            WHERE ve.evidence_id IN ({ids_sql})
            ORDER BY ve.start_time_s ASC
        """
        df = self.conn.execute(query).df()
        if df.empty:
            return []
        records = df.to_dict(orient="records")
        for r in records:
            r["tags"] = [t.strip() for t in r["tags"].split(",") if t.strip()] if r.get("tags") else []
            r["player_ids"] = [p.strip() for p in r["player_ids"].split(",") if p.strip()] if r.get("player_ids") else []
        return records

    def update_evidence(self, evidence_id: str, updates: Dict[str, Any]) -> bool:
        """Updates fields of a VideoEvidence entity (e.g. coach confirmation, notes)."""
        set_clauses = []
        for k, v in updates.items():
            if k in ["title", "category", "subcategory", "description", "review_status", "source"]:
                safe_val = str(v).replace("'", "''")
                set_clauses.append(f"{k} = '{safe_val}'")
            elif k in ["start_time_s", "end_time_s", "confidence"]:
                if v is not None:
                    set_clauses.append(f"{k} = {float(v)}")
            elif k in ["tags", "player_ids"]:
                joined = ",".join(v) if isinstance(v, list) else str(v)
                set_clauses.append(f"{k} = '{joined.replace("'", "''")}'")

        if not set_clauses:
            return False

        try:
            self.conn.execute(f"UPDATE video_evidence SET {', '.join(set_clauses)} WHERE evidence_id = '{evidence_id}';")
            return True
        except Exception as e:
            print(f"[ERROR] Update evidence failed: {e}")
            return False

    def delete_evidence(self, evidence_id: str) -> bool:
        """Deletes a VideoEvidence entity."""
        try:
            self.conn.execute(f"DELETE FROM video_evidence WHERE evidence_id = '{evidence_id}';")
            return True
        except Exception as e:
            print(f"[ERROR] Delete evidence failed: {e}")
            return False

    # --------------------------------------------------------------------------
    # COACH NOTES WITH EVIDENCE REFERENCES
    # --------------------------------------------------------------------------
    def create_coach_note(self, note_data: Dict[str, Any]) -> str:
        """Creates a coach note referencing one or more evidence IDs."""
        note_id = note_data.get("note_id") or f"NOT_{uuid.uuid4().hex[:10].upper()}"
        author = (note_data.get("author") or "Coach").replace("'", "''")
        p_id = f"'{note_data['player_id']}'" if note_data.get("player_id") else "NULL"
        t_id = f"'{note_data['team_id']}'" if note_data.get("team_id") else "NULL"
        g_id = f"'{note_data['game_id']}'" if note_data.get("game_id") else "NULL"
        title = (note_data.get("title") or "Coach Note").replace("'", "''")
        content = (note_data.get("content") or "").replace("'", "''")
        cat = (note_data.get("category") or "Tactical").replace("'", "''")
        
        ev_ids_raw = note_data.get("evidence_ids") or []
        ev_ids_str = ",".join(ev_ids_raw) if isinstance(ev_ids_raw, list) else str(ev_ids_raw)

        self.conn.execute(f"""
            INSERT INTO coach_note (
                note_id, author, player_id, team_id, game_id,
                title, content, category, evidence_ids, created_at, updated_at
            ) VALUES (
                '{note_id}', '{author}', {p_id}, {t_id}, {g_id},
                '{title}', '{content}', '{cat}', '{ev_ids_str.replace("'", "''")}',
                CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
            );
        """)
        logger.info("Coach note created: %s '%s' (player=%s, attached_evidences=%s)", note_id, title, note_data.get('player_id'), ev_ids_str)
        return note_id

    def get_coach_notes(
        self,
        player_id: Optional[str] = None,
        game_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Retrieves coach notes filtered by player or game."""
        where_clauses = []
        if player_id:
            where_clauses.append(f"player_id = '{player_id}'")
        if game_id:
            where_clauses.append(f"game_id = '{game_id}'")
        where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

        df = self.conn.execute(f"SELECT * FROM coach_note {where_sql} ORDER BY created_at DESC").df()
        if df.empty:
            return []
        records = df.to_dict(orient="records")
        for r in records:
            r["evidence_ids"] = [e.strip() for e in r["evidence_ids"].split(",") if e.strip()] if r.get("evidence_ids") else []
        return records

    def delete_coach_note(self, note_id: str) -> bool:
        """Deletes a coach note."""
        try:
            self.conn.execute(f"DELETE FROM coach_note WHERE note_id = '{note_id}';")
            return True
        except Exception:
            return False

    # --------------------------------------------------------------------------
    # PLAYER DEVELOPMENT OBJECTIVES WITH EVIDENCE REFERENCES
    # --------------------------------------------------------------------------
    def create_development_objective(self, obj_data: Dict[str, Any]) -> str:
        """Creates a player development objective referencing attached video evidence IDs."""
        obj_id = obj_data.get("objective_id") or f"OBJ_{uuid.uuid4().hex[:10].upper()}"
        player_id = obj_data["player_id"]
        title = (obj_data.get("title") or "Development Goal").replace("'", "''")
        category = (obj_data.get("category") or "Defense").replace("'", "''")
        target_desc = (obj_data.get("target_description") or "").replace("'", "''")
        status = (obj_data.get("status") or "IN_PROGRESS").replace("'", "''")
        created_by = (obj_data.get("created_by") or "Coach Staff").replace("'", "''")

        ev_ids_raw = obj_data.get("evidence_ids") or []
        ev_ids_str = ",".join(ev_ids_raw) if isinstance(ev_ids_raw, list) else str(ev_ids_raw)

        self.conn.execute(f"""
            INSERT INTO player_development_objective (
                objective_id, player_id, title, category, target_description,
                status, evidence_ids, created_by, created_at, updated_at
            ) VALUES (
                '{obj_id}', '{player_id}', '{title}', '{category}', '{target_desc}',
                '{status}', '{ev_ids_str.replace("'", "''")}', '{created_by}',
                CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
            );
        """)
        logger.info("Player development objective created: %s '%s' (player=%s, status=%s, attached_evidences=%s)", obj_id, title, player_id, status, ev_ids_str)
        return obj_id

    def get_development_objectives(self, player_id: str) -> List[Dict[str, Any]]:
        """Retrieves development objectives for a player."""
        df = self.conn.execute(f"SELECT * FROM player_development_objective WHERE player_id = '{player_id}' ORDER BY created_at DESC").df()
        if df.empty:
            return []
        records = df.to_dict(orient="records")
        for r in records:
            r["evidence_ids"] = [e.strip() for e in r["evidence_ids"].split(",") if e.strip()] if r.get("evidence_ids") else []
        return records

    def attach_evidence_to_objective(self, objective_id: str, evidence_id: str) -> bool:
        """Appends an evidence_id to a player's development objective."""
        try:
            df = self.conn.execute(f"SELECT evidence_ids FROM player_development_objective WHERE objective_id = '{objective_id}'").df()
            if df.empty:
                return False
            curr = df.iloc[0]["evidence_ids"] or ""
            existing = [e.strip() for e in curr.split(",") if e.strip()]
            if evidence_id not in existing:
                existing.append(evidence_id)
                new_str = ",".join(existing).replace("'", "''")
                self.conn.execute(f"UPDATE player_development_objective SET evidence_ids = '{new_str}', updated_at = CURRENT_TIMESTAMP WHERE objective_id = '{objective_id}';")
            return True
        except Exception as e:
            print(f"[ERROR] Attach evidence failed: {e}")
            return False

    def delete_development_objective(self, objective_id: str) -> bool:
        """Deletes a development objective."""
        try:
            self.conn.execute(f"DELETE FROM player_development_objective WHERE objective_id = '{objective_id}';")
            return True
        except Exception:
            return False
