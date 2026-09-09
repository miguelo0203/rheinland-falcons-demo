"""Deterministic Evidence-Based Analytical Engine for Academy Development Monitoring.

Provides statistical classification, temporal multi-window evaluation, possession-gated
on-court impact analysis, and U16 -> U19 promotion screening for Rheinland Falcons Basketball.

Invariants:
- Zero black-box composite scores.
- Net Rating requires >= 20 reconstructable possessions in BOTH comparison windows.
- Multi-dimensional signal confirmation required for IMPROVING / DECLINING.
- Conservative stagnation definition (>= 8 GP, >= 10 MPG, multi-window flat metrics).
- Conservative fallback to STABLE.
- Strict category isolation (U16 vs U19).
- Dynamic data extraction with zero hardcoded roster sizes, game counts, or benchmark medians.
- Full point-in-time temporal cutoff support (as_of_date).
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd


class DevelopmentStatus(str, Enum):
    IMPROVING = "IMPROVING"
    STABLE = "STABLE"
    STAGNATING = "STAGNATING"
    DECLINING = "DECLINING"
    INSUFFICIENT_DATA = "INSUFFICIENT DATA"


class EvidenceStrength(str, Enum):
    STRONG = "STRONG EVIDENCE"
    MODERATE = "MODERATE EVIDENCE"
    LIMITED = "LIMITED EVIDENCE"
    INSUFFICIENT = "INSUFFICIENT EVIDENCE"


class ScreeningCriterionStatus(str, Enum):
    PASS = "PASS"
    NOT_MET = "NOT MET"
    UNAVAILABLE = "UNAVAILABLE"


@dataclass
class DevelopmentWindow:
    """Aggregated player performance window calculated strictly from raw sums."""
    gp: int = 0
    total_minutes: float = 0.0
    mpg: float = 0.0
    ppg: float = 0.0
    rpg: float = 0.0
    apg: float = 0.0
    topg: float = 0.0
    spg: float = 0.0
    bpg: float = 0.0
    fga_per_game: float = 0.0
    tot_pts: int = 0
    tot_fga: int = 0
    tot_fgm: int = 0
    tot_fg2a: int = 0
    tot_fg2m: int = 0
    tot_fg3a: int = 0
    tot_fg3m: int = 0
    tot_fta: int = 0
    tot_ftm: int = 0
    tot_trb: int = 0
    tot_ast: int = 0
    tot_tov: int = 0
    ts_pct: Optional[float] = None
    efg_pct: Optional[float] = None
    ast_to_tov: Optional[float] = None
    stint_poss: float = 0.0
    stint_pts_for: float = 0.0
    stint_pts_against: float = 0.0
    ortg: Optional[float] = None
    drtg: Optional[float] = None
    net_rtg: Optional[float] = None
    net_rtg_low_volume: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "gp": self.gp,
            "total_minutes": self.total_minutes,
            "mpg": self.mpg,
            "ppg": self.ppg,
            "rpg": self.rpg,
            "apg": self.apg,
            "topg": self.topg,
            "spg": self.spg,
            "bpg": self.bpg,
            "fga_per_game": self.fga_per_game,
            "tot_pts": self.tot_pts,
            "tot_fga": self.tot_fga,
            "tot_fta": self.tot_fta,
            "ts_pct": self.ts_pct,
            "efg_pct": self.efg_pct,
            "ast_to_tov": self.ast_to_tov,
            "stint_poss": self.stint_poss,
            "ortg": self.ortg,
            "drtg": self.drtg,
            "net_rtg": self.net_rtg,
            "net_rtg_low_volume": self.net_rtg_low_volume,
        }


@dataclass
class DevelopmentDeltas:
    """Multi-dimensional delta comparison between Recent window and Comparison window."""
    comparison_type: str = "PREVIOUS_WINDOW"  # "PREVIOUS_WINDOW" or "SEASON_BASELINE"
    delta_ts_pct: Optional[float] = None
    delta_efg_pct: Optional[float] = None
    delta_net_rtg: Optional[float] = None
    net_rtg_eligible_for_classification: bool = False
    net_rtg_recent_poss: float = 0.0
    net_rtg_comp_poss: float = 0.0
    delta_ppg: float = 0.0
    delta_mpg: float = 0.0
    delta_apg: float = 0.0
    delta_topg: float = 0.0
    delta_rpg: float = 0.0
    delta_fga_pg: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "comparison_type": self.comparison_type,
            "delta_ts_pct": self.delta_ts_pct,
            "delta_efg_pct": self.delta_efg_pct,
            "delta_net_rtg": self.delta_net_rtg,
            "net_rtg_eligible_for_classification": self.net_rtg_eligible_for_classification,
            "net_rtg_recent_poss": self.net_rtg_recent_poss,
            "net_rtg_comp_poss": self.net_rtg_comp_poss,
            "delta_ppg": self.delta_ppg,
            "delta_mpg": self.delta_mpg,
            "delta_apg": self.delta_apg,
            "delta_topg": self.delta_topg,
            "delta_rpg": self.delta_rpg,
            "delta_fga_pg": self.delta_fga_pg,
        }


@dataclass
class PlayerDevelopmentProfile:
    """Complete developmental evaluation profile for an academy player."""
    player_id: str
    canonical_name: str
    team_id: str
    squad: str
    season_id: str
    status: DevelopmentStatus
    status_badge: str
    evidence_strength: EvidenceStrength
    recent_window: DevelopmentWindow
    baseline_window: DevelopmentWindow
    previous_window: Optional[DevelopmentWindow] = None
    deltas: DevelopmentDeltas = field(default_factory=DevelopmentDeltas)
    sample_summary: str = ""
    sample_notes: str = ""
    primary_signals: List[str] = field(default_factory=list)
    why_narrative: str = ""
    attention_flags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "player_id": self.player_id,
            "canonical_name": self.canonical_name,
            "team_id": self.team_id,
            "squad": self.squad,
            "season_id": self.season_id,
            "status": self.status.value,
            "status_badge": self.status_badge,
            "evidence_strength": self.evidence_strength.value,
            "recent_window": self.recent_window.to_dict(),
            "previous_window": self.previous_window.to_dict() if self.previous_window else None,
            "baseline_window": self.baseline_window.to_dict(),
            "deltas": self.deltas.to_dict(),
            "sample_summary": self.sample_summary,
            "sample_notes": self.sample_notes,
            "primary_signals": self.primary_signals,
            "why_narrative": self.why_narrative,
            "attention_flags": self.attention_flags,
        }


@dataclass
class PipelineEvaluation:
    """Multi-criteria screening evaluation for U16 -> U19 transition."""
    player_id: str
    canonical_name: str
    squad: str
    criterion_sample_stability: ScreeningCriterionStatus
    criterion_sample_detail: str
    criterion_trajectory: ScreeningCriterionStatus
    criterion_trajectory_detail: str
    criterion_efficiency: ScreeningCriterionStatus
    criterion_efficiency_detail: str
    criterion_role_capacity: ScreeningCriterionStatus
    criterion_role_detail: str
    criterion_impact: ScreeningCriterionStatus
    criterion_impact_detail: str
    qualification_status: str  # "POTENTIAL U19 CANDIDATE", "CONDITIONAL CANDIDATE", "NOT CURRENTLY INDICATED"
    qualification_badge: str
    summary_notes: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "player_id": self.player_id,
            "canonical_name": self.canonical_name,
            "squad": self.squad,
            "sample_stability": {
                "status": self.criterion_sample_stability.value,
                "detail": self.criterion_sample_detail,
            },
            "trajectory": {
                "status": self.criterion_trajectory.value,
                "detail": self.criterion_trajectory_detail,
            },
            "efficiency": {
                "status": self.criterion_efficiency.value,
                "detail": self.criterion_efficiency_detail,
            },
            "role_capacity": {
                "status": self.criterion_role_capacity.value,
                "detail": self.criterion_role_detail,
            },
            "on_court_impact": {
                "status": self.criterion_impact.value,
                "detail": self.criterion_impact_detail,
            },
            "qualification_status": self.qualification_status,
            "qualification_badge": self.qualification_badge,
            "summary_notes": self.summary_notes,
        }


class AcademyDevelopmentEngine:
    """Core analytical engine for multi-window development monitoring."""

    MIN_GP_FOR_TREND: int = 4
    MIN_MINUTES_FOR_TREND: float = 20.0
    MIN_GP_FOR_MULTI_WINDOW: int = 8
    MIN_POSS_FOR_NET_RTG: float = 20.0
    MIN_FGA_FOR_TS_VOLUME: float = 3.0
    MIN_GP_FOR_STAGNATION: int = 8
    MIN_MPG_FOR_STAGNATION: float = 10.0

    @classmethod
    def aggregate_window(cls, df_w: pd.DataFrame) -> DevelopmentWindow:
        """Aggregates a subset of match boxscores strictly from raw sums."""
        gp = len(df_w)
        if gp == 0:
            return DevelopmentWindow()

        tot_pts = int(df_w['points'].sum()) if 'points' in df_w.columns else 0
        tot_fga = int(df_w['fga'].sum()) if 'fga' in df_w.columns else 0
        tot_fgm = int(df_w['fgm'].sum()) if 'fgm' in df_w.columns else 0
        tot_fg2a = int(df_w['fg2a'].sum()) if 'fg2a' in df_w.columns else 0
        tot_fg2m = int(df_w['fg2m'].sum()) if 'fg2m' in df_w.columns else 0
        tot_fg3a = int(df_w['fg3a'].sum()) if 'fg3a' in df_w.columns else 0
        tot_fg3m = int(df_w['fg3m'].sum()) if 'fg3m' in df_w.columns else 0
        tot_fta = int(df_w['fta'].sum()) if 'fta' in df_w.columns else 0
        tot_ftm = int(df_w['ftm'].sum()) if 'ftm' in df_w.columns else 0
        tot_trb = int(df_w['trb'].sum()) if 'trb' in df_w.columns else 0
        tot_ast = int(df_w['ast'].sum()) if 'ast' in df_w.columns else 0
        tot_tov = int(df_w['tov'].sum()) if 'tov' in df_w.columns else 0
        tot_stl = int(df_w['stl'].sum()) if 'stl' in df_w.columns else 0
        tot_blk = int(df_w['blk'].sum()) if 'blk' in df_w.columns else 0
        tot_min = float(df_w['minutes'].sum()) if 'minutes' in df_w.columns else 0.0

        # Exact True Shooting % formula from raw sums
        ts_denom = 2.0 * (tot_fga + 0.44 * tot_fta)
        ts_pct = round(100.0 * tot_pts / ts_denom, 1) if ts_denom > 0 else None

        # Effective FG%
        efg_pct = round(100.0 * (tot_fgm + 0.5 * tot_fg3m) / tot_fga, 1) if tot_fga > 0 else None

        # AST/TOV ratio
        if tot_tov > 0:
            ast_to_tov = round(float(tot_ast) / float(tot_tov), 2)
        elif tot_ast > 0:
            ast_to_tov = float(tot_ast)
        else:
            ast_to_tov = None

        # PBP on-court stint aggregation
        stint_poss = 0.0
        stint_pts_for = 0.0
        stint_pts_against = 0.0
        ortg = None
        drtg = None
        net_rtg = None
        net_rtg_low_volume = False

        if 'stint_poss' in df_w.columns and 'stint_pts_for' in df_w.columns and 'stint_pts_against' in df_w.columns:
            valid_stints = df_w.dropna(subset=['stint_poss'])
            if not valid_stints.empty:
                stint_poss = round(float(valid_stints['stint_poss'].sum()), 1)
                stint_pts_for = round(float(valid_stints['stint_pts_for'].sum()), 1)
                stint_pts_against = round(float(valid_stints['stint_pts_against'].sum()), 1)

                if stint_poss > 0:
                    ortg = round(100.0 * stint_pts_for / stint_poss, 1)
                    drtg = round(100.0 * stint_pts_against / stint_poss, 1)
                    net_rtg = round(ortg - drtg, 1)
                    if stint_poss < cls.MIN_POSS_FOR_NET_RTG:
                        net_rtg_low_volume = True

        return DevelopmentWindow(
            gp=gp,
            total_minutes=round(tot_min, 1),
            mpg=round(tot_min / gp, 1) if gp > 0 else 0.0,
            ppg=round(float(tot_pts) / gp, 1) if gp > 0 else 0.0,
            rpg=round(float(tot_trb) / gp, 1) if gp > 0 else 0.0,
            apg=round(float(tot_ast) / gp, 1) if gp > 0 else 0.0,
            topg=round(float(tot_tov) / gp, 1) if gp > 0 else 0.0,
            spg=round(float(tot_stl) / gp, 1) if gp > 0 else 0.0,
            bpg=round(float(tot_blk) / gp, 1) if gp > 0 else 0.0,
            fga_per_game=round(float(tot_fga) / gp, 1) if gp > 0 else 0.0,
            tot_pts=tot_pts,
            tot_fga=tot_fga,
            tot_fgm=tot_fgm,
            tot_fg2a=tot_fg2a,
            tot_fg2m=tot_fg2m,
            tot_fg3a=tot_fg3a,
            tot_fg3m=tot_fg3m,
            tot_fta=tot_fta,
            tot_ftm=tot_ftm,
            tot_trb=tot_trb,
            tot_ast=tot_ast,
            tot_tov=tot_tov,
            ts_pct=ts_pct,
            efg_pct=efg_pct,
            ast_to_tov=ast_to_tov,
            stint_poss=stint_poss,
            stint_pts_for=stint_pts_for,
            stint_pts_against=stint_pts_against,
            ortg=ortg,
            drtg=drtg,
            net_rtg=net_rtg,
            net_rtg_low_volume=net_rtg_low_volume,
        )

    @classmethod
    def compute_deltas(
        cls,
        recent: DevelopmentWindow,
        comparison: DevelopmentWindow,
        comparison_type: str = "PREVIOUS_WINDOW"
    ) -> DevelopmentDeltas:
        """Computes deltas between recent and comparison window with possession gating."""
        d_ts = round(recent.ts_pct - comparison.ts_pct, 1) if (recent.ts_pct is not None and comparison.ts_pct is not None) else None
        d_efg = round(recent.efg_pct - comparison.efg_pct, 1) if (recent.efg_pct is not None and comparison.efg_pct is not None) else None
        d_ppg = round(recent.ppg - comparison.ppg, 1)
        d_mpg = round(recent.mpg - comparison.mpg, 1)
        d_apg = round(recent.apg - comparison.apg, 1)
        d_topg = round(recent.topg - comparison.topg, 1)
        d_rpg = round(recent.rpg - comparison.rpg, 1)
        d_fga = round(recent.fga_per_game - comparison.fga_per_game, 1)

        # Net Rating possession-volume gating: >= 20.0 possessions required in BOTH windows
        recent_poss = recent.stint_poss
        comp_poss = comparison.stint_poss
        has_min_poss = (recent_poss >= cls.MIN_POSS_FOR_NET_RTG) and (comp_poss >= cls.MIN_POSS_FOR_NET_RTG)

        d_net = None
        if recent.net_rtg is not None and comparison.net_rtg is not None:
            d_net = round(recent.net_rtg - comparison.net_rtg, 1)

        eligible_for_classification = bool(has_min_poss and (d_net is not None))

        return DevelopmentDeltas(
            comparison_type=comparison_type,
            delta_ts_pct=d_ts,
            delta_efg_pct=d_efg,
            delta_net_rtg=d_net,
            net_rtg_eligible_for_classification=eligible_for_classification,
            net_rtg_recent_poss=recent_poss,
            net_rtg_comp_poss=comp_poss,
            delta_ppg=d_ppg,
            delta_mpg=d_mpg,
            delta_apg=d_apg,
            delta_topg=d_topg,
            delta_rpg=d_rpg,
            delta_fga_pg=d_fga,
        )

    @classmethod
    def evaluate_player_development(
        cls,
        df_player_games: pd.DataFrame,
        player_id: str,
        canonical_name: str,
        team_id: str,
        squad: str,
        season_id: str,
        as_of_date: Optional[str] = None
    ) -> PlayerDevelopmentProfile:
        """Evaluates a single player's development trajectory under the approved specification."""
        # 1. Temporal point-in-time filtering (zero future leakage)
        df = df_player_games.copy()
        if as_of_date and not df.empty and 'game_date' in df.columns:
            cutoff = str(as_of_date)[:10]
            df = df[df['game_date'].astype(str) <= cutoff]

        # Filter out DNP or 0-second appearances if seconds_played exists
        if not df.empty and 'seconds_played' in df.columns:
            df = df[df['seconds_played'] > 0]
        elif not df.empty and 'minutes' in df.columns:
            df = df[df['minutes'] > 0.0]

        total_gp = len(df)
        total_min = float(df['minutes'].sum()) if (not df.empty and 'minutes' in df.columns) else 0.0

        # Full season baseline window
        baseline_w = cls.aggregate_window(df)

        # 2. Sample Floor Guard (< 4 GP or < 20 min -> INSUFFICIENT DATA)
        if total_gp < cls.MIN_GP_FOR_TREND or total_min < cls.MIN_MINUTES_FOR_TREND:
            return PlayerDevelopmentProfile(
                player_id=player_id,
                canonical_name=canonical_name,
                team_id=team_id,
                squad=squad,
                season_id=season_id,
                status=DevelopmentStatus.INSUFFICIENT_DATA,
                status_badge="⚪ INSUFFICIENT DATA",
                evidence_strength=EvidenceStrength.INSUFFICIENT,
                recent_window=baseline_w,
                baseline_window=baseline_w,
                previous_window=None,
                deltas=DevelopmentDeltas(comparison_type="NONE"),
                sample_summary=f"{total_gp} match{'es' if total_gp != 1 else ''} ({total_min:.1f} min)",
                sample_notes="Sample below minimum evaluation threshold (>= 4 matches and >= 20.0 total minutes). Trend analysis suspended to prevent small-sample noise.",
                primary_signals=[],
                why_narrative=f"{canonical_name} has logged {total_gp} official appearance{'s' if total_gp != 1 else ''} ({total_min:.1f} total minutes) in squad {squad}. A minimum sample of 4 appearances with at least 20 minutes played is required before developmental trends can be reliably established.",
                attention_flags=["SAMPLE_TOO_SMALL"] if total_gp > 0 else ["ROSTER_REGISTERED_NO_MATCHES"]
            )

        # 3. Sort chronologically
        if 'game_date' in df.columns:
            df = df.sort_values(['game_date', 'game_id'] if 'game_id' in df.columns else ['game_date']).reset_index(drop=True)

        # 4. Temporal Multi-Window Slicing
        recent_size = min(5, total_gp)
        recent_df = df.tail(recent_size)
        recent_w = cls.aggregate_window(recent_df)

        if total_gp >= cls.MIN_GP_FOR_MULTI_WINDOW:
            # Multi-window: Recent (last 5) vs Previous (preceding up to 5, min 3)
            prev_end = total_gp - recent_size
            prev_start = max(0, prev_end - 5)
            prev_df = df.iloc[prev_start:prev_end]
            prev_w = cls.aggregate_window(prev_df)
            deltas = cls.compute_deltas(recent_w, prev_w, comparison_type="PREVIOUS_WINDOW")
            sample_summary = f"{len(recent_df)} + {len(prev_df)} matches"
            sample_notes = f"Recent: Last {len(recent_df)} matches ({recent_w.total_minutes:.1f} min) vs Previous: {len(prev_df)} matches ({prev_w.total_minutes:.1f} min) · Season Total: {total_gp} matches."
            comp_w = prev_w
        else:
            # Single-window vs Season Baseline
            prev_w = None
            deltas = cls.compute_deltas(recent_w, baseline_w, comparison_type="SEASON_BASELINE")
            sample_summary = f"{len(recent_df)} matches"
            sample_notes = f"Recent: Last {len(recent_df)} matches ({recent_w.total_minutes:.1f} min) evaluated against Season Baseline ({total_gp} matches, {baseline_w.total_minutes:.1f} min)."
            comp_w = baseline_w

        # 5. Multi-Signal Directional Evaluation Matrix
        d_ts = deltas.delta_ts_pct
        d_net = deltas.delta_net_rtg
        net_valid = deltas.net_rtg_eligible_for_classification
        d_ppg = deltas.delta_ppg
        d_mpg = deltas.delta_mpg
        d_topg = deltas.delta_topg
        d_apg = deltas.delta_apg
        d_rpg = deltas.delta_rpg
        ts_vol_ok = (recent_w.fga_per_game >= cls.MIN_FGA_FOR_TS_VOLUME)

        # Check for IMPROVING
        improving_path_a = (d_ts is not None and d_ts >= 4.0 and ts_vol_ok and net_valid and d_net is not None and d_net >= 5.0)
        improving_path_b = (
            d_ts is not None and d_ts >= 4.0 and ts_vol_ok and
            (d_ppg >= 2.5 or d_mpg >= 3.0) and
            (not net_valid or d_net is None or d_net >= -2.0)
        )
        improving_path_c = (
            net_valid and d_net is not None and d_net >= 7.0 and
            d_ppg >= 2.0 and
            (d_ts is None or d_ts >= -1.5)
        )

        is_improving = (improving_path_a or improving_path_b or improving_path_c)

        # Strict contradictor guards for IMPROVING
        if is_improving:
            if d_ts is not None and d_ts <= -4.0 and ts_vol_ok:
                is_improving = False
            if net_valid and d_net is not None and d_net <= -6.0:
                is_improving = False

        # Check for DECLINING
        declining_path_a = (
            d_ts is not None and d_ts <= -6.0 and ts_vol_ok and
            ((net_valid and d_net is not None and d_net <= 0.0) or d_ppg <= -2.0 or d_topg >= 1.0)
        )
        declining_path_b = (
            net_valid and d_net is not None and d_net <= -9.0 and
            (d_ts is None or d_ts <= -2.0)
        )
        declining_path_c = (
            d_ppg <= -3.5 and (d_ts is not None and d_ts <= -3.5) and d_mpg <= -3.0
        )

        is_declining = (declining_path_a or declining_path_b or declining_path_c)

        # Check for STAGNATING (Conservative Definition)
        is_stagnating = False
        if not is_improving and not is_declining:
            if (
                total_gp >= cls.MIN_GP_FOR_STAGNATION and
                baseline_w.mpg >= cls.MIN_MPG_FOR_STAGNATION and
                recent_w.mpg >= cls.MIN_MPG_FOR_STAGNATION and
                deltas.comparison_type == "PREVIOUS_WINDOW" and
                (d_ts is None or abs(d_ts) < 2.0) and
                abs(d_ppg) < 1.5 and
                abs(d_mpg) < 2.0 and
                (not net_valid or d_net is None or abs(d_net) < 3.0) and
                abs(d_apg) < 0.8 and
                abs(d_rpg) < 1.0
            ):
                is_stagnating = True

        # Assign final Status
        if is_improving:
            status = DevelopmentStatus.IMPROVING
            badge = "🟢 IMPROVING"
        elif is_declining:
            status = DevelopmentStatus.DECLINING
            badge = "🔴 DECLINING"
        elif is_stagnating:
            status = DevelopmentStatus.STAGNATING
            badge = "🟡 STAGNATING"
        else:
            status = DevelopmentStatus.STABLE
            badge = "⚪ STABLE"

        # 6. Evidence Strength Tiering
        if status == DevelopmentStatus.IMPROVING:
            if improving_path_a:
                ev_strength = EvidenceStrength.STRONG
            elif improving_path_b or improving_path_c:
                ev_strength = EvidenceStrength.STRONG if (total_gp >= 8 and ts_vol_ok) else EvidenceStrength.MODERATE
            else:
                ev_strength = EvidenceStrength.MODERATE
        elif status == DevelopmentStatus.DECLINING:
            if declining_path_a and net_valid:
                ev_strength = EvidenceStrength.STRONG
            elif declining_path_b:
                ev_strength = EvidenceStrength.STRONG
            else:
                ev_strength = EvidenceStrength.MODERATE
        elif status == DevelopmentStatus.STAGNATING:
            ev_strength = EvidenceStrength.STRONG if (total_gp >= 10 and net_valid) else EvidenceStrength.MODERATE
        else:  # STABLE
            if total_gp >= 8 and net_valid and ts_vol_ok:
                ev_strength = EvidenceStrength.STRONG
            elif total_gp >= 5:
                ev_strength = EvidenceStrength.MODERATE
            else:
                ev_strength = EvidenceStrength.LIMITED

        # 7. Construct Primary Signals & Narrative ("Why?" Explanation)
        comp_label = "previous window" if deltas.comparison_type == "PREVIOUS_WINDOW" else "season baseline"
        primary_signals = []
        attention_flags = []

        # TS% signal
        if d_ts is not None and recent_w.ts_pct is not None and comp_w.ts_pct is not None:
            vol_note = f" [{recent_w.fga_per_game:.1f} FGA/g]" if ts_vol_ok else f" (Low Volume: {recent_w.fga_per_game:.1f} FGA/g)"
            primary_signals.append(
                f"True Shooting: {d_ts:+0.1f} pp ({recent_w.ts_pct:.1f}% vs {comp_w.ts_pct:.1f}% {comp_label}){vol_note}"
            )
            if d_ts >= 5.0 and ts_vol_ok:
                attention_flags.append("EFFICIENCY_SURGE")
            elif d_ts <= -5.0 and ts_vol_ok:
                attention_flags.append("EFFICIENCY_DROP")

        # Net Rating signal
        if d_net is not None and recent_w.net_rtg is not None and comp_w.net_rtg is not None:
            if net_valid:
                primary_signals.append(
                    f"On-Court Net Rating: {d_net:+0.1f} per 100 poss ({recent_w.net_rtg:+0.1f} vs {comp_w.net_rtg:+0.1f} {comp_label}) [Possessions: {deltas.net_rtg_recent_poss:.1f} / {deltas.net_rtg_comp_poss:.1f}]"
                )
                if d_net >= 6.0:
                    attention_flags.append("IMPACT_SURGE")
                elif d_net <= -8.0:
                    attention_flags.append("IMPACT_DROP")
            else:
                primary_signals.append(
                    f"On-Court Net Rating: {d_net:+0.1f} (Low Volume: {deltas.net_rtg_recent_poss:.1f} / {deltas.net_rtg_comp_poss:.1f} poss — Excluded from classification)"
                )
        elif recent_w.net_rtg is None:
            primary_signals.append("On-Court Net Rating: Unavailable (PBP stint data unobserved)")

        # Scoring & Role signals
        primary_signals.append(f"Scoring: {d_ppg:+0.1f} PPG ({recent_w.ppg:.1f} vs {comp_w.ppg:.1f} PPG {comp_label})")
        primary_signals.append(f"Playing Time: {d_mpg:+0.1f} MPG ({recent_w.mpg:.1f} vs {comp_w.mpg:.1f} MPG {comp_label})")

        if d_mpg >= 4.0:
            attention_flags.append("ROLE_EXPANSION")
        elif d_mpg <= -4.0:
            attention_flags.append("ROTATION_DROP")

        if d_topg >= 1.5:
            attention_flags.append("TURNOVER_INCREASE")

        # Build Why Narrative
        narrative_parts = [
            f"**{canonical_name}** is classified as **{status.value}** ({ev_strength.value}).",
            f"Over the recent {recent_w.gp}-match evaluation window, the athlete averaged {recent_w.ppg:.1f} PPG and {recent_w.rpg:.1f} RPG in {recent_w.mpg:.1f} MPG."
        ]
        if d_ts is not None:
            narrative_parts.append(
                f"True Shooting changed by {d_ts:+0.1f} percentage points ({recent_w.ts_pct:.1f}% vs {comp_w.ts_pct:.1f}%)."
            )
        if d_net is not None:
            if net_valid:
                narrative_parts.append(
                    f"On-court net rating shifted by {d_net:+0.1f} per 100 possessions ({recent_w.net_rtg:+0.1f} vs {comp_w.net_rtg:+0.1f}) across {deltas.net_rtg_recent_poss:.0f} and {deltas.net_rtg_comp_poss:.0f} reconstructable possessions."
                )
            else:
                narrative_parts.append(
                    f"Net rating ({d_net:+0.1f}) is recorded under low possession volume ({deltas.net_rtg_recent_poss:.0f} poss) and was conservatively excluded from triggering classification."
                )

        if status == DevelopmentStatus.IMPROVING:
            narrative_parts.append("Multi-dimensional positive evidence confirms developmental growth exceeding natural youth variance.")
        elif status == DevelopmentStatus.DECLINING:
            narrative_parts.append("Meaningful downward divergence across monitored dimensions warrants staff review and tactical support.")
        elif status == DevelopmentStatus.STAGNATING:
            narrative_parts.append("Performance and role have remained essentially flat across consecutive multi-game windows despite sustained rotational opportunity.")
        else:
            narrative_parts.append("Performance remains consistent with established baseline standards within normal statistical variation.")

        return PlayerDevelopmentProfile(
            player_id=player_id,
            canonical_name=canonical_name,
            team_id=team_id,
            squad=squad,
            season_id=season_id,
            status=status,
            status_badge=badge,
            evidence_strength=ev_strength,
            recent_window=recent_w,
            previous_window=prev_w,
            baseline_window=baseline_w,
            deltas=deltas,
            sample_summary=sample_summary,
            sample_notes=sample_notes,
            primary_signals=primary_signals,
            why_narrative=" ".join(narrative_parts),
            attention_flags=attention_flags,
        )

    @classmethod
    def evaluate_u16_pipeline_candidate(
        cls,
        profile: PlayerDevelopmentProfile,
        benchmark_ts_threshold: float = 50.0
    ) -> PipelineEvaluation:
        """Evaluates a U16 player for potential U19 exposure via an objective screening matrix."""
        base = profile.baseline_window

        # Criterion 1: Sample Stability (>= 10 GP and >= 200 min)
        if base.gp >= 10 and base.total_minutes >= 200.0:
            c1_status = ScreeningCriterionStatus.PASS
            c1_detail = f"{base.gp} GP · {base.total_minutes:.1f} Total Minutes (Meets >= 10 GP / 200 min)"
        else:
            c1_status = ScreeningCriterionStatus.NOT_MET
            c1_detail = f"{base.gp} GP · {base.total_minutes:.1f} Total Minutes (Requires >= 10 GP / 200 min)"

        # Criterion 2: Development Trajectory (IMPROVING or high-efficiency STABLE)
        if profile.status == DevelopmentStatus.IMPROVING:
            c2_status = ScreeningCriterionStatus.PASS
            c2_detail = f"Status: {profile.status.value} ({profile.evidence_strength.value})"
        elif profile.status == DevelopmentStatus.STABLE and (base.ts_pct is not None and base.ts_pct >= benchmark_ts_threshold):
            c2_status = ScreeningCriterionStatus.PASS
            c2_detail = f"Status: STABLE with high baseline efficiency ({base.ts_pct:.1f}% TS)"
        else:
            c2_status = ScreeningCriterionStatus.NOT_MET
            c2_detail = f"Status: {profile.status.value} (Positive or efficient trajectory required)"

        # Criterion 3: True Shooting Efficiency (>= threshold, default 50.0%)
        if base.ts_pct is not None and base.ts_pct >= benchmark_ts_threshold:
            c3_status = ScreeningCriterionStatus.PASS
            c3_detail = f"{base.ts_pct:.1f}% TS% (Meets screening threshold >= {benchmark_ts_threshold:.1f}%)"
        elif base.ts_pct is not None:
            c3_status = ScreeningCriterionStatus.NOT_MET
            c3_detail = f"{base.ts_pct:.1f}% TS% (Below screening threshold {benchmark_ts_threshold:.1f}%)"
        else:
            c3_status = ScreeningCriterionStatus.UNAVAILABLE
            c3_detail = "TS% unavailable"

        # Criterion 4: Role Capacity (>= 18.0 MPG)
        if base.mpg >= 18.0:
            c4_status = ScreeningCriterionStatus.PASS
            c4_detail = f"{base.mpg:.1f} MPG (Meets high-leverage threshold >= 18.0 MPG)"
        else:
            c4_status = ScreeningCriterionStatus.NOT_MET
            c4_detail = f"{base.mpg:.1f} MPG (Below 18.0 MPG threshold)"

        # Criterion 5: On-Court Impact (Net Rtg > 0.0 with >= 40 season reconstructable possessions)
        if base.stint_poss >= 40.0 and base.net_rtg is not None:
            if base.net_rtg > 0.0:
                c5_status = ScreeningCriterionStatus.PASS
                c5_detail = f"{base.net_rtg:+0.1f} Net Rating ({base.stint_poss:.1f} season possessions)"
            else:
                c5_status = ScreeningCriterionStatus.NOT_MET
                c5_detail = f"{base.net_rtg:+0.1f} Net Rating ({base.stint_poss:.1f} season possessions)"
        elif base.stint_poss > 0:
            c5_status = ScreeningCriterionStatus.UNAVAILABLE
            c5_detail = f"Low possession volume: {base.stint_poss:.1f} / 40.0 possessions"
        else:
            c5_status = ScreeningCriterionStatus.UNAVAILABLE
            c5_detail = "Stint PBP unobserved"

        # Qualification Evaluation Matrix
        core_passed = (
            c1_status == ScreeningCriterionStatus.PASS and
            c2_status == ScreeningCriterionStatus.PASS and
            c3_status == ScreeningCriterionStatus.PASS and
            c4_status == ScreeningCriterionStatus.PASS
        )
        impact_ok = (c5_status in (ScreeningCriterionStatus.PASS, ScreeningCriterionStatus.UNAVAILABLE))

        if core_passed and impact_ok:
            qual_status = "POTENTIAL U19 CANDIDATE"
            qual_badge = "🌟 POTENTIAL U19 CANDIDATE"
            summary = "Athlete meets all core stability, efficiency, role, and trajectory screening criteria. Recommended for tactical and physical evaluation by U19 coaching staff."
        elif c1_status == ScreeningCriterionStatus.PASS and c4_status == ScreeningCriterionStatus.PASS:
            qual_status = "CONDITIONAL CANDIDATE"
            qual_badge = "🔍 CONDITIONAL CANDIDATE"
            summary = "Athlete demonstrates strong role stability and court exposure, but efficiency or recent trajectory requires further developmental consolidation before U19 promotion."
        else:
            qual_status = "NOT CURRENTLY INDICATED"
            qual_badge = "⚪ NOT CURRENTLY INDICATED"
            summary = "Athlete currently does not meet the multi-dimensional sample stability, role, or trajectory requirements for older-age exposure."

        return PipelineEvaluation(
            player_id=profile.player_id,
            canonical_name=profile.canonical_name,
            squad=profile.squad,
            criterion_sample_stability=c1_status,
            criterion_sample_detail=c1_detail,
            criterion_trajectory=c2_status,
            criterion_trajectory_detail=c2_detail,
            criterion_efficiency=c3_status,
            criterion_efficiency_detail=c3_detail,
            criterion_role_capacity=c4_status,
            criterion_role_detail=c4_detail,
            criterion_impact=c5_status,
            criterion_impact_detail=c5_detail,
            qualification_status=qual_status,
            qualification_badge=qual_badge,
            summary_notes=summary,
        )
