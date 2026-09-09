"""Player Trajectory, Longitudinal Trend & Development Intelligence Engine.

Rheinland Falcons Basketball — JBBL / NBBL Longitudinal Basketball Intelligence Platform.

Evaluates multi-game trajectory by comparing recent rolling form (last 4 games) against season baseline,
distinguishing genuine signal from short-term noise and accounting for minutes/role changes.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd


class TrajectoryStatus(str, Enum):
    IMPROVING = "IMPROVING"
    DETERIORATING = "DETERIORATING"
    STABLE = "STABLE"
    MIXED = "MIXED"
    INCONCLUSIVE = "INCONCLUSIVE"


class TrajectoryConfidence(str, Enum):
    STRONG_EVIDENCE = "STRONG_EVIDENCE"
    MODERATE_EVIDENCE = "MODERATE_EVIDENCE"
    EMERGING_SIGNAL = "EMERGING_SIGNAL"
    INSUFFICIENT_SAMPLE = "INSUFFICIENT_SAMPLE"


@dataclass
class PlayerTrajectorySummary:
    player_id: str
    canonical_name: str
    games_played: int
    total_minutes: float
    overall_status: TrajectoryStatus
    confidence: TrajectoryConfidence
    recent_window_games: int
    
    # Baseline vs Recent
    baseline_ppg: float
    recent_ppg: float
    delta_ppg: float
    
    baseline_ts_pct: float
    recent_ts_pct: float
    delta_ts_pct: float
    
    baseline_rpg: float
    recent_rpg: float
    delta_rpg: float
    
    baseline_apg: float
    recent_apg: float
    delta_apg: float
    
    baseline_mpg: float
    recent_mpg: float
    delta_mpg: float
    
    # Area breakdowns
    improving_areas: List[str] = field(default_factory=list)
    declining_areas: List[str] = field(default_factory=list)
    stable_areas: List[str] = field(default_factory=list)
    role_change_note: Optional[str] = None
    
    # Synthesis & Film Review
    trajectory_narrative: str = ""
    film_hypotheses: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "player_id": self.player_id,
            "canonical_name": self.canonical_name,
            "games_played": self.games_played,
            "total_minutes": round(self.total_minutes, 1),
            "overall_status": self.overall_status.value,
            "confidence": self.confidence.value,
            "recent_window_games": self.recent_window_games,
            "baseline": {
                "ppg": round(self.baseline_ppg, 1),
                "ts_pct": round(self.baseline_ts_pct, 1),
                "rpg": round(self.baseline_rpg, 1),
                "apg": round(self.baseline_apg, 1),
                "mpg": round(self.baseline_mpg, 1),
            },
            "recent": {
                "ppg": round(self.recent_ppg, 1),
                "ts_pct": round(self.recent_ts_pct, 1),
                "rpg": round(self.recent_rpg, 1),
                "apg": round(self.recent_apg, 1),
                "mpg": round(self.recent_mpg, 1),
            },
            "deltas": {
                "delta_ppg": round(self.delta_ppg, 1),
                "delta_ts_pct": round(self.delta_ts_pct, 1),
                "delta_rpg": round(self.delta_rpg, 1),
                "delta_apg": round(self.delta_apg, 1),
                "delta_mpg": round(self.delta_mpg, 1),
            },
            "improving_areas": self.improving_areas,
            "declining_areas": self.declining_areas,
            "stable_areas": self.stable_areas,
            "role_change_note": self.role_change_note,
            "trajectory_narrative": self.trajectory_narrative,
            "film_hypotheses": self.film_hypotheses,
        }


def evaluate_player_trajectory(
    df_game_log: pd.DataFrame,
    player_id: str,
    canonical_name: str,
    window_size: int = 4
) -> PlayerTrajectorySummary:
    """Evaluates multi-metric player development trajectory from chronological match log."""
    if df_game_log.empty:
        return PlayerTrajectorySummary(
            player_id=player_id,
            canonical_name=canonical_name,
            games_played=0,
            total_minutes=0.0,
            overall_status=TrajectoryStatus.INCONCLUSIVE,
            confidence=TrajectoryConfidence.INSUFFICIENT_SAMPLE,
            recent_window_games=0,
            baseline_ppg=0.0, recent_ppg=0.0, delta_ppg=0.0,
            baseline_ts_pct=0.0, recent_ts_pct=0.0, delta_ts_pct=0.0,
            baseline_rpg=0.0, recent_rpg=0.0, delta_rpg=0.0,
            baseline_apg=0.0, recent_apg=0.0, delta_apg=0.0,
            baseline_mpg=0.0, recent_mpg=0.0, delta_mpg=0.0,
            trajectory_narrative="No match appearances recorded for this season.",
            film_hypotheses=[]
        )

    df_sorted = df_game_log.sort_values("game_date").reset_index(drop=True)
    gp = len(df_sorted)
    tot_min = float(df_sorted["minutes"].sum())

    base_ppg = float(df_sorted["points"].mean())
    base_rpg = float(df_sorted["trb"].mean())
    base_apg = float(df_sorted["ast"].mean())
    base_mpg = float(df_sorted["minutes"].mean())

    # Calculate True Shooting percentage safely
    tot_pts = df_sorted["points"].sum()
    tot_fga = df_sorted["fga"].sum()
    tot_fta = df_sorted["fta"].sum()
    denom_ts = 2 * (tot_fga + 0.44 * tot_fta)
    base_ts = float(tot_pts * 100.0 / denom_ts) if denom_ts > 0 else 0.0

    if gp < window_size:
        return PlayerTrajectorySummary(
            player_id=player_id,
            canonical_name=canonical_name,
            games_played=gp,
            total_minutes=tot_min,
            overall_status=TrajectoryStatus.INCONCLUSIVE,
            confidence=TrajectoryConfidence.INSUFFICIENT_SAMPLE,
            recent_window_games=gp,
            baseline_ppg=base_ppg, recent_ppg=base_ppg, delta_ppg=0.0,
            baseline_ts_pct=base_ts, recent_ts_pct=base_ts, delta_ts_pct=0.0,
            baseline_rpg=base_rpg, recent_rpg=base_rpg, delta_rpg=0.0,
            baseline_apg=base_apg, recent_apg=base_apg, delta_apg=0.0,
            baseline_mpg=base_mpg, recent_mpg=base_mpg, delta_mpg=0.0,
            trajectory_narrative=f"Sample size ({gp} appearances, {tot_min:.0f} min) is insufficient to establish an empirical developmental trajectory.",
            film_hypotheses=["Monitor rotational entry and tactical comfort during garbage-time and early-season appearances."]
        )

    recent_df = df_sorted.tail(window_size)
    r_ppg = float(recent_df["points"].mean())
    r_rpg = float(recent_df["trb"].mean())
    r_apg = float(recent_df["ast"].mean())
    r_mpg = float(recent_df["minutes"].mean())

    r_pts = recent_df["points"].sum()
    r_fga = recent_df["fga"].sum()
    r_fta = recent_df["fta"].sum()
    r_denom_ts = 2 * (r_fga + 0.44 * r_fta)
    r_ts = float(r_pts * 100.0 / r_denom_ts) if r_denom_ts > 0 else base_ts

    d_ppg = r_ppg - base_ppg
    d_ts = r_ts - base_ts
    d_rpg = r_rpg - base_rpg
    d_apg = r_apg - base_apg
    d_mpg = r_mpg - base_mpg

    improving = []
    declining = []
    stable = []
    film_q = []

    # 1. Scoring & Efficiency
    if d_ppg >= 2.5 and d_ts >= -3.0:
        improving.append(f"Scoring volume (+{d_ppg:.1f} PPG)")
        film_q.append("Inspect whether recent scoring surge is driven by increased primary ball-screen usage or higher transition frequency.")
    elif d_ppg <= -2.5 and abs(d_mpg) < 4.0:
        declining.append(f"Scoring volume ({d_ppg:.1f} PPG)")
        film_q.append("Review whether scoring drop reflects opposing defensive scouting adjustments (denials/traps) or passive off-ball spacing.")
    else:
        stable.append("Scoring output")

    if r_denom_ts >= 10:
        if d_ts >= 5.0:
            improving.append(f"Shooting efficiency (+{d_ts:.1f}% TS)")
        elif d_ts <= -5.0:
            declining.append(f"Shooting efficiency ({d_ts:.1f}% TS)")
            film_q.append("Check shot selection quality on film: are recent misses highly contested late-clock attempts or open catch-and-shoot looks?")

    # 2. Rebounding
    if d_rpg >= 1.5:
        improving.append(f"Glass control (+{d_rpg:.1f} RPG)")
    elif d_rpg <= -1.5 and abs(d_mpg) < 4.0:
        declining.append(f"Rebounding ({d_rpg:.1f} RPG)")

    # 3. Playmaking
    if d_apg >= 1.0:
        improving.append(f"Playmaking (+{d_apg:.1f} APG)")
    elif d_apg <= -1.0 and abs(d_mpg) < 4.0:
        declining.append(f"Playmaking ({d_apg:.1f} APG)")

    # 4. Minutes & Role Shift context
    role_note = None
    if d_mpg >= 5.0:
        role_note = f"Rotation expansion: +{d_mpg:.1f} MPG over the last {window_size} games."
    elif d_mpg <= -5.0:
        role_note = f"Rotation contraction: {d_mpg:.1f} MPG over the last {window_size} games."

    # Overall Status Classification
    if len(improving) > len(declining) and not declining:
        overall = TrajectoryStatus.IMPROVING
        narrative = f"Recent form shows broad upward trajectory across {', '.join(improving)}."
    elif len(declining) > len(improving) and not improving:
        overall = TrajectoryStatus.DETERIORATING
        narrative = f"Recent performance shows downward trend in {', '.join(declining)}."
    elif improving and declining:
        overall = TrajectoryStatus.MIXED
        narrative = f"Mixed trajectory: Showing improvement in {', '.join(improving)}, alongside dip in {', '.join(declining)}."
    else:
        overall = TrajectoryStatus.STABLE
        narrative = f"Stable performance profile aligning consistently with season baseline standards ({base_ppg:.1f} PPG, {base_ts:.1f}% TS)."

    if role_note:
        narrative += f" Note: {role_note}"

    # Confidence Tier
    if gp >= 15 and tot_min >= 250:
        conf = TrajectoryConfidence.STRONG_EVIDENCE
    elif gp >= 8 and tot_min >= 100:
        conf = TrajectoryConfidence.MODERATE_EVIDENCE
    elif gp >= 4:
        conf = TrajectoryConfidence.EMERGING_SIGNAL
    else:
        conf = TrajectoryConfidence.INSUFFICIENT_SAMPLE

    if not film_q:
        film_q.append("Examine off-ball cutting tendencies, defensive closeout balance, and pick-and-roll positioning.")

    return PlayerTrajectorySummary(
        player_id=player_id,
        canonical_name=canonical_name,
        games_played=gp,
        total_minutes=tot_min,
        overall_status=overall,
        confidence=conf,
        recent_window_games=window_size,
        baseline_ppg=base_ppg,
        recent_ppg=r_ppg,
        delta_ppg=d_ppg,
        baseline_ts_pct=base_ts,
        recent_ts_pct=r_ts,
        delta_ts_pct=d_ts,
        baseline_rpg=base_rpg,
        recent_rpg=r_rpg,
        delta_rpg=d_rpg,
        baseline_apg=base_apg,
        recent_apg=r_apg,
        delta_apg=d_apg,
        baseline_mpg=base_mpg,
        recent_mpg=r_mpg,
        delta_mpg=d_mpg,
        improving_areas=improving,
        declining_areas=declining,
        stable_areas=stable,
        role_change_note=role_note,
        trajectory_narrative=narrative,
        film_hypotheses=film_q
    )
