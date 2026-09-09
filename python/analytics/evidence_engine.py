"""Universal Evidence & Statistical Interpretation Engine v2.

Rheinland Falcons Basketball — JBBL / NBBL Longitudinal Basketball Intelligence Platform.

Evolves metric presentation from raw numbers/percentiles into a rigorous epistemic evidence chain:
    OBSERVATION -> DENOMINATOR -> VOLUME -> EFFICIENCY -> RATE -> ROLE -> CONTEXT -> PERCENTILE -> STABILITY -> INTERPRETATION -> LIMITATIONS -> FILM QUESTIONS
"""

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union
import math
import numpy as np
import pandas as pd

def _safe_float(v: Any, default: float = 0.0) -> float:
    if v is None or pd.isna(v):
        return default
    try:
        f = float(v)
        return default if np.isnan(f) else f
    except (ValueError, TypeError):
        return default

def _safe_int(v: Any, default: int = 0) -> int:
    return int(_safe_float(v, float(default)))

def format_ordinal(n: Union[int, float, str]) -> str:
    """Formats a number with proper English ordinal suffix (1st, 2nd, 3rd, 82nd, 85th, 100th)."""
    try:
        val = int(round(float(n)))
    except (ValueError, TypeError):
        return str(n)
    if 11 <= (val % 100) <= 13:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(val % 10, "th")
    return f"{val}{suffix}"

def format_season(season_id: Any) -> str:
    """Formats season identifier into standard academic year notation (e.g. SEA_2025 -> 2025/26)."""
    s = str(season_id or "2025/26").replace("SEA_", "")
    if len(s) == 4 and s.isdigit():
        nxt = str(int(s) + 1)[-2:]
        return f"{s}/{nxt}"
    return s

# =============================================================================
# 1. TAXONOMY & AVAILABILITY ENUMS
# =============================================================================

class ContextAvailability(str, Enum):
    AVAILABLE = "AVAILABLE"
    DERIVABLE = "DERIVABLE"
    NOT_AVAILABLE = "NOT_AVAILABLE"
    NOT_IDENTIFIABLE = "NOT_IDENTIFIABLE"

class EvidenceLevel(str, Enum):
    OBSERVATION = "OBSERVATION"
    CONTEXT = "CONTEXT"
    INTERPRETATION = "INTERPRETATION"
    HYPOTHESIS = "HYPOTHESIS"
    CLAIM = "CLAIM"  # Never auto-generated without human audit

class StabilityTier(str, Enum):
    ESTABLISHED_SIGNAL = "ESTABLISHED_SIGNAL"
    USABLE_SIGNAL = "USABLE_SIGNAL"
    EMERGING_SIGNAL = "EMERGING_SIGNAL"
    DESCRIPTIVE_ONLY = "DESCRIPTIVE_ONLY"

# Formal Metric Relationship Registry
METRIC_RELATIONSHIPS = {
    "points": {
        "primary_context": ["fga", "fta", "minutes", "usage"],
        "derived_context": ["pts_per_40", "ts_pct", "efg_pct"],
        "opportunity_denominator": "possessions_or_minutes",
        "description": "Scoring volume and points produced."
    },
    "three_pointers_made": {
        "primary_context": ["fg3a", "fg3_pct", "three_point_attempt_rate"],
        "derived_context": ["fg3_pct", "f3a_per_game", "f3a_rate"],
        "opportunity_denominator": "fg3a",
        "description": "3-point conversion and perimeter volume."
    },
    "two_pointers_made": {
        "primary_context": ["fg2a", "fg2_pct", "paint_frequency"],
        "derived_context": ["fg2_pct", "fg2a_per_game"],
        "opportunity_denominator": "fg2a",
        "description": "2-point conversion and interior shot volume."
    },
    "assists": {
        "primary_context": ["minutes", "turnovers", "usage"],
        "derived_context": ["ast_per_40", "ast_to_tov", "ast_pct_proxy"],
        "opportunity_denominator": "minutes_and_possessions",
        "description": "Shot creation for teammates and ball distribution."
    },
    "rebounds": {
        "primary_context": ["minutes", "team_rebounds", "orb", "drb"],
        "derived_context": ["reb_per_40", "rpg"],
        "opportunity_denominator": "minutes_and_missed_shots",
        "description": "Glass control on offensive and defensive possessions."
    },
    "steals": {
        "primary_context": ["minutes", "possessions"],
        "derived_context": ["stl_per_40"],
        "opportunity_denominator": "opponent_possessions",
        "description": "Defensive event play on passing lanes and ball pressure."
    },
    "blocks": {
        "primary_context": ["minutes", "opponent_2pa"],
        "derived_context": ["blk_per_40"],
        "opportunity_denominator": "opponent_interior_attempts",
        "description": "Rim protection and interior shot deterrence."
    },
    "net_rating": {
        "primary_context": ["minutes", "lineup_exposure", "opponent_context"],
        "secondary_context": ["teammate_context"],
        "derived_context": ["off_rating", "def_rating", "margin_per_100"],
        "opportunity_denominator": "team_and_opponent_possessions",
        "description": "Team scoring margin per 100 possessions during player on-court exposure."
    },
    "ortg": {
        "primary_context": ["possessions", "usage", "efficiency"],
        "derived_context": ["ts_pct", "tov_rate"],
        "opportunity_denominator": "offensive_possessions",
        "description": "Points generated per 100 team offensive possessions."
    },
    "drtg": {
        "primary_context": ["possessions", "opponent_quality", "lineup_context"],
        "derived_context": ["def_rebounding", "turnover_generation"],
        "opportunity_denominator": "defensive_possessions",
        "description": "Points allowed per 100 opponent possessions during exposure."
    },
    "on_off": {
        "primary_context": ["on_minutes", "off_minutes", "lineup_continuity"],
        "derived_context": ["net_rating_delta"],
        "opportunity_denominator": "on_off_possessions_split",
        "description": "Differential team performance when player is on-court vs off-court."
    }
}

