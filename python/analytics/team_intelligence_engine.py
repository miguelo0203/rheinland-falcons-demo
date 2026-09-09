"""Team Intelligence, Observed Lineup Reconstruction & Progressive Quintet Engine.

Rheinland Falcons Rheinland — JBBL / NBBL Basketball Intelligence Platform.

Provides a unified analytical layer supporting two distinct modes:
- MODE A: Observed Lineup Intelligence (Exact PBP on-court 5-man stints, minutes, possessions, Net Rating)
- MODE B: Profile-Based Quintet Intelligence (Statistical complementarity, spacing, role balance, progressive 1->5 builder)
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
import numpy as np
import pandas as pd
import duckdb


class LineupEvidenceTier(str, Enum):
    STRONG_EVIDENCE = "STRONG_EVIDENCE"          # >= 30.0 min
    MODERATE_EVIDENCE = "MODERATE_EVIDENCE"      # 15.0 - 29.9 min
    EMERGING_SIGNAL = "EMERGING_SIGNAL"          # 5.0 - 14.9 min
    INSUFFICIENT_SAMPLE = "INSUFFICIENT_SAMPLE"  # < 5.0 min


@dataclass
class ObservedLineupRecord:
    lineup_key: str
    player_ids: List[str]
    player_names: List[str]
    games_played: int
    stint_count: int
    total_minutes: float
    possessions: float
    points_for: int
    points_against: int
    point_diff: int
    ortg: float
    drtg: float
    net_rtg: float
    efg_pct: float
    tov_pct: float
    orb_pct: float
    ftr: float
    evidence_tier: LineupEvidenceTier

    def to_dict(self) -> Dict[str, Any]:
        return {
            "lineup_key": self.lineup_key,
            "player_ids": self.player_ids,
            "player_names": self.player_names,
            "lineup_display": " + ".join(self.player_names),
            "games_played": self.games_played,
            "stint_count": self.stint_count,
            "total_minutes": round(self.total_minutes, 1),
            "possessions": round(self.possessions, 1),
            "points_for": self.points_for,
            "points_against": self.points_against,
            "point_diff": self.point_diff,
            "ortg": round(self.ortg, 1),
            "drtg": round(self.drtg, 1),
            "net_rtg": round(self.net_rtg, 1),
            "efg_pct": round(self.efg_pct, 1),
            "tov_pct": round(self.tov_pct, 1),
            "orb_pct": round(self.orb_pct, 1),
            "ftr": round(self.ftr, 3),
            "evidence_tier": self.evidence_tier.value,
        }


@dataclass
class QuintetDimensionScores:
    shooting_spacing: float      # 0 - 100
    creation_playmaking: float   # 0 - 100
    rebounding_glass: float      # 0 - 100
    ball_security: float         # 0 - 100
    defensive_profile: float     # 0 - 100
    role_balance: float          # 0 - 100
    overall_fit_index: float     # 0 - 100

    def to_dict(self) -> Dict[str, float]:
        return {
            "shooting_spacing": round(self.shooting_spacing, 1),
            "creation_playmaking": round(self.creation_playmaking, 1),
            "rebounding_glass": round(self.rebounding_glass, 1),
            "ball_security": round(self.ball_security, 1),
            "defensive_profile": round(self.defensive_profile, 1),
            "role_balance": round(self.role_balance, 1),
            "overall_fit_index": round(self.overall_fit_index, 1),
        }


@dataclass
class ProgressiveAdditionDelta:
    added_player_id: str
    added_player_name: str
    delta_fit_index: float
    delta_shooting: float
    delta_creation: float
    delta_rebounding: float
    delta_ball_security: float
    delta_defense: float
    delta_role_balance: float
    tactical_summary: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "added_player_id": self.added_player_id,
            "added_player_name": self.added_player_name,
            "delta_fit_index": round(self.delta_fit_index, 1),
            "delta_shooting": round(self.delta_shooting, 1),
            "delta_creation": round(self.delta_creation, 1),
            "delta_rebounding": round(self.delta_rebounding, 1),
            "delta_ball_security": round(self.delta_ball_security, 1),
            "delta_defense": round(self.delta_defense, 1),
            "delta_role_balance": round(self.delta_role_balance, 1),
            "tactical_summary": self.tactical_summary,
        }


@dataclass
class QuintetProfileSummary:
    player_ids: List[str]
    player_names: List[str]
    count: int
    scores: QuintetDimensionScores
    is_observed: bool
    observed_record: Optional[ObservedLineupRecord] = None
    addition_delta: Optional[ProgressiveAdditionDelta] = None
    strengths: List[str] = field(default_factory=list)
    risks_and_overlaps: List[str] = field(default_factory=list)
    film_hypotheses: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "player_ids": self.player_ids,
            "player_names": self.player_names,
            "count": self.count,
            "scores": self.scores.to_dict(),
            "is_observed": self.is_observed,
            "observed_record": self.observed_record.to_dict() if self.observed_record else None,
            "addition_delta": self.addition_delta.to_dict() if self.addition_delta else None,
            "strengths": self.strengths,
            "risks_and_overlaps": self.risks_and_overlaps,
            "film_hypotheses": self.film_hypotheses,
        }


def _safe_query(conn: Any, sql: str) -> pd.DataFrame:
    try:
        res = conn.execute(sql)
        if res is not None:
            df = res.df() if hasattr(res, "df") else res
            if df is not None:
                return df
    except Exception:
        pass
    return pd.DataFrame()


def _get_player_map(conn: Any) -> Dict[str, str]:
    df = _safe_query(conn, "SELECT player_id, canonical_name FROM player")
    if df is not None and not df.empty and "player_id" in df.columns:
        return df.set_index("player_id")["canonical_name"].to_dict()
    return {}


# ==============================================================================
# MODE A: OBSERVED LINEUP RECONSTRUCTION ENGINE
# ==============================================================================

class LineupReconstructionEngine:
    """Reconstructs exact on-court 5-man stints from starting lineups and substitution streams."""

    @staticmethod
    def reconstruct_stints(conn: Any, season_id: str = "SEA_2025", team_id: str = "TEM_DEMO_U16") -> pd.DataFrame:
        """Reconstructs all 5-man on-court stints across official matches with PBP."""
        # Fetch starting 5s
        df_s5 = _safe_query(conn, f"""
            SELECT game_id, team_id, period, player_ids 
            FROM lineup_stint 
            WHERE team_id = '{team_id}'
        """)

        # Fetch FALCONS games with PBP
        pbp_games = _safe_query(conn, f"""
            SELECT DISTINCT g.game_id, g.game_date
            FROM game g
            JOIN pbp_event p ON g.game_id = p.game_id
            WHERE (g.home_team_id = '{team_id}' OR g.away_team_id = '{team_id}') 
              AND g.season_id = '{season_id}'
            ORDER BY g.game_date ASC
        """)

        if pbp_games is None or not isinstance(pbp_games, pd.DataFrame) or pbp_games.empty or 'game_id' not in pbp_games.columns:
            return pd.DataFrame()
        if df_s5 is None or not isinstance(df_s5, pd.DataFrame) or df_s5.empty or 'player_ids' not in df_s5.columns:
            return pd.DataFrame()

        reconstructed_stints = []

        for gid in pbp_games['game_id'].tolist():
            df_game_events = _safe_query(conn, f"""
                SELECT * FROM pbp_event 
                WHERE game_id = '{gid}' 
                ORDER BY period ASC, game_seconds_remaining DESC, event_index ASC
            """)

            if df_game_events is None or not isinstance(df_game_events, pd.DataFrame) or df_game_events.empty or 'period' not in df_game_events.columns:
                continue

            for period in range(1, 5):
                s5_row = df_s5[(df_s5['game_id'] == gid) & (df_s5['period'] == period)]
                if s5_row.empty:
                    continue

                p_ids_val = s5_row.iloc[0].get('player_ids') if hasattr(s5_row.iloc[0], 'get') else s5_row.iloc[0]['player_ids']
                if p_ids_val is None or pd.isna(p_ids_val):
                    continue

                current_lineup = set([p.strip() for p in str(p_ids_val).split(',') if p.strip().startswith('PLY_')])
                stint_start_sec = ((4 - period) * 600.0) + 600.0
                stint_pts_for = 0
                stint_pts_against = 0
                stint_fga = 0
                stint_fgm = 0
                stint_fg3a = 0
                stint_fg3m = 0
                stint_fta = 0
                stint_tov = 0
                stint_orb = 0

                q_events = df_game_events[df_game_events['period'] == period]

                for _, ev in q_events.iterrows():
                    sec_rem = ev.get('game_seconds_remaining', 0.0) if hasattr(ev, 'get') else ev['game_seconds_remaining']
                    ev_team = ev.get('team_id') if hasattr(ev, 'get') else ev['team_id']
                    ev_type = ev.get('event_type') if hasattr(ev, 'get') else ev['event_type']
                    pts_val = ev.get('points_scored', 0) if hasattr(ev, 'get') else ev['points_scored']
                    pts = int(pts_val) if pd.notna(pts_val) and not (isinstance(pts_val, float) and np.isnan(pts_val)) else 0

                    if pts > 0:
                        if ev_team == team_id:
                            stint_pts_for += pts
                        else:
                            stint_pts_against += pts

                    if ev_team == team_id:
                        if ev_type == 'SHOT':
                            stint_fga += 1
                            if ev.get('is_made') or pts > 0:
                                stint_fgm += 1
                            if ev.get('shot_type') == '3PT' or ev.get('event_subtype') == '3':
                                stint_fg3a += 1
                                if ev.get('is_made') or pts == 3:
                                    stint_fg3m += 1
                        elif ev_type == 'FREE_THROW':
                            stint_fta += 1
                        elif ev_type == 'TURNOVER':
                            stint_tov += 1
                        elif ev_type == 'REBOUND' and ev.get('event_subtype') == 'O':
                            stint_orb += 1

                    if ev_type == 'SUB' and ev_team == team_id:
                        p_out = ev.get('player_id') if hasattr(ev, 'get') else ev['player_id']
                        p_in = ev.get('secondary_player_id') if hasattr(ev, 'get') else ev['secondary_player_id']

                        duration = stint_start_sec - sec_rem
                        if duration > 0 and len(current_lineup) == 5:
                            reconstructed_stints.append({
                                'game_id': gid,
                                'period': period,
                                'duration_seconds': duration,
                                'player_ids': ','.join(sorted([str(p) for p in current_lineup if str(p).startswith('PLY_')])),
                                'points_for': stint_pts_for,
                                'points_against': stint_pts_against,
                                'fga': stint_fga,
                                'fgm': stint_fgm,
                                'fg3a': stint_fg3a,
                                'fg3m': stint_fg3m,
                                'fta': stint_fta,
                                'tov': stint_tov,
                                'orb': stint_orb
                            })

                        # Sub transition
                        if pd.notna(p_out) and str(p_out) in current_lineup:
                            current_lineup.remove(str(p_out))
                        if pd.notna(p_in) and str(p_in).startswith('PLY_'):
                            current_lineup.add(str(p_in))

                        stint_start_sec = sec_rem
                        stint_pts_for = 0
                        stint_pts_against = 0
                        stint_fga = 0
                        stint_fgm = 0
                        stint_fg3a = 0
                        stint_fg3m = 0
                        stint_fta = 0
                        stint_tov = 0
                        stint_orb = 0

                # End of quarter remaining duration
                duration = stint_start_sec - ((4 - period) * 600.0)
                if duration > 0 and len(current_lineup) == 5:
                    reconstructed_stints.append({
                        'game_id': gid,
                        'period': period,
                        'duration_seconds': duration,
                        'player_ids': ','.join(sorted([str(p) for p in current_lineup if str(p).startswith('PLY_')])),
                        'points_for': stint_pts_for,
                        'points_against': stint_pts_against,
                        'fga': stint_fga,
                        'fgm': stint_fgm,
                        'fg3a': stint_fg3a,
                        'fg3m': stint_fg3m,
                        'fta': stint_fta,
                        'tov': stint_tov,
                        'orb': stint_orb
                    })

        return pd.DataFrame(reconstructed_stints)

    @classmethod
    def get_aggregated_lineups(cls, conn: Any, season_id: str = "SEA_2025", team_id: str = "TEM_DEMO_U16") -> pd.DataFrame:
        """Aggregates all observed 5-man lineups with advanced efficiency ratings and Four Factors."""
        df_stints = cls.reconstruct_stints(conn, season_id, team_id)
        if df_stints is None or not isinstance(df_stints, pd.DataFrame) or df_stints.empty:
            return pd.DataFrame()

        # Aggregate by Lineup
        lineup_agg = df_stints.groupby('player_ids').agg(
            games_played=('game_id', 'nunique'),
            stint_count=('duration_seconds', 'count'),
            total_seconds=('duration_seconds', 'sum'),
            pts_for=('points_for', 'sum'),
            pts_against=('points_against', 'sum'),
            fga=('fga', 'sum'),
            fgm=('fgm', 'sum'),
            fg3a=('fg3a', 'sum'),
            fg3m=('fg3m', 'sum'),
            fta=('fta', 'sum'),
            tov=('tov', 'sum'),
            orb=('orb', 'sum')
        ).reset_index()

        lineup_agg['minutes'] = round(lineup_agg['total_seconds'] / 60.0, 1)
        lineup_agg['possessions'] = round(lineup_agg['fga'] + 0.44 * lineup_agg['fta'] - lineup_agg['orb'] + lineup_agg['tov'], 1)
        lineup_agg['point_diff'] = lineup_agg['pts_for'] - lineup_agg['pts_against']
        
        # Ratings (per 100 poss)
        poss_safe = lineup_agg['possessions'].replace(0, 1.0)
        lineup_agg['ortg'] = round(lineup_agg['pts_for'] * 100.0 / poss_safe, 1)
        lineup_agg['drtg'] = round(lineup_agg['pts_against'] * 100.0 / poss_safe, 1)
        lineup_agg['net_rtg'] = round(lineup_agg['ortg'] - lineup_agg['drtg'], 1)

        # Four Factors
        fga_safe = lineup_agg['fga'].replace(0, 1.0)
        lineup_agg['efg_pct'] = round((lineup_agg['fgm'] + 0.5 * lineup_agg['fg3m']) * 100.0 / fga_safe, 1)
        lineup_agg['tov_pct'] = round(lineup_agg['tov'] * 100.0 / (lineup_agg['fga'] + 0.44 * lineup_agg['fta'] + lineup_agg['tov']).replace(0, 1.0), 1)
        lineup_agg['orb_pct'] = round(lineup_agg['orb'] * 100.0 / (lineup_agg['orb'] + 15.0), 1)  # Empirical normalization
        lineup_agg['ftr'] = round(lineup_agg['fta'] / fga_safe, 3)

        # Evidence Confidence Tiers
        def assign_tier(m: float) -> str:
            if m >= 30.0:
                return LineupEvidenceTier.STRONG_EVIDENCE.value
            elif m >= 15.0:
                return LineupEvidenceTier.MODERATE_EVIDENCE.value
            elif m >= 5.0:
                return LineupEvidenceTier.EMERGING_SIGNAL.value
            return LineupEvidenceTier.INSUFFICIENT_SAMPLE.value

        lineup_agg['evidence_tier'] = lineup_agg['minutes'].apply(assign_tier)

        # Player names mapping
        p_map = _get_player_map(conn)
        lineup_agg['player_names_list'] = lineup_agg['player_ids'].apply(lambda p_str: [p_map.get(pid, pid) for pid in p_str.split(',') if pid])
        lineup_agg['lineup_display'] = lineup_agg['player_names_list'].apply(lambda names: " + ".join(sorted(names)))

        return lineup_agg.sort_values('minutes', ascending=False).reset_index(drop=True)


# ==============================================================================
# MODE B: PROFILE-BASED QUINTET COMPLEMENTARITY ENGINE
# ==============================================================================

class QuintetComplementarityEngine:
    """Evaluates statistical complementarity, spacing, and role balance across any 1 to 5 selected players."""

    @classmethod
    def evaluate_selection(
        cls,
        df_player_stats: pd.DataFrame,
        selected_player_ids: List[str],
        p_map: Dict[str, str],
        previous_player_ids: Optional[List[str]] = None
    ) -> QuintetProfileSummary:
        """Evaluates progressive 1 to 5 player selection."""
        p_ids = [pid for pid in selected_player_ids if pid in df_player_stats['player_id'].values]
        p_names = [p_map.get(pid, pid) for pid in p_ids]
        n = len(p_ids)

        if n == 0:
            empty_scores = QuintetDimensionScores(0, 0, 0, 0, 0, 0, 0)
            return QuintetProfileSummary(
                player_ids=[],
                player_names=[],
                count=0,
                scores=empty_scores,
                is_observed=False,
                strengths=["Select players from the roster to begin constructing the unit."],
                risks_and_overlaps=[],
                film_hypotheses=[]
            )

        df_sub = df_player_stats[df_player_stats['player_id'].isin(p_ids)].copy()

        # Dimension 1: Shooting & Spacing (0 - 100)
        avg_ts = float(df_sub['ts_pct'].mean())
        avg_3par = float(df_sub['f3a_rate'].mean())
        avg_3pct = float(df_sub['fg3_pct'].mean())
        # Scale: TS% 50% = 50, 65% = 90; 3PAr 30% = 60
        s_spacing = np.clip((avg_ts - 35.0) * 2.2 + (avg_3par * 0.5) + (avg_3pct * 0.3), 15.0, 98.0)

        # Dimension 2: Creation & Playmaking (0 - 100)
        tot_ast_40 = float(df_sub['ast_per_40'].sum())
        avg_ast_tov = float(df_sub['ast_to_tov'].mean())
        # Scale: For 5 players, 15+ AST/40 is elite
        s_creation = np.clip((tot_ast_40 / (n * 3.5)) * 55.0 + (avg_ast_tov * 20.0), 10.0, 98.0)

        # Dimension 3: Rebounding & Glass Control (0 - 100)
        tot_reb_40 = float(df_sub['reb_per_40'].sum())
        # Scale: High rebounding sum across positions
        s_rebound = np.clip((tot_reb_40 / (n * 7.5)) * 80.0, 15.0, 98.0)

        # Dimension 4: Ball Security & Turnover Resistance (0 - 100)
        avg_tov_40 = float(df_sub['tov_per_40'].mean())
        # Inverted: lower TOV/40 = higher score (4.0 TOV/40 = 80, 8.0 TOV/40 = 40)
        s_security = np.clip(100.0 - (avg_tov_40 * 7.5) + (avg_ast_tov * 10.0), 10.0, 98.0)

        # Dimension 5: Defensive Profile & Event Disruption (0 - 100)
        tot_def_disrupt = float(df_sub['def_disruption'].sum())
        s_defense = np.clip((tot_def_disrupt / (n * 3.8)) * 80.0, 15.0, 98.0)

        # Dimension 6: Role & Positional Balance (0 - 100)
        # Check presence of lead handlers, shooters, and interior anchors
        has_lead_creator = any(df_sub['ast_per_40'] >= 4.0)
        has_spacer = any((df_sub['f3a_rate'] >= 35.0) & (df_sub['fg3_pct'] >= 28.0))
        has_anchor = any(df_sub['reb_per_40'] >= 10.0)
        has_scorer = any(df_sub['pts_per_40'] >= 18.0)

        role_coverage = sum([has_lead_creator, has_spacer, has_anchor, has_scorer])
        base_role_score = 40.0 + (role_coverage * 14.0)
        s_role = np.clip(base_role_score if n >= 3 else (base_role_score * 0.8), 20.0, 95.0)

        # Overall Quintet Fit Index
        fit_idx = (s_spacing * 0.22) + (s_creation * 0.18) + (s_rebound * 0.18) + (s_security * 0.15) + (s_defense * 0.15) + (s_role * 0.12)

        scores = QuintetDimensionScores(
            shooting_spacing=s_spacing,
            creation_playmaking=s_creation,
            rebounding_glass=s_rebound,
            ball_security=s_security,
            defensive_profile=s_defense,
            role_balance=s_role,
            overall_fit_index=fit_idx
        )

        # Strengths & Risks Synthesis
        strengths = []
        risks = []
        film_q = []

        if s_spacing >= 75.0:
            strengths.append(f"High-caliber perimeter spacing & shooting touch ({avg_ts:.1f}% TS composite).")
        if s_rebound >= 75.0:
            strengths.append(f"Dominant rebounding & physical interior presence ({tot_reb_40/n:.1f} REB/40 avg).")
        if s_creation >= 75.0:
            strengths.append("Fluid ball distribution and primary creation depth.")
        if s_defense >= 75.0:
            strengths.append("High defensive playmaking and passing-lane event disruption.")

        if s_security <= 55.0:
            risks.append(f"Elevated turnover vulnerability under ball pressure ({avg_tov_40:.1f} TOV/40 avg).")
            film_q.append("Review whether secondary ball-handlers handle full-court traps safely or force interior passes into traffic.")
        if s_spacing <= 55.0:
            risks.append("Contracted half-court spacing: Limited reliable catch-and-shoot 3PT threats.")
            film_q.append("Examine opposing defensive help-and-recover positioning when this unit attacks the paint.")
        if not has_anchor and n >= 4:
            risks.append("Interior rim protection deficit: Lacks a primary rim anchor with elite defensive rebounding.")

        if not strengths:
            strengths.append("Balanced developmental lineup configuration.")
        if not film_q:
            film_q.append("Examine defensive transition communication and weak-side tag execution with this unit.")

        # Progressive Addition Delta Calculation (N vs N-1)
        addition_delta = None
        if previous_player_ids and len(previous_player_ids) == n - 1:
            prev_summary = cls.evaluate_selection(df_player_stats, previous_player_ids, p_map)
            added_pid = [pid for pid in p_ids if pid not in previous_player_ids][0]
            added_pname = p_map.get(added_pid, added_pid)

            d_fit = fit_idx - prev_summary.scores.overall_fit_index
            d_shoot = s_spacing - prev_summary.scores.shooting_spacing
            d_create = s_creation - prev_summary.scores.creation_playmaking
            d_reb = s_rebound - prev_summary.scores.rebounding_glass
            d_sec = s_security - prev_summary.scores.ball_security
            d_def = s_defense - prev_summary.scores.defensive_profile
            d_role = s_role - prev_summary.scores.role_balance

            tactical_narratives = []
            if d_shoot >= 3.0: tactical_narratives.append("elevates perimeter spacing")
            if d_create >= 3.0: tactical_narratives.append("amplifies shot creation")
            if d_reb >= 3.0: tactical_narratives.append("secures glass control")
            if d_def >= 3.0: tactical_narratives.append("boosts defensive disruption")
            if d_sec <= -3.0: tactical_narratives.append("increases turnover risk")

            narrative = f"Adding **{added_pname}** {', '.join(tactical_narratives) if tactical_narratives else 'provides steady structural depth'}."

            addition_delta = ProgressiveAdditionDelta(
                added_player_id=added_pid,
                added_player_name=added_pname,
                delta_fit_index=d_fit,
                delta_shooting=d_shoot,
                delta_creation=d_create,
                delta_rebounding=d_reb,
                delta_ball_security=d_sec,
                delta_defense=d_def,
                delta_role_balance=d_role,
                tactical_summary=narrative
            )

        return QuintetProfileSummary(
            player_ids=p_ids,
            player_names=p_names,
            count=n,
            scores=scores,
            is_observed=False,
            addition_delta=addition_delta,
            strengths=strengths,
            risks_and_overlaps=risks,
            film_hypotheses=film_q
        )
