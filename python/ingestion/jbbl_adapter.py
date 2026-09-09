"""JBBL Real-Match Ingestion Adapter for SCB REST & Socket.IO Payloads."""

import json
import re
from datetime import datetime, timezone, date
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from python.ingestion.base import BaseAdapter, NormalizedPayload
from python.ingestion.entity_resolver import EntityResolver
from python.ingestion.provenance import ProvenanceTracker, generate_id
from python.models.canonical import (
    Competition,
    Season,
    Team,
    Player,
    PlayerTeam,
    Game,
    GameRoster,
    BoxscoreTeam,
    BoxscorePlayer,
    PBPEvent,
    Shot,
    LineupStint,
    EntityAlias,
    SourceProvenance,
)
from python.models.enums import (
    ObservationStatus,
    EventType,
    ShotType,
    PeriodType,
    SourceType,
    ReconstructionMethod,
    ConfidenceStatus,
)

# SCB Protocol Mappings
k = {0:"scorelist",1:"action",2:"team",3:"time_event",4:"player_stats",5:"scorelist_delete",6:"action_delete",7:"starting_five",8:"delete_player",20:"history_end"}
K = {1:"q1",2:"q2",3:"q3",4:"q4",5:"ot1",6:"ot2",7:"ot3",8:"ot4"}
at = {0:"JB",1:"JS",2:"FT",3:"P2",4:"P3",5:"FOUL",6:"RFOUL",7:"REB",8:"TREB",9:"TO",10:"ST",11:"BL",12:"TIMEO",13:"SUBST",14:"CFOUL",15:"TTO"}
ct = {0:"D",1:"O",2:"P",3:"T",4:"U",5:"Q",6:"C",7:"P",8:"1",9:"2",10:"3",11:"LB",12:"BP",13:"OB",14:"TR",15:"VI",16:"5",17:"8",18:"24",19:"E"}
ht = {0:0,1:1,2:2,3:3,4:4,5:5,6:"SC",7:"FB",8:"TO",9:"FT",10:"ST",11:"SF",12:"AL",51:"JS",52:"LU",53:"DU",54:"AO",55:"TI"}
ut = {0:"-",1:"+",2:"BL"}
P = {1:"A",2:"B","1":"A","2":"B"}
ft = {0:"N",1:"S","0":"N","1":"S"}

pt = {
    0: {"objects":["type","id","quarter","time","points_1","points_2"], "mappings":{0:k,2:K}},
    1: {"objects":["type","id","quarter","teamcode","player_id1","player_id2","time","player_nr1","player_nr2","action","info1","info2","info3","result","points1","points2","x","y"], "mappings":{0:k,2:K,3:P,9:at,10:ct,12:ht,13:ut}},
    2: {"objects":["type","id","teamcode","FT_points","FT_attempts","FT_rate","P2_points","P2_attempts","P2_rate","P3_points","P3_attempts","P3_rate","FOUL_nr","REBD_nr","REBO_nr","BL_nr","ST_nr","TO_nr","index1","index2","team_foul_nr"], "mappings":{0:k,2:P}},
    3: {"objects":["type","id","quarter","time","action","points1","points2"], "mappings":{0:k,2:K}},
    4: {"objects":["type","id","teamcode","player_id","playcode","player_nr","points","FT_points","FT_attempts","FT_rate","P2_points","P2_attempts","p2_rate","P3_points","P3_attempts","P3_rate","FOUL_nr","REB_nr","ASSIST_nr","BL_nr","ST_nr","TO_nr","index1","index2","time_s"], "mappings":{0:k,2:P,4:ft}},
    7: {"objects":["type","quarter","teamcode","player_id1","player_id2","player_id3","player_id4","player_id5"], "mappings":{0:k,2:P}},
    20: {"objects":["type"], "mappings":{0:k}},
}

EVENT_TYPE_MAP = {
    "JB": EventType.JUMP_BALL,
    "JS": EventType.SHOT,
    "FT": EventType.FREE_THROW,
    "P2": EventType.SHOT,
    "P3": EventType.SHOT,
    "FOUL": EventType.FOUL,
    "RFOUL": EventType.FOUL,
    "REB": EventType.REBOUND,
    "TREB": EventType.REBOUND,
    "TO": EventType.TURNOVER,
    "ST": EventType.TURNOVER,
    "BL": EventType.SHOT,
    "TIMEO": EventType.TIMEOUT,
    "SUBST": EventType.SUB,
    "CFOUL": EventType.FOUL,
    "TTO": EventType.TIMEOUT,
}