# =============================================================================
# 2. STRUCTURED EVIDENCE INTERPRETATION DATACLASS
# =============================================================================

@dataclass
class StructuredEvidenceInterpretation:
    category: str
    metric_name: str
    headline: str
    observation: Dict[str, Any]
    context: Dict[str, Any]
    volume_context: Dict[str, Any]
    efficiency_context: Dict[str, Any]
    stability_tier: str
    interpretation: str
    limitations: List[str]
    film_questions: List[str]
    evidence_level: str = EvidenceLevel.INTERPRETATION.value

    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category,
            "metric_name": self.metric_name,
            "headline": self.headline,
            "observation": self.observation.get("text", str(self.observation)),
            "context": self.context.get("text", str(self.context)),
            "volume_note": self.volume_context.get("text", str(self.volume_context)),
            "interpretation": self.interpretation,
            "stability_tier": self.stability_tier,
            "film_question": self.film_questions[0] if self.film_questions else "",
            "limitations": self.limitations,
            "structured_data": asdict(self)
        }

# =============================================================================
# 3. SAMPLE STABILITY EVALUATION ENGINE
# =============================================================================

class StabilityEvaluator:
    """Calculates sample stability tiers based on domain-specific basketball thresholds."""

    @staticmethod
    def evaluate_fga_stability(fga: float) -> str:
        f = _safe_float(fga)
        if f >= 150:
            return StabilityTier.ESTABLISHED_SIGNAL.value
        elif f >= 75:
            return StabilityTier.USABLE_SIGNAL.value
        elif f >= 25:
            return StabilityTier.EMERGING_SIGNAL.value
        return StabilityTier.DESCRIPTIVE_ONLY.value

    @staticmethod
    def evaluate_3pa_stability(fg3a: float) -> str:
        f = _safe_float(fg3a)
        if f >= 200:
            return StabilityTier.ESTABLISHED_SIGNAL.value
        elif f >= 75:
            return StabilityTier.USABLE_SIGNAL.value
        elif f >= 25:
            return StabilityTier.EMERGING_SIGNAL.value
        return StabilityTier.DESCRIPTIVE_ONLY.value

    @staticmethod
    def evaluate_tsa_stability(tsa: float) -> str:
        f = _safe_float(tsa)
        if f >= 180:
            return StabilityTier.ESTABLISHED_SIGNAL.value
        elif f >= 90:
            return StabilityTier.USABLE_SIGNAL.value
        elif f >= 30:
            return StabilityTier.EMERGING_SIGNAL.value
        return StabilityTier.DESCRIPTIVE_ONLY.value

    @staticmethod
    def evaluate_fta_stability(fta: float) -> str:
        f = _safe_float(fta)
        if f >= 100:
            return StabilityTier.ESTABLISHED_SIGNAL.value
        elif f >= 50:
            return StabilityTier.USABLE_SIGNAL.value
        elif f >= 20:
            return StabilityTier.EMERGING_SIGNAL.value
        return StabilityTier.DESCRIPTIVE_ONLY.value

    @staticmethod
    def evaluate_minutes_stability(minutes: float) -> str:
        f = _safe_float(minutes)
        if f >= 250:
            return StabilityTier.ESTABLISHED_SIGNAL.value
        elif f >= 100:
            return StabilityTier.USABLE_SIGNAL.value
        elif f >= 40:
            return StabilityTier.EMERGING_SIGNAL.value
        return StabilityTier.DESCRIPTIVE_ONLY.value

    @staticmethod
    def evaluate_event_stability(minutes: float) -> str:
        """For volatile event-based defensive stats (steals, blocks)."""
        f = _safe_float(minutes)
        if f >= 300:
            return StabilityTier.ESTABLISHED_SIGNAL.value
        elif f >= 120:
            return StabilityTier.USABLE_SIGNAL.value
        elif f >= 50:
            return StabilityTier.EMERGING_SIGNAL.value
        return StabilityTier.DESCRIPTIVE_ONLY.value

    @staticmethod
    def evaluate_rating_stability(minutes: float, possessions: Optional[float] = None) -> str:
        """For team ratings and On/Off splits."""
        if possessions is not None:
            p = _safe_float(possessions)
            if p >= 800:
                return StabilityTier.ESTABLISHED_SIGNAL.value
            elif p >= 400:
                return StabilityTier.USABLE_SIGNAL.value
            elif p >= 150:
                return StabilityTier.EMERGING_SIGNAL.value
            return StabilityTier.DESCRIPTIVE_ONLY.value
        return StabilityEvaluator.evaluate_minutes_stability(minutes)

