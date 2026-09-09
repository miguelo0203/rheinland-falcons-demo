"""Pair and Trio Chemistry & Combinatorial Interaction Engine.

Rheinland Falcons Basketball — JBBL / NBBL Basketball Intelligence Platform.

Computes observed 2-man and 3-man combinations from on-court PBP stint streams,
and provides statistical role interaction metrics for profile-based pairings.
"""

from itertools import combinations
from typing import Any, Dict, List, Optional
import duckdb
import numpy as np
import pandas as pd
from python.analytics.team_intelligence_engine import LineupReconstructionEngine, _get_player_map


class PairTrioEngine:
    """Extracts and evaluates 2-man pairs and 3-man trios from observed stints and player profiles."""

    @classmethod
    def get_observed_pairs(cls, conn: Any, season_id: str = "SEA_2025", team_id: str = "TEM_DEMO_U16") -> pd.DataFrame:
        """Aggregates all observed 2-man player pairs from reconstructed stints."""
        df_stints = LineupReconstructionEngine.reconstruct_stints(conn, season_id, team_id)
        if df_stints is None or not isinstance(df_stints, pd.DataFrame) or df_stints.empty:
            return pd.DataFrame()

        p_map = _get_player_map(conn)

        pair_records = []
        for _, r in df_stints.iterrows():
            p_list = sorted([p for p in r['player_ids'].split(',') if p])
            if len(p_list) == 5:
                dur = r['duration_seconds']
                pts_f = r['points_for']
                pts_a = r['points_against']
                fga = r['fga']
                fta = r['fta']
                tov = r['tov']
                orb = r['orb']

                for p1, p2 in combinations(p_list, 2):
                    pair_records.append({
                        'game_id': r['game_id'],
                        'player_1_id': p1,
                        'player_2_id': p2,
                        'pair_key': f"{p1}_{p2}",
                        'duration_seconds': dur,
                        'points_for': pts_f,
                        'points_against': pts_a,
                        'fga': fga,
                        'fta': fta,
                        'tov': tov,
                        'orb': orb
                    })

        df_p = pd.DataFrame(pair_records)
        if df_p.empty:
            return pd.DataFrame()

        pair_agg = df_p.groupby(['pair_key', 'player_1_id', 'player_2_id']).agg(
            games_played=('game_id', 'nunique'),
            stint_count=('duration_seconds', 'count'),
            total_seconds=('duration_seconds', 'sum'),
            pts_for=('points_for', 'sum'),
            pts_against=('points_against', 'sum'),
            fga=('fga', 'sum'),
            fta=('fta', 'sum'),
            tov=('tov', 'sum'),
            orb=('orb', 'sum')
        ).reset_index()

        pair_agg['minutes'] = round(pair_agg['total_seconds'] / 60.0, 1)
        pair_agg['possessions'] = round(pair_agg['fga'] + 0.44 * pair_agg['fta'] - pair_agg['orb'] + pair_agg['tov'], 1)
        pair_agg['point_diff'] = pair_agg['pts_for'] - pair_agg['pts_against']
        
        poss_safe = pair_agg['possessions'].replace(0, 1.0)
        pair_agg['ortg'] = round(pair_agg['pts_for'] * 100.0 / poss_safe, 1)
        pair_agg['drtg'] = round(pair_agg['pts_against'] * 100.0 / poss_safe, 1)
        pair_agg['net_rtg'] = round(pair_agg['ortg'] - pair_agg['drtg'], 1)

        # Names
        pair_agg['player_1_name'] = pair_agg['player_1_id'].map(lambda pid: p_map.get(pid, pid))
        pair_agg['player_2_name'] = pair_agg['player_2_id'].map(lambda pid: p_map.get(pid, pid))
        pair_agg['pair_display'] = pair_agg.apply(lambda r: f"{r['player_1_name']} + {r['player_2_name']}", axis=1)

        # Confidence Tier
        def assign_pair_tier(m: float) -> str:
            if m >= 100.0: return "STRONG_EVIDENCE"
            elif m >= 50.0: return "MODERATE_EVIDENCE"
            elif m >= 15.0: return "EMERGING_SIGNAL"
            return "INSUFFICIENT_SAMPLE"

        pair_agg['confidence_tier'] = pair_agg['minutes'].apply(assign_pair_tier)
        return pair_agg.sort_values('minutes', ascending=False).reset_index(drop=True)

    @classmethod
    def get_observed_trios(cls, conn: Any, season_id: str = "SEA_2025", team_id: str = "TEM_DEMO_U16") -> pd.DataFrame:
        """Aggregates all observed 3-man player trios from reconstructed stints."""
        df_stints = LineupReconstructionEngine.reconstruct_stints(conn, season_id, team_id)
        if df_stints is None or not isinstance(df_stints, pd.DataFrame) or df_stints.empty:
            return pd.DataFrame()

        p_map = _get_player_map(conn)

        trio_records = []
        for _, r in df_stints.iterrows():
            p_list = sorted([p for p in r['player_ids'].split(',') if p])
            if len(p_list) == 5:
                dur = r['duration_seconds']
                pts_f = r['points_for']
                pts_a = r['points_against']
                fga = r['fga']
                fta = r['fta']
                tov = r['tov']
                orb = r['orb']

                for p1, p2, p3 in combinations(p_list, 3):
                    trio_records.append({
                        'game_id': r['game_id'],
                        'player_1_id': p1,
                        'player_2_id': p2,
                        'player_3_id': p3,
                        'trio_key': f"{p1}_{p2}_{p3}",
                        'duration_seconds': dur,
                        'points_for': pts_f,
                        'points_against': pts_a,
                        'fga': fga,
                        'fta': fta,
                        'tov': tov,
                        'orb': orb
                    })

        df_t = pd.DataFrame(trio_records)
        if df_t.empty:
            return pd.DataFrame()

        trio_agg = df_t.groupby(['trio_key', 'player_1_id', 'player_2_id', 'player_3_id']).agg(
            games_played=('game_id', 'nunique'),
            stint_count=('duration_seconds', 'count'),
            total_seconds=('duration_seconds', 'sum'),
            pts_for=('points_for', 'sum'),
            pts_against=('points_against', 'sum'),
            fga=('fga', 'sum'),
            fta=('fta', 'sum'),
            tov=('tov', 'sum'),
            orb=('orb', 'sum')
        ).reset_index()

        trio_agg['minutes'] = round(trio_agg['total_seconds'] / 60.0, 1)
        trio_agg['possessions'] = round(trio_agg['fga'] + 0.44 * trio_agg['fta'] - trio_agg['orb'] + trio_agg['tov'], 1)
        trio_agg['point_diff'] = trio_agg['pts_for'] - trio_agg['pts_against']
        
        poss_safe = trio_agg['possessions'].replace(0, 1.0)
        trio_agg['ortg'] = round(trio_agg['pts_for'] * 100.0 / poss_safe, 1)
        trio_agg['drtg'] = round(trio_agg['pts_against'] * 100.0 / poss_safe, 1)
        trio_agg['net_rtg'] = round(trio_agg['ortg'] - trio_agg['drtg'], 1)

        # Names
        trio_agg['trio_display'] = trio_agg.apply(lambda r: f"{p_map.get(r['player_1_id'], r['player_1_id'])} + {p_map.get(r['player_2_id'], r['player_2_id'])} + {p_map.get(r['player_3_id'], r['player_3_id'])}", axis=1)

        # Confidence Tier
        def assign_trio_tier(m: float) -> str:
            if m >= 60.0: return "STRONG_EVIDENCE"
            elif m >= 30.0: return "MODERATE_EVIDENCE"
            elif m >= 10.0: return "EMERGING_SIGNAL"
            return "INSUFFICIENT_SAMPLE"

        trio_agg['confidence_tier'] = trio_agg['minutes'].apply(assign_trio_tier)
        return trio_agg.sort_values('minutes', ascending=False).reset_index(drop=True)

    @classmethod
    def get_observed_quartets(cls, conn: Any, season_id: str = "SEA_2025", team_id: str = "TEM_DEMO_U16") -> pd.DataFrame:
        """Aggregates all observed 4-man player quartets from reconstructed stints."""
        df_stints = LineupReconstructionEngine.reconstruct_stints(conn, season_id, team_id)
        if df_stints is None or not isinstance(df_stints, pd.DataFrame) or df_stints.empty:
            return pd.DataFrame()

        p_map = _get_player_map(conn)

        quartet_records = []
        for _, r in df_stints.iterrows():
            p_list = sorted([p for p in r['player_ids'].split(',') if p])
            if len(p_list) == 5:
                dur = r['duration_seconds']
                pts_f = r['points_for']
                pts_a = r['points_against']
                fga = r['fga']
                fta = r['fta']
                tov = r['tov']
                orb = r['orb']

                for p1, p2, p3, p4 in combinations(p_list, 4):
                    quartet_records.append({
                        'game_id': r['game_id'],
                        'player_1_id': p1,
                        'player_2_id': p2,
                        'player_3_id': p3,
                        'player_4_id': p4,
                        'quartet_key': f"{p1}_{p2}_{p3}_{p4}",
                        'duration_seconds': dur,
                        'points_for': pts_f,
                        'points_against': pts_a,
                        'fga': fga,
                        'fta': fta,
                        'tov': tov,
                        'orb': orb
                    })

        df_q = pd.DataFrame(quartet_records)
        if df_q.empty:
            return pd.DataFrame()

        quartet_agg = df_q.groupby(['quartet_key', 'player_1_id', 'player_2_id', 'player_3_id', 'player_4_id']).agg(
            games_played=('game_id', 'nunique'),
            stint_count=('duration_seconds', 'count'),
            total_seconds=('duration_seconds', 'sum'),
            pts_for=('points_for', 'sum'),
            pts_against=('points_against', 'sum'),
            fga=('fga', 'sum'),
            fta=('fta', 'sum'),
            tov=('tov', 'sum'),
            orb=('orb', 'sum')
        ).reset_index()

        quartet_agg['minutes'] = round(quartet_agg['total_seconds'] / 60.0, 1)
        quartet_agg['possessions'] = round(quartet_agg['fga'] + 0.44 * quartet_agg['fta'] - quartet_agg['orb'] + quartet_agg['tov'], 1)
        quartet_agg['point_diff'] = quartet_agg['pts_for'] - quartet_agg['pts_against']
        
        poss_safe = quartet_agg['possessions'].replace(0, 1.0)
        quartet_agg['ortg'] = round(quartet_agg['pts_for'] * 100.0 / poss_safe, 1)
        quartet_agg['drtg'] = round(quartet_agg['pts_against'] * 100.0 / poss_safe, 1)
        quartet_agg['net_rtg'] = round(quartet_agg['ortg'] - quartet_agg['drtg'], 1)

        # Names
        quartet_agg['quartet_display'] = quartet_agg.apply(
            lambda r: f"{p_map.get(r['player_1_id'], r['player_1_id'])} + {p_map.get(r['player_2_id'], r['player_2_id'])} + {p_map.get(r['player_3_id'], r['player_3_id'])} + {p_map.get(r['player_4_id'], r['player_4_id'])}",
            axis=1
        )

        # Confidence Tier for 4-man quartets
        def assign_quartet_tier(m: float) -> str:
            if m >= 40.0: return "STRONG_EVIDENCE"
            elif m >= 20.0: return "MODERATE_EVIDENCE"
            elif m >= 5.0: return "EMERGING_SIGNAL"
            return "INSUFFICIENT_SAMPLE"

        quartet_agg['confidence_tier'] = quartet_agg['minutes'].apply(assign_quartet_tier)
        return quartet_agg.sort_values('minutes', ascending=False).reset_index(drop=True)