class JBBLAdapter(BaseAdapter):
    """Adapter for real JBBL multi-source match extractions (REST + Socket.IO)."""

    def __init__(
        self,
        entity_resolver: Optional[EntityResolver] = None,
        provenance_tracker: Optional[ProvenanceTracker] = None,
    ):
        super().__init__(entity_resolver, provenance_tracker)

    def detect(self, file_path: Union[str, Path]) -> bool:
        """Detects if directory or file contains JBBL raw SCB artifacts."""
        p = Path(file_path)
        if p.is_dir():
            return (p / "raw_game_header.json").exists() or any(p.glob("raw_socket_stream*"))
        return "raw_game_header" in p.name or "raw_socket_stream" in p.name

    def extract(self, raw_dir: Union[str, Path]) -> Dict[str, Any]:
        """Loads and parses all raw payload files from a game raw directory."""
        dir_path = Path(raw_dir)
        header_file = dir_path / "raw_game_header.json"
        
        # Find stream file
        stream_files = list(dir_path.glob("raw_socket_stream*"))
        if not header_file.exists() or not stream_files:
            raise FileNotFoundError(f"Missing required raw files in {raw_dir}")

        stream_file = stream_files[0]
        manifest_file = dir_path / "raw_provenance_manifest.json"

        header_data = json.loads(header_file.read_text(encoding="utf-8"))
        stream_text = stream_file.read_text(encoding="utf-8")
        manifest_data = json.loads(manifest_file.read_text(encoding="utf-8")) if manifest_file.exists() else {}

        # Decode Socket.IO stream
        raw_arrays = re.findall(r'42\[\d+,\s*(\[[^\]]+\])\]', stream_text)
        decoded_stream = {
            "team_stats": [],
            "player_stats": [],
            "actions": [],
            "time_events": [],
            "scorelist": [],
            "starting_five": [],
        }

        for s in raw_arrays:
            try:
                arr = json.loads(s)
                type_id = arr[0]
                schema = pt.get(type_id)
                if not schema:
                    continue
                res = {}
                for idx, key in enumerate(schema["objects"]):
                    val = arr[idx] if idx < len(arr) else None
                    mapping = schema["mappings"].get(idx)
                    if mapping and val in mapping:
                        res[key] = mapping[val]
                    else:
                        res[key] = val
                
                t = res.get("type")
                if t == "team": decoded_stream["team_stats"].append(res)
                elif t == "player_stats": decoded_stream["player_stats"].append(res)
                elif t == "action": decoded_stream["actions"].append(res)
                elif t == "time_event": decoded_stream["time_events"].append(res)
                elif t == "scorelist": decoded_stream["scorelist"].append(res)
                elif t == "starting_five": decoded_stream["starting_five"].append(res)
            except Exception:
                pass

        return {
            "header": header_data,
            "stream": decoded_stream,
            "manifest": manifest_data,
            "raw_dir": str(dir_path),
            "stream_file": str(stream_file.as_posix()),
        }

    def normalize(
        self,
        raw_data: Dict[str, Any],
        file_path: Union[str, Path],
        game_id: Optional[str] = None,
        season_id: Optional[str] = None,
        competition_id: Optional[str] = None,
    ) -> NormalizedPayload:
        """Transforms extracted raw JBBL match data into Canonical relational entities."""
        header = raw_data["header"]
        stream = raw_data["stream"]
        manifest = raw_data["manifest"]
        stream_path = raw_data.get("stream_file", str(file_path))
        
        # 1. Provenance
        prov = self.provenance_tracker.create_provenance(
            source_type=SourceType.BOXSCORE,
            source_provider="Sporting Code Broadcast (SCB World)",
            source_file_path=stream_path,
            parser_version="jbbl_adapter_v2.0",
        )

        # 2. Competition & Season
        is_nbbl = (competition_id == "CMP_NBBL") or ("nbbl" in str(file_path).lower()) or (header.get("competition") == "NBBL")
        comp_id = competition_id or ("CMP_NBBL" if is_nbbl else "CMP_JBBL")
        age_cat = "U19" if is_nbbl else "U16"
        comp_name = "Nachwuchs-Basketball-Bundesliga (NBBL U19)" if is_nbbl else "Jugend-Basketball-Bundesliga (JBBL U16)"
        seas_prefix = "NBBL" if is_nbbl else "JBBL"
        header_season = header.get("seasonId", 2025)

        competition = Competition(
            competition_id=comp_id,
            name=comp_name,
            gender="MALE",
            age_category=age_cat,
            country="DE",
            governing_body="DBB / BBL",
        )

        seas_id = season_id or f"SEA_{header_season}"
        season = Season(
            season_id=seas_id,
            competition_id=comp_id,
            name=f"{seas_prefix} Season {header_season}",
            start_date=date(header_season - 1, 10, 1) if isinstance(header_season, int) else date(2025, 10, 1),
            end_date=date(header_season, 5, 31) if isinstance(header_season, int) else date(2026, 5, 31),
        )

        # 3. Teams Resolution
        home_raw = header["homeTeam"]
        guest_raw = header["guestTeam"]
        
        home_team_canon_id = f"TEM_{home_raw['id']}"
        guest_team_canon_id = f"TEM_{guest_raw['id']}"
        
        team_home = Team(
            team_id=home_team_canon_id,
            canonical_name=home_raw["name"],
            short_name=home_raw.get("short"),
            club_name=home_raw.get("TLC"),
            age_category=age_cat,
        )
        team_guest = Team(
            team_id=guest_team_canon_id,
            canonical_name=guest_raw["name"],
            short_name=guest_raw.get("short"),
            club_name=guest_raw.get("TLC"),
            age_category=age_cat,
        )

        # 4. Game Entity
        src_game_id = str(header.get("gameId", "9995585"))
        canonical_game_id = game_id or f"GAM_{src_game_id}"
        
        sched_str = header.get("scheduledTime", "2026-03-22T11:30:00Z")
        game_dt = datetime.fromisoformat(sched_str.replace("Z", "+00:00"))
        
        # Calculate official score from team stats or scorelist
        t_a = next((t for t in stream["team_stats"] if t.get("teamcode") == "A"), {})
        t_b = next((t for t in stream["team_stats"] if t.get("teamcode") == "B"), {})
        home_pts = t_a.get("FT_points", 0) + (t_a.get("P2_points", 0) * 2) + (t_a.get("P3_points", 0) * 3)
        away_pts = t_b.get("FT_points", 0) + (t_b.get("P2_points", 0) * 2) + (t_b.get("P3_points", 0) * 3)
        
        # Extract venue string safely
        venue_val = header.get("venue") or header.get("stadium")
        if isinstance(venue_val, dict):
            venue_str = venue_val.get("name") or venue_val.get("city") or "Unknown Venue"
        elif isinstance(venue_val, str):
            venue_str = venue_val
        else:
            venue_str = "FALCONS Arena Rheinland"

        game_entity = Game(
            game_id=canonical_game_id,
            season_id=seas_id,
            competition_id=comp_id,
            game_date=game_dt.date(),
            game_time=game_dt.time().strftime("%H:%M:%S"),
            home_team_id=home_team_canon_id,
            away_team_id=guest_team_canon_id,
            venue=venue_str,
            periods_played=4,
            home_score=home_pts,
            away_score=away_pts,
            game_status="FINAL",
            game_type="OFFICIAL",
        )

        # 5. Players, PlayerTeam, GameRoster & Aliases
        players_dict = {}
        player_teams = []
        game_rosters = []
        aliases = []
        
        roster_to_canon_pid = {}
        playerid_to_canon_pid = {}
        seen_player_teams = set()
        seen_game_rosters = set()

        # Generic placeholder player for unassigned team actions
        players_dict["PLY_UNKNOWN"] = Player(
            player_id="PLY_UNKNOWN",
            canonical_name="Team / Unknown Player",
        )

        for team_raw, team_cid, tcode in [(home_raw, home_team_canon_id, "A"), (guest_raw, guest_team_canon_id, "B")]:
            for p_raw in team_raw.get("roster", []):
                master_pid = p_raw["playerId"]
                roster_id = p_raw["id"]
                canon_pid = f"PLY_{master_pid}"
                
                roster_to_canon_pid[roster_id] = canon_pid
                playerid_to_canon_pid[master_pid] = canon_pid
                
                full_name = f"{p_raw.get('firstName', '')} {p_raw.get('lastName', '')}".strip()
                dob = date.fromisoformat(p_raw["birthDate"]) if p_raw.get("birthDate") else None
                height_cm = round(p_raw["height"] * 100.0, 1) if p_raw.get("height") else None
                nats = ",".join(p_raw.get("nationalities", [])) if p_raw.get("nationalities") else None

                players_dict[canon_pid] = Player(
                    player_id=canon_pid,
                    canonical_name=full_name,
                    first_name=p_raw.get("firstName"),
                    last_name=p_raw.get("lastName"),
                    birth_date=dob,
                    height_cm=height_cm,
                    listed_position=p_raw.get("position"),
                    nationality=nats,
                )

                # PlayerTeam & GameRoster (deduplicated by canonical player ID)
                pt_key = (canon_pid, team_cid, seas_id)
                if pt_key not in seen_player_teams:
                    seen_player_teams.add(pt_key)
                    pt_id = generate_id("PLT")
                    player_teams.append(PlayerTeam(
                        player_team_id=pt_id,
                        player_id=canon_pid,
                        team_id=team_cid,
                        season_id=seas_id,
                        jersey_number=str(p_raw.get("NUM", "")),
                        is_active=True,
                    ))

                gr_key = (canonical_game_id, team_cid, canon_pid)
                if gr_key not in seen_game_rosters:
                    seen_game_rosters.add(gr_key)
                    gr_id = generate_id("ROS")
                    game_rosters.append(GameRoster(
                        game_roster_id=gr_id,
                        game_id=canonical_game_id,
                        team_id=team_cid,
                        player_id=canon_pid,
                        jersey_number=str(p_raw.get("NUM", "")),
                        is_active=True,
                        provenance_id=prov.provenance_id,
                    ))

                # Entity Alias for traceability
                alias_id = generate_id("ALS")
                aliases.append(EntityAlias(
                    alias_id=alias_id,
                    entity_type="PLAYER",
                    canonical_id=canon_pid,
                    source_provider="Sporting Code Broadcast (SCB World)",
                    source_id=str(roster_id),
                    source_name_raw=full_name,
                    normalized_name=full_name.lower(),
                    jersey_number=str(p_raw.get("NUM", "")),
                    match_confidence=1.0,
                    requires_review=False,
                ))

        # Check for unassigned player IDs in stream that weren't in header roster
        for p_stat in stream["player_stats"]:
            p_src = p_stat.get("player_id") or p_stat.get("id")
            if p_src:
                c_pid = roster_to_canon_pid.get(p_src) or playerid_to_canon_pid.get(p_src)
                if not c_pid:
                    c_pid = f"PLY_{p_src}"
                    playerid_to_canon_pid[p_src] = c_pid
                    if c_pid not in players_dict:
                        players_dict[c_pid] = Player(
                            player_id=c_pid,
                            canonical_name=f"Player ID {p_src}",
                        )

        players = list(players_dict.values())

        # Deduplicate stream player stats by (teamcode, canonical_pid) to protect against duplicate federation roster entries
        deduped_player_stats = []
        seen_pstat_keys = set()
        for p_stat in stream["player_stats"]:
            src_pid = p_stat.get("player_id") or p_stat.get("id")
            c_pid = roster_to_canon_pid.get(src_pid) or playerid_to_canon_pid.get(src_pid) or f"PLY_{src_pid}"
            p_key = (p_stat.get("teamcode"), c_pid)
            if p_key not in seen_pstat_keys:
                seen_pstat_keys.add(p_key)
                deduped_player_stats.append(p_stat)

        # 6. Team Boxscores
        boxscore_teams = []
        for t_stat, team_cid, is_home, tcode in [(t_a, home_team_canon_id, True, "A"), (t_b, guest_team_canon_id, False, "B")]:
            if t_stat:
                pts = t_stat.get("FT_points", 0) + (t_stat.get("P2_points", 0) * 2) + (t_stat.get("P3_points", 0) * 3)
                fg2m = t_stat.get("P2_points", 0)
                fg2a = t_stat.get("P2_attempts", 0)
                fg3m = t_stat.get("P3_points", 0)
                fg3a = t_stat.get("P3_attempts", 0)
                ftm = t_stat.get("FT_points", 0)
                fta = t_stat.get("FT_attempts", 0)
                tot_trb = t_stat.get("REBO_nr", 0) + t_stat.get("REBD_nr", 0)
                
                # Calculate team dead-ball / team rebounds (team total minus player sum)
                p_trb_sum = sum(p.get("REB_nr", 0) for p in deduped_player_stats if p.get("teamcode") == tcode)
                team_reb_count = max(0, tot_trb - p_trb_sum)
                
                bt_id = generate_id("BXT")
                boxscore_teams.append(BoxscoreTeam(
                    boxscore_team_id=bt_id,
                    game_id=canonical_game_id,
                    team_id=team_cid,
                    is_home=is_home,
                    points=pts,
                    fgm=fg2m + fg3m,
                    fga=fg2a + fg3a,
                    fg2m=fg2m,
                    fg2a=fg2a,
                    fg3m=fg3m,
                    fg3a=fg3a,
                    ftm=ftm,
                    fta=fta,
                    orb=t_stat.get("REBO_nr", 0),
                    drb=t_stat.get("REBD_nr", 0),
                    trb=tot_trb,
                    ast=None,
                    stl=t_stat.get("ST_nr", 0),
                    blk=t_stat.get("BL_nr", 0),
                    tov=t_stat.get("TO_nr", 0),
                    pf=t_stat.get("FOUL_nr", 0),
                    team_rebounds=team_reb_count,
                    provenance_id=prov.provenance_id,
                ))

        # 7. Player Boxscores
        boxscore_players = []
        for p_stat in deduped_player_stats:
            src_pid = p_stat.get("player_id") or p_stat.get("id")
            canon_pid = roster_to_canon_pid.get(src_pid) or playerid_to_canon_pid.get(src_pid) or f"PLY_{src_pid}"
            tcode = p_stat.get("teamcode")
            team_cid = home_team_canon_id if tcode == "A" else guest_team_canon_id
            
            fg2m = p_stat.get("P2_points", 0)
            fg2a = p_stat.get("P2_attempts", 0)
            fg3m = p_stat.get("P3_points", 0)
            fg3a = p_stat.get("P3_attempts", 0)
            ftm = p_stat.get("FT_points", 0)
            fta = p_stat.get("FT_attempts", 0)
            sec_played = p_stat.get("time_s")

            bxp_id = generate_id("BXP")
            boxscore_players.append(BoxscorePlayer(
                boxscore_player_id=bxp_id,
                game_id=canonical_game_id,
                team_id=team_cid,
                player_id=canon_pid,
                jersey_number=str(p_stat.get("player_nr", "")),
                seconds_played=sec_played,
                points=p_stat.get("points", 0),
                fgm=fg2m + fg3m,
                fga=fg2a + fg3a,
                fg2m=fg2m,
                fg2a=fg2a,
                fg3m=fg3m,
                fg3a=fg3a,
                ftm=ftm,
                fta=fta,
                orb=None,
                drb=None,
                trb=p_stat.get("REB_nr", 0),
                ast=p_stat.get("ASSIST_nr", 0),
                stl=p_stat.get("ST_nr", 0),
                blk=p_stat.get("BL_nr", 0),
                tov=p_stat.get("TO_nr", 0),
                pf=p_stat.get("FOUL_nr", 0),
                is_dnp=(sec_played == 0 and p_stat.get("points", 0) == 0),
                observation_status=ObservationStatus.OBSERVED,
                provenance_id=prov.provenance_id,
            ))

        # 8. PBP Events & Shots
        pbp_events = []
        shots = []
        
        curr_home_score = 0
        curr_away_score = 0

        def parse_quarter_num(q_str: Any) -> int:
            if isinstance(q_str, int): return q_str
            s = str(q_str).lower().replace("q", "").replace("ot", "")
            try: return int(s)
            except Exception: return 1

        for idx, a in enumerate(stream["actions"]):
            q_num = parse_quarter_num(a.get("quarter", 1))
            clock_sec = float(a.get("time", 0))
            game_sec_rem = ((4 - q_num) * 600.0) + clock_sec
            
            mins = int(clock_sec // 60)
            secs = int(clock_sec % 60)
            clock_display = f"{mins:02d}:{secs:02d}"

            act_code = a.get("action")
            event_type = EVENT_TYPE_MAP.get(act_code, EventType.VIOLATION)
            tcode = a.get("teamcode")
            act_team_id = home_team_canon_id if tcode == "A" else (guest_team_canon_id if tcode == "B" else None)
            
            p1_src = a.get("player_id1")
            p2_src = a.get("player_id2")
            p1_canon = roster_to_canon_pid.get(p1_src) or playerid_to_canon_pid.get(p1_src) or (f"PLY_{p1_src}" if p1_src else None)
            p2_canon = roster_to_canon_pid.get(p2_src) or playerid_to_canon_pid.get(p2_src) or (f"PLY_{p2_src}" if p2_src else None)

            res = a.get("result")
            pts_scored = 0
            if res == "+":
                if act_code == "FT": pts_scored = 1
                elif act_code in ["P2", "JS"] or a.get("info2") == 2: pts_scored = 2
                elif act_code == "P3" or a.get("info2") == 3: pts_scored = 3
                
                if tcode == "A":
                    curr_home_score += pts_scored
                elif tcode == "B":
                    curr_away_score += pts_scored

            evt_id = generate_id("PBP")
            pbp_obj = PBPEvent(
                event_id=evt_id,
                game_id=canonical_game_id,
                period=q_num,
                period_type=PeriodType.REGULAR,
                clock_display=clock_display,
                game_seconds_remaining=game_sec_rem,
                period_seconds_remaining=clock_sec,
                event_index=idx + 1,
                event_type=event_type,
                event_subtype=str(a.get("info1")) if a.get("info1") is not None else None,
                team_id=act_team_id,
                player_id=p1_canon,
                secondary_player_id=p2_canon,
                home_score=curr_home_score,
                away_score=curr_away_score,
                score_margin=curr_home_score - curr_away_score,
                points_scored=pts_scored,
                description=f"{act_code} by player {a.get('player_nr1')} (result: {res})",
                provenance_id=prov.provenance_id,
            )
            pbp_events.append(pbp_obj)

            # If event is a field goal shot (P2, P3, JS) -> Create Shot entity
            if act_code in ["P2", "P3", "JS"]:
                stype = ShotType.THREE_POINT if act_code == "P3" else ShotType.TWO_POINT
                x_val = float(a.get("x")) if (a.get("x") is not None and a.get("x") != 0) else None
                y_val = float(a.get("y")) if (a.get("y") is not None and a.get("y") != 0) else None
                loc_status = ObservationStatus.OBSERVED if (x_val is not None and y_val is not None) else ObservationStatus.NOT_AVAILABLE
                
                shot_id = generate_id("SHT")
                shots.append(Shot(
                    shot_id=shot_id,
                    event_id=evt_id,
                    game_id=canonical_game_id,
                    team_id=act_team_id or home_team_canon_id,
                    player_id=p1_canon or "PLY_UNKNOWN",
                    period=q_num,
                    game_seconds_remaining=game_sec_rem,
                    shot_type=stype,
                    shot_subtype=str(a.get("info3")) if a.get("info3") is not None else None,
                    is_made=(res == "+"),
                    points=pts_scored,
                    x_coord=x_val,
                    y_coord=y_val,
                    shot_location_status=loc_status,
                    assisted_by_player_id=p2_canon if (res == "+" and p2_canon != p1_canon) else None,
                    provenance_id=prov.provenance_id,
                ))

        # 9. Lineup Stints
        lineup_stints = []
        for s5 in stream["starting_five"]:
            q_num = parse_quarter_num(s5.get("quarter", 1))
            tcode = s5.get("teamcode")
            team_cid = home_team_canon_id if tcode == "A" else guest_team_canon_id
            
            p_ids_raw = [s5.get(f"player_id{i}") for i in range(1, 6) if s5.get(f"player_id{i}")]
            p_ids_canon = sorted([
                roster_to_canon_pid.get(pid) or playerid_to_canon_pid.get(pid) or f"PLY_{pid}"
                for pid in p_ids_raw
            ])
            
            stint_id = generate_id("STN")
            lineup_stints.append(LineupStint(
                stint_id=stint_id,
                game_id=canonical_game_id,
                team_id=team_cid,
                period=q_num,
                start_game_seconds=((4 - q_num) * 600.0) + 600.0,
                end_game_seconds=((4 - q_num) * 600.0) + 600.0,
                duration_seconds=0.0,
                player_ids=",".join(p_ids_canon),
                is_home=(tcode == "A"),
                points_for=0,
                points_against=0,
                reconstruction_method=ReconstructionMethod.EXACT_SUB_TRACKING,
                confidence_status=ConfidenceStatus.EXACT,
                provenance_id=prov.provenance_id,
            ))

        return NormalizedPayload(
            provenance=prov,
            competitions=[competition],
            seasons=[season],
            teams=[team_home, team_guest],
            players=players,
            player_teams=player_teams,
            games=[game_entity],
            game_rosters=game_rosters,
            boxscore_teams=boxscore_teams,
            boxscore_players=boxscore_players,
            pbp_events=pbp_events,
            shots=shots,
            lineup_stints=lineup_stints,
            aliases=aliases,
        )