# =============================================================================
# 4. UNIVERSAL EVIDENCE & INTERPRETATION ENGINE
# =============================================================================

class EvidenceInterpretationEngine:
    """Universal basketball evidence engine that explains metrics in context."""

    def __init__(self):
        self.evaluator = StabilityEvaluator()

    # -------------------------------------------------------------------------
    # 4.1. SCORING & PRODUCTION INTERPRETER
    # -------------------------------------------------------------------------
    def interpret_scoring(
        self,
        stats: Dict[str, Any],
        percentiles: Dict[str, Any],
        medians: Dict[str, Any],
        benchmark_meta: Dict[str, Any]
    ) -> StructuredEvidenceInterpretation:
        pts = _safe_float(stats.get('total_pts', 0))
        pts_40 = _safe_float(stats.get('pts_per_40', 0.0))
        ppg = _safe_float(stats.get('ppg', 0.0))
        fga = _safe_float(stats.get('total_fga', 0))
        fta = _safe_float(stats.get('total_fta', 0))
        tot_min = _safe_float(stats.get('total_min', 0))
        gp = max(1, _safe_int(stats.get('gp', 1)))
        ts_pct = _safe_float(stats.get('ts_pct', 0.0))
        
        p_pts = _safe_float(percentiles.get('pts_per_40', 50.0))
        p_ts = _safe_float(percentiles.get('ts_pct', 50.0))
        pop_n = _safe_int(benchmark_meta.get('qualified_pop_size', percentiles.get('qualified_pop_size', 34)))
        season_str = format_season(benchmark_meta.get('season_id', 'SEA_2025'))
        comp_str = str(benchmark_meta.get('competition_id', 'CMP_JBBL')).replace('CMP_', '')

        stability = self.evaluator.evaluate_fga_stability(fga)
        med_pts = _safe_float(medians.get('pts_per_40', 16.9))
        med_ts = _safe_float(medians.get('ts_pct', 49.1))

        # Context synthesis (Volume vs Efficiency)
        if p_pts >= 75 and p_ts >= 75:
            interp = "High scoring output is supported by above-average shooting efficiency rather than shot volume alone."
        elif p_pts >= 75 and p_ts < 40:
            interp = "The player produces substantial scoring volume, but the scoring rate is accompanied by below-average shooting efficiency. The production appears more volume-driven than efficiency-driven."
        elif p_pts >= 75:
            interp = "The player carries substantial scoring responsibility in the offense with solid conversion across opportunities."
        elif p_pts < 40 and p_ts >= 75:
            interp = "Scoring output is modest, but efficiency is strong. The player is not currently producing high scoring volume despite converting efficiently on available looks."
        else:
            interp = "Scoring rate and shooting efficiency align closely with league-median rotational standards."

        obs_text = f"Scored {_safe_int(pts)} total points in {_safe_int(tot_min)} minutes ({ppg:.1f} PPG, {pts_40:.1f} PTS/40)."
        ctx_text = f"Ranks at the {format_ordinal(p_pts)} percentile in scoring rate and {format_ordinal(p_ts)} percentile in True Shooting % among {pop_n} qualified {comp_str} players from season {season_str} (>=100 min, Median: {med_pts:.1f} PTS/40, {med_ts:.1f}% TS)."
        vol_text = f"Generated across {_safe_int(fga)} field goal attempts ({fga/gp:.1f} FGA/G) and {_safe_int(fta)} free throw attempts in {gp} appearances."

        limitations = []
        if stability in [StabilityTier.EMERGING_SIGNAL.value, StabilityTier.DESCRIPTIVE_ONLY.value]:
            limitations.append(f"Scoring sample is limited ({_safe_int(fga)} FGA); signal stability is classified as {stability}.")
        if 'usage_pct' not in stats:
            limitations.append("Possession usage rate is estimated from boxscore proxy rather than play-by-play possession tracking.")

        film_q = [
            "Verify on film how much scoring comes in transition vs structured half-court sets, and how defensive coverage adjusts to his scoring runs."
        ]

        return StructuredEvidenceInterpretation(
            category="Scoring & True Shooting",
            metric_name="pts_per_40",
            headline=f"{pts_40:.1f} PTS/40 ({format_ordinal(p_pts)} %ile) | {ts_pct:.1f}% TS ({format_ordinal(p_ts)} %ile)",
            observation={"text": obs_text, "total_pts": pts, "total_min": tot_min, "ppg": ppg, "pts_per_40": pts_40},
            context={"text": ctx_text, "pts_pct": p_pts, "ts_pct": p_ts, "benchmark_n": pop_n, "season": season_str},
            volume_context={"text": vol_text, "fga": fga, "fta": fta, "fga_per_game": round(fga/gp, 1)},
            efficiency_context={"ts_pct": ts_pct, "ts_percentile": p_ts, "median_ts": med_ts},
            stability_tier=stability,
            interpretation=interp,
            limitations=limitations,
            film_questions=film_q
        )

    # -------------------------------------------------------------------------
    # 4.2. THREE-POINT & PERIMETER SHOOTING INTERPRETER
    # -------------------------------------------------------------------------
    def interpret_perimeter_shooting(
        self,
        stats: Dict[str, Any],
        percentiles: Dict[str, Any],
        medians: Dict[str, Any],
        benchmark_meta: Dict[str, Any]
    ) -> StructuredEvidenceInterpretation:
        fg3m = _safe_float(stats.get('total_fg3m', 0))
        fg3a = _safe_float(stats.get('total_fg3a', 0))
        fga = _safe_float(stats.get('total_fga', 0))
        fg3_pct = _safe_float(stats.get('fg3_pct', 0.0))
        f3a_rate = _safe_float(stats.get('f3a_rate', 0.0))
        gp = max(1, _safe_int(stats.get('gp', 1)))

        p_3p = _safe_float(percentiles.get('fg3_pct', 50.0))
        pop_n = _safe_int(benchmark_meta.get('qualified_pop_size', percentiles.get('qualified_pop_size', 34)))
        season_str = format_season(benchmark_meta.get('season_id', 'SEA_2025'))
        comp_str = str(benchmark_meta.get('competition_id', 'CMP_JBBL')).replace('CMP_', '')
        med_3p = _safe_float(medians.get('fg3_pct', 25.0))

        stability = self.evaluator.evaluate_3pa_stability(fg3a)

        # Distinguish Makes vs Attempts and Volume vs Efficiency
        if fg3a >= 25:
            if p_3p >= 75 and stability == StabilityTier.EMERGING_SIGNAL.value:
                interp = (
                    f"The player converted {fg3_pct:.1f}% from three ({_safe_int(fg3m)}/{_safe_int(fg3a)}), placing him at the top of the qualified distribution. "
                    f"However, {_safe_int(fg3a)} attempts classify the 3P% signal as emerging rather than established. "
                    "The percentage indicates strong observed conversion efficiency, but the sample is still relatively limited."
                )
            elif p_3p >= 75 and stability in [StabilityTier.ESTABLISHED_SIGNAL.value, StabilityTier.USABLE_SIGNAL.value]:
                interp = (
                    f"High three-point conversion ({fg3_pct:.1f}%) is validated across substantial attempt volume ({_safe_int(fg3a)} 3PA). "
                    "Perimeter shooting represents a reliable and established weapon in the offensive repertoire."
                )
            elif p_3p < 40 and fg3a >= 75:
                interp = (
                    f"The player attempted a high volume of threes ({_safe_int(fg3a)} 3PA, {f3a_rate:.1f}% of FGA), but converted {fg3_pct:.1f}%. "
                    "The 3-point production is driven by attempt volume and perimeter shot diet rather than high conversion efficiency."
                )
            else:
                interp = f"Shows moderate perimeter capability ({fg3_pct:.1f}% 3P on {_safe_int(fg3a)} 3PA), representing {f3a_rate:.1f}% of overall shot diet."
        else:
            interp = f"Recorded {_safe_int(fg3m)} makes on {_safe_int(fg3a)} attempts ({fg3_pct:.1f}%). Attempt volume is very low (<25 3PA); descriptive only."

        obs_text = f"Converted {_safe_int(fg3m)} of {_safe_int(fg3a)} three-point attempts ({fg3_pct:.1f}% 3P, {fg3a/gp:.1f} 3PA/G)."
        ctx_text = f"Ranks at the {format_ordinal(p_3p)} percentile in 3P% among {pop_n} qualified {comp_str} peers from season {season_str} (>=100 min, Median: {med_3p:.1f}%)."
        vol_text = f"Three-point attempts account for {f3a_rate:.1f}% of total field goal attempts ({_safe_int(fg3a)}/{_safe_int(fga)} FGA)."

        limitations = []
        if stability != StabilityTier.ESTABLISHED_SIGNAL.value:
            limitations.append(f"3-point sample ({_safe_int(fg3a)} 3PA) has not reached the stabilization threshold (>=200 3PA); classified as {stability}.")
        limitations.append("Contested vs uncontested shot quality tracking is unavailable in standard boxscores.")

        film_q = [
            "Inspect whether 3-point makes stem predominantly from assisted catch-and-shoot looks, open trailer opportunities, or self-created pull-ups."
        ]

        return StructuredEvidenceInterpretation(
            category="Perimeter Shooting",
            metric_name="fg3_pct",
            headline=f"{fg3_pct:.1f}% 3P ({_safe_int(fg3m)}/{_safe_int(fg3a)}) | {format_ordinal(p_3p)} %ile",
            observation={"text": obs_text, "fg3m": fg3m, "fg3a": fg3a, "fg3_pct": fg3_pct},
            context={"text": ctx_text, "percentile": p_3p, "median": med_3p, "benchmark_n": pop_n},
            volume_context={"text": vol_text, "fg3a": fg3a, "f3a_rate": f3a_rate, "f3a_per_game": round(fg3a/gp, 1)},
            efficiency_context={"fg3_pct": fg3_pct, "percentile": p_3p},
            stability_tier=stability,
            interpretation=interp,
            limitations=limitations,
            film_questions=film_q
        )

    # -------------------------------------------------------------------------
    # 4.3. PLAYMAKING & BALL SECURITY INTERPRETER
    # -------------------------------------------------------------------------
    def interpret_playmaking(
        self,
        stats: Dict[str, Any],
        percentiles: Dict[str, Any],
        medians: Dict[str, Any],
        benchmark_meta: Dict[str, Any]
    ) -> StructuredEvidenceInterpretation:
        ast = _safe_float(stats.get('total_ast', 0))
        tov = _safe_float(stats.get('total_tov', 0))
        apg = _safe_float(stats.get('apg', 0.0))
        ast_40 = _safe_float(stats.get('ast_per_40', 0.0))
        ast_to_tov = _safe_float(stats.get('ast_to_tov', 1.0))
        tot_min = _safe_float(stats.get('total_min', 0))
        mpg = _safe_float(stats.get('mpg', 0.0))
        gp = max(1, _safe_int(stats.get('gp', 1)))

        p_ast = _safe_float(percentiles.get('ast_per_40', 50.0))
        p_tov = _safe_float(percentiles.get('ast_to_tov', 50.0))
        pop_n = _safe_int(benchmark_meta.get('qualified_pop_size', percentiles.get('qualified_pop_size', 34)))
        season_str = format_season(benchmark_meta.get('season_id', 'SEA_2025'))
        comp_str = str(benchmark_meta.get('competition_id', 'CMP_JBBL')).replace('CMP_', '')
        med_ast = _safe_float(medians.get('ast_per_40', 3.5))
        med_tov = _safe_float(medians.get('ast_to_tov', 0.8))

        stability = self.evaluator.evaluate_minutes_stability(tot_min)

        if p_ast >= 75 and ast_to_tov >= 1.0:
            interp = f"The player generates {ast_40:.1f} AST/40 ({format_ordinal(p_ast)} percentile), accompanied by a solid {ast_to_tov:.2f} AST/TOV ratio, indicating that assist creation is occurring with controlled turnover risk."
        elif p_ast >= 75:
            interp = f"Active primary playmaker ({ast_40:.1f} AST/40, {format_ordinal(p_ast)} percentile), carrying high facilitation duties alongside a higher turnover burden ({_safe_int(tov)} TOV in {_safe_int(tot_min)} min)."
        elif apg >= 4.0 and mpg >= 28.0:
            interp = f"The player records {apg:.1f} APG, but plays substantial minutes ({mpg:.1f} MPG). His per-40 rate ({ast_40:.1f} AST/40) provides a normalized perspective relative to league peers."
        else:
            interp = f"Rotational ball-distribution output ({ast_40:.1f} AST/40, AST/TOV: {ast_to_tov:.2f})."

        obs_text = f"Dished {_safe_int(ast)} assists against {_safe_int(tov)} turnovers in {_safe_int(tot_min)} minutes ({apg:.1f} APG, {ast_40:.1f} AST/40)."
        ctx_text = f"Ranks at the {format_ordinal(p_ast)} percentile in playmaking creation and {format_ordinal(p_tov)} percentile in AST/TOV among {pop_n} qualified {comp_str} peers from season {season_str} (>=100 min, Median: {med_ast:.1f} AST/40, {med_tov:.2f} AST/TOV)."
        vol_text = f"Recorded across {gp} games with {mpg:.1f} minutes of on-court playmaking responsibility per game."

        limitations = [
            "Potential assists, hockey (secondary) assists, and passing turnover breakdowns are not available in standard boxscores."
        ]

        film_q = [
            "Analyze drive-and-kick decision making, pick-and-roll pass timing, and turnover triggers against full-court pressure."
        ]

        return StructuredEvidenceInterpretation(
            category="Playmaking & Ball Control",
            metric_name="ast_per_40",
            headline=f"{ast_40:.1f} AST/40 ({format_ordinal(p_ast)} %ile) | AST/TOV: {ast_to_tov:.2f}",
            observation={"text": obs_text, "total_ast": ast, "total_tov": tov, "apg": apg, "ast_40": ast_40},
            context={"text": ctx_text, "ast_pct": p_ast, "tov_pct": p_tov, "benchmark_n": pop_n},
            volume_context={"text": vol_text, "total_min": tot_min, "mpg": mpg},
            efficiency_context={"ast_to_tov": ast_to_tov, "median_ratio": med_tov},
            stability_tier=stability,
            interpretation=interp,
            limitations=limitations,
            film_questions=film_q
        )

    # -------------------------------------------------------------------------
    # 4.4. REBOUNDING & GLASS CONTROL INTERPRETER
    # -------------------------------------------------------------------------
    def interpret_rebounding(
        self,
        stats: Dict[str, Any],
        percentiles: Dict[str, Any],
        medians: Dict[str, Any],
        benchmark_meta: Dict[str, Any]
    ) -> StructuredEvidenceInterpretation:
        trb = _safe_float(stats.get('total_trb', 0))
        orb = _safe_float(stats.get('total_orb', 0))
        drb = _safe_float(stats.get('total_drb', 0))
        rpg = _safe_float(stats.get('rpg', 0.0))
        reb_40 = _safe_float(stats.get('reb_per_40', 0.0))
        tot_min = _safe_float(stats.get('total_min', 0))
        mpg = _safe_float(stats.get('mpg', 0.0))
        gp = max(1, _safe_int(stats.get('gp', 1)))

        p_reb = _safe_float(percentiles.get('reb_per_40', 50.0))
        pop_n = _safe_int(benchmark_meta.get('qualified_pop_size', percentiles.get('qualified_pop_size', 34)))
        season_str = format_season(benchmark_meta.get('season_id', 'SEA_2025'))
        comp_str = str(benchmark_meta.get('competition_id', 'CMP_JBBL')).replace('CMP_', '')
        med_reb = _safe_float(medians.get('reb_per_40', 8.4))

        stability = self.evaluator.evaluate_minutes_stability(tot_min)

        if p_reb >= 90:
            if (orb + drb) > 0:
                glass_desc = f"Shows high physical impact on the boards across both offensive ({_safe_int(orb)}) and defensive ({_safe_int(drb)}) glass."
            else:
                glass_desc = f"Shows high physical impact on the glass ({_safe_int(trb)} total rebounds secured)."
            interp = f"{rpg:.1f} RPG reflects substantial per-game production, confirmed by a rate of {reb_40:.1f} REB/40 which places him at the top of the qualified JBBL distribution. {glass_desc}"
        elif p_reb >= 70:
            interp = f"Solid above-average rebounding contributor ({reb_40:.1f} REB/40, {format_ordinal(p_reb)} percentile), consistently securing possessions in his rotational minutes."
        elif rpg >= 7.0 and mpg >= 28.0:
            interp = f"Records {rpg:.1f} RPG, but per-40 rate ({reb_40:.1f} REB/40) demonstrates that raw totals are partly a function of high playing time ({mpg:.1f} MPG)."
        else:
            interp = f"Positional rebounding output ({reb_40:.1f} REB/40, {rpg:.1f} RPG) within expected parameters."

        if (orb + drb) > 0:
            obs_text = f"Secured {_safe_int(trb)} total rebounds ({_safe_int(orb)} offensive, {_safe_int(drb)} defensive) in {_safe_int(tot_min)} minutes ({rpg:.1f} RPG, {reb_40:.1f} REB/40)."
        else:
            obs_text = f"Secured {_safe_int(trb)} total rebounds in {_safe_int(tot_min)} minutes ({rpg:.1f} RPG, {reb_40:.1f} REB/40)."
        ctx_text = f"Ranks at the {format_ordinal(p_reb)} percentile in per-minute rebounding among {pop_n} qualified {comp_str} peers from season {season_str} (>=100 min, Median: {med_reb:.1f} REB/40)."
        vol_text = f"Recorded across {gp} games with {mpg:.1f} minutes of court exposure per game."

        limitations = [
            "Contested rebound %, box-out counts, and rebound opportunity conversions are not tracked in standard boxscores."
        ]

        film_q = [
            "Examine box-out fundamentals, positioning vs crashing traffic, and outlet pass initiation speed."
        ]

        return StructuredEvidenceInterpretation(
            category="Rebounding",
            metric_name="reb_per_40",
            headline=f"{reb_40:.1f} REB/40 ({format_ordinal(p_reb)} %ile) | {rpg:.1f} RPG",
            observation={"text": obs_text, "total_trb": trb, "orb": orb, "drb": drb, "rpg": rpg, "reb_40": reb_40},
            context={"text": ctx_text, "percentile": p_reb, "median": med_reb, "benchmark_n": pop_n},
            volume_context={"text": vol_text, "total_min": tot_min, "mpg": mpg},
            efficiency_context={"orb_share": round(orb*100.0/trb, 1) if trb > 0 else 0.0},
            stability_tier=stability,
            interpretation=interp,
            limitations=limitations,
            film_questions=film_q
        )

    # -------------------------------------------------------------------------
    # 4.5. ADVANCED RATINGS & ON/OFF INTERPRETER (RESPONSIBLE ATTRIBUTION)
    # -------------------------------------------------------------------------
    def interpret_net_rating(
        self,
        net_rtg: float,
        minutes: float,
        possessions: Optional[float] = None,
        lineup_info: Optional[Dict[str, Any]] = None
    ) -> StructuredEvidenceInterpretation:
        f_net = _safe_float(net_rtg)
        f_min = _safe_float(minutes)
        stability = self.evaluator.evaluate_rating_stability(f_min, possessions)
        poss_str = f" across approx {_safe_int(possessions)} possessions" if possessions else ""

        interp = (
            f"The team outscored opponents by {f_net:+.1f} points per 100 possessions during this player's measured exposure{poss_str} ({_safe_int(f_min)} minutes). "
            "The statistic describes team performance during his observed minutes; it should not be interpreted as an isolated measure of individual impact."
        )

        limitations = [
            "Individual attribution is limited because the available data does not fully isolate teammate and opponent lineup effects.",
            f"Sample exposure is {stability.lower()} ({_safe_int(f_min)} minutes)."
        ]

        film_q = [
            "Review lineup combinations and tactical flow during positive scoring runs vs negative scoring stretches."
        ]

        return StructuredEvidenceInterpretation(
            category="Team Impact Metric",
            metric_name="net_rating",
            headline=f"Net Rating: {f_net:+.1f} in {_safe_int(f_min)} Min",
            observation={"text": f"Team Net Rating was {f_net:+.1f} during {_safe_int(f_min)} on-court minutes.", "net_rtg": f_net, "minutes": f_min},
            context={"text": f"Measured across team on-court minutes (Signal: {stability})."},
            volume_context={"text": f"Total exposure: {_safe_int(f_min)} minutes{poss_str}."},
            efficiency_context={"net_rating": f_net},
            stability_tier=stability,
            interpretation=interp,
            limitations=limitations,
            film_questions=film_q
        )

    def interpret_offensive_rating(
        self,
        ortg: float,
        minutes: float,
        possessions: Optional[float] = None,
        usage_pct: Optional[float] = None
    ) -> StructuredEvidenceInterpretation:
        f_ortg = _safe_float(ortg)
        f_min = _safe_float(minutes)
        stability = self.evaluator.evaluate_rating_stability(f_min, possessions)
        usg_note = f" (estimated usage: {usage_pct:.1f}%)" if usage_pct is not None else ""

        interp = (
            f"Team generated {f_ortg:.1f} points per 100 offensive possessions during player's on-court minutes{usg_note}. "
            "High efficiency in a low-usage or complementary role is not equivalent to sustaining the same efficiency under primary-creator usage."
        )

        limitations = [
            "Team ORTG is heavily dependent on 5-man offensive spacing and teammate shot-making.",
            "Possession-level shot creation vs play-finishing context is required for complete individual evaluation."
        ]

        return StructuredEvidenceInterpretation(
            category="Offensive Efficiency",
            metric_name="ortg",
            headline=f"ORTG: {f_ortg:.1f} Points / 100 Possessions",
            observation={"text": f"Offensive rating of {f_ortg:.1f} across {_safe_int(f_min)} minutes.", "ortg": f_ortg, "minutes": f_min},
            context={"text": "Team-level offensive output during player floor time."},
            volume_context={"text": f"Exposure: {_safe_int(f_min)} minutes."},
            efficiency_context={"ortg": f_ortg},
            stability_tier=stability,
            interpretation=interp,
            limitations=limitations,
            film_questions=["Examine offensive set execution and spacing when this lineup configuration is on the floor."]
        )

    def interpret_defensive_rating(
        self,
        drtg: float,
        minutes: float,
        possessions: Optional[float] = None
    ) -> StructuredEvidenceInterpretation:
        f_drtg = _safe_float(drtg)
        f_min = _safe_float(minutes)
        stability = self.evaluator.evaluate_rating_stability(f_min, possessions)

        interp = (
            f"Team allowed {f_drtg:.1f} points per 100 possessions during player's on-court minutes. "
            "This team-level result is influenced by teammates, opponent shot quality, and lineup combinations and should not be treated as a standalone individual defensive grade."
        )

        limitations = [
            "Individual defensive rating cannot isolate point-of-attack vs help-side breakdowns without spatial tracking.",
            "Opponent shooting variance over small samples materially impacts defensive rating."
        ]

        return StructuredEvidenceInterpretation(
            category="Defensive Efficiency",
            metric_name="drtg",
            headline=f"DRTG: {f_drtg:.1f} Points Allowed / 100 Poss",
            observation={"text": f"Allowed {f_drtg:.1f} points per 100 possessions across {_safe_int(f_min)} minutes.", "drtg": f_drtg, "minutes": f_min},
            context={"text": "Team-level defensive outcome during player floor time."},
            volume_context={"text": f"Exposure: {_safe_int(f_min)} minutes."},
            efficiency_context={"drtg": f_drtg},
            stability_tier=stability,
            interpretation=interp,
            limitations=limitations,
            film_questions=["Review defensive communication, pick-and-roll coverage execution, and defensive rebounding discipline."]
        )

    def interpret_on_off(
        self,
        on_net: float,
        off_net: float,
        on_min: float,
        off_min: float
    ) -> StructuredEvidenceInterpretation:
        f_on = _safe_float(on_net)
        f_off = _safe_float(off_net)
        f_on_min = _safe_float(on_min)
        f_off_min = _safe_float(off_min)
        delta = f_on - f_off
        stability = self.evaluator.evaluate_minutes_stability(min(f_on_min, f_off_min))

        interp = (
            f"Team scoring margin was {f_on:+.1f} on-court vs {f_off:+.1f} off-court ({delta:+.1f} net differential). "
            "The statistic is descriptive of the observed split across these games and does not establish causal individual impact."
        )

        limitations = [
            "On/Off splits are sensitive to substitution patterns and the quality of opposing bench units.",
            f"Off-court sample ({_safe_int(f_off_min)} min) vs on-court sample ({_safe_int(f_on_min)} min)."
        ]

        return StructuredEvidenceInterpretation(
            category="On/Off Differential",
            metric_name="on_off_delta",
            headline=f"On/Off Net Differential: {delta:+.1f}",
            observation={"text": f"On-court: {f_on:+.1f} ({_safe_int(f_on_min)} min) | Off-court: {f_off:+.1f} ({_safe_int(f_off_min)} min).", "on_net": f_on, "off_net": f_off, "delta": delta},
            context={"text": f"Observed margin differential: {delta:+.1f} points/100 possessions."},
            volume_context={"text": f"On: {_safe_int(f_on_min)} min, Off: {_safe_int(f_off_min)} min."},
            efficiency_context={"net_delta": delta},
            stability_tier=stability,
            interpretation=interp,
            limitations=limitations,
            film_questions=["Examine team offensive and defensive flow when player sits vs when player enters the game."]
        )

    # -------------------------------------------------------------------------
    # 4.6. FULL PLAYER DOSSIER FINDINGS SYNTHESIZER
    # -------------------------------------------------------------------------
    def generate_player_dossier_findings(
        self,
        stats: Dict[str, Any],
        percentiles: Dict[str, Any],
        medians: Dict[str, Any],
        benchmark_meta: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Synthesizes structured findings for a player dossier."""
        if not stats or _safe_int(stats.get('gp', 0)) == 0:
            return []

        findings = []

        # 1. Scoring & True Shooting
        f_score = self.interpret_scoring(stats, percentiles, medians, benchmark_meta)
        findings.append(f_score.to_dict())

        # 2. Shooting Profile (Perimeter 3P or Interior 2P)
        fg3a = _safe_float(stats.get('total_fg3a', 0))
        if fg3a >= 10:
            f_3p = self.interpret_perimeter_shooting(stats, percentiles, medians, benchmark_meta)
            findings.append(f_3p.to_dict())
        else:
            fg2m = _safe_float(stats.get('total_fg2m', 0))
            fg2a = _safe_float(stats.get('total_fg2a', 0))
            fg2_pct = _safe_float(stats.get('fg2_pct', 0.0))
            fga = _safe_float(stats.get('total_fga', 0))
            f3a_rate = _safe_float(stats.get('f3a_rate', 0.0))
            gp = max(1, _safe_int(stats.get('gp', 1)))
            stability = self.evaluator.evaluate_fga_stability(fga)
            
            findings.append({
                "category": "Shot Diet & Interior Focus",
                "headline": f"Heavy Interior Orientation: {fg2_pct:.1f}% 2PT ({_safe_int(fg2m)}/{_safe_int(fg2a)})",
                "observation": f"Took {_safe_int(fg2a)} of {_safe_int(fga)} shots inside the arc ({fg2_pct:.1f}% 2P conversion).",
                "context": f"Takes only {f3a_rate:.1f}% of shots from 3-point range, concentrating scoring inside the paint.",
                "volume_note": f"Total 2-point volume: {_safe_int(fg2a)} attempts across {gp} matches.",
                "interpretation": "High-concentration interior scorer who consistently creates high-percentage looks around the rim.",
                "stability_tier": stability,
                "film_question": "Review paint touch finishes against rim protectors, post footwork, and dump-off / roll reception timing.",
                "limitations": ["Shot quality tracking unavailable in standard boxscores."],
                "structured_data": {}
            })

        # 3. Rebounding or Playmaking
        p_reb = _safe_float(percentiles.get('reb_per_40', 50.0))
        p_ast = _safe_float(percentiles.get('ast_per_40', 50.0))
        if p_reb >= p_ast and p_reb >= 65:
            f_reb = self.interpret_rebounding(stats, percentiles, medians, benchmark_meta)
            findings.append(f_reb.to_dict())
        else:
            f_ast = self.interpret_playmaking(stats, percentiles, medians, benchmark_meta)
            findings.append(f_ast.to_dict())

        return findings
