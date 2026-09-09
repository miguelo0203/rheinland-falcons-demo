"""Centralized Basketball Metric Semantics & Epistemic Direction Registry.

Rheinland Falcons Basketball — JBBL / NBBL Longitudinal Basketball Intelligence Platform.

Provides a single source of truth for:
- Semantic Direction (HIGHER_IS_BETTER, LOWER_IS_BETTER, CONTEXT_DEPENDENT, TARGET_RANGE, DESCRIPTIVE_ONLY)
- Percentile Calculation & Correct Inversion (Higher percentile always = Better performance)
- Delta and Trend Arrow Interpretation (Respecting metric direction)
- Color Semantics (Communicating desirability, not raw numerical magnitude)
- Contextual Tiers (Descriptive tempo/style tiers vs evaluative performance tiers)
- Default Table Sorting Preferences
- Concise Coach-Facing Explanations & Epistemic Limitations
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd


class MetricSemanticDirection(str, Enum):
    HIGHER_IS_BETTER = "HIGHER_IS_BETTER"
    LOWER_IS_BETTER = "LOWER_IS_BETTER"
    CONTEXT_DEPENDENT = "CONTEXT_DEPENDENT"
    TARGET_RANGE = "TARGET_RANGE"
    DESCRIPTIVE_ONLY = "DESCRIPTIVE_ONLY"


class TrendEvaluation(str, Enum):
    IMPROVED = "IMPROVED"
    DETERIORATED = "DETERIORATED"
    STABLE = "STABLE"
    FASTER_PACE = "FASTER_PACE"
    SLOWER_PACE = "SLOWER_PACE"
    INCREASED_VOLUME = "INCREASED_VOLUME"
    DECREASED_VOLUME = "DECREASED_VOLUME"
    EXPANDED_ROLE = "EXPANDED_ROLE"
    REDUCED_ROLE = "REDUCED_ROLE"
    INCONCLUSIVE = "INCONCLUSIVE"


@dataclass
class MetricSemanticDefinition:
    canonical_name: str
    ui_label: str
    category: str
    direction: MetricSemanticDirection
    formula: str
    denominator: str
    unit: str
    is_derived: bool
    target_range: Optional[Tuple[float, float]] = None
    sorting_preference: str = "DESC"  # "DESC" or "ASC"
    coach_explanation: str = ""
    limitations: List[str] = field(default_factory=list)

    def calculate_percentile(self, val: float, distribution: pd.Series) -> float:
        """Calculates percentile rank respecting basketball semantic direction.
        
        For HIGHER_IS_BETTER: (distribution <= val).mean() * 100
        For LOWER_IS_BETTER:  (distribution >= val).mean() * 100  (Inverted: lower raw value = higher percentile)
        For CONTEXT_DEPENDENT / DESCRIPTIVE: (distribution <= val).mean() * 100
        """
        if distribution.empty or pd.isna(val):
            return 50.0
        clean_dist = distribution.dropna()
        if len(clean_dist) == 0:
            return 50.0

        if self.direction == MetricSemanticDirection.LOWER_IS_BETTER:
            pct = (clean_dist >= val).mean() * 100.0
        else:
            pct = (clean_dist <= val).mean() * 100.0
            
        return round(float(np.clip(pct, 0.0, 100.0)), 1)

    def classify_contextual_tier(self, percentile: float, raw_val: Optional[float] = None) -> str:
        """Classifies performance or descriptive tier based on percentile and semantic direction."""
        pct = float(percentile)
        
        if self.direction == MetricSemanticDirection.CONTEXT_DEPENDENT:
            if self.canonical_name == "pace":
                if pct >= 75:
                    return "HIGH_TEMPO"
                elif pct <= 25:
                    return "HALF_COURT_TEMPO"
                return "BALANCED_TEMPO"
            elif self.canonical_name in ["mpg", "minutes", "min_share_pct"]:
                if pct >= 80:
                    return "CORE_ROTATION_STARTER"
                elif pct >= 40:
                    return "ROTATIONAL_CONTRIBUTOR"
                return "DEVELOPMENTAL_DEPTH"
            elif self.canonical_name in ["f3a_rate", "three_point_attempt_rate"]:
                if pct >= 75:
                    return "PERIMETER_HEAVY_DIET"
                elif pct <= 25:
                    return "INTERIOR_HEAVY_DIET"
                return "BALANCED_SHOT_DIET"
            return "CONTEXTUAL"

        if self.direction == MetricSemanticDirection.DESCRIPTIVE_ONLY:
            return "DESCRIPTIVE"

        # Evaluative Tiers
        if pct >= 80:
            return "TOP_TIER"
        elif pct >= 60:
            return "ABOVE_AVERAGE"
        elif pct >= 40:
            return "AVERAGE"
        elif pct >= 20:
            return "BELOW_AVERAGE"
        return "BOTTOM_TIER"

    def evaluate_delta(self, delta: float, threshold: float = 0.05) -> TrendEvaluation:
        """Evaluates whether a numerical change represents improvement, deterioration, or context change."""
        if abs(delta) < threshold:
            return TrendEvaluation.STABLE

        if self.direction == MetricSemanticDirection.HIGHER_IS_BETTER:
            return TrendEvaluation.IMPROVED if delta > 0 else TrendEvaluation.DETERIORATED
        elif self.direction == MetricSemanticDirection.LOWER_IS_BETTER:
            return TrendEvaluation.IMPROVED if delta < 0 else TrendEvaluation.DETERIORATED
        elif self.direction == MetricSemanticDirection.CONTEXT_DEPENDENT:
            if self.canonical_name == "pace":
                return TrendEvaluation.FASTER_PACE if delta > 0 else TrendEvaluation.SLOWER_PACE
            elif self.canonical_name in ["mpg", "minutes", "min_share_pct"]:
                return TrendEvaluation.EXPANDED_ROLE if delta > 0 else TrendEvaluation.REDUCED_ROLE
            return TrendEvaluation.INCREASED_VOLUME if delta > 0 else TrendEvaluation.DECREASED_VOLUME
        else:
            return TrendEvaluation.INCREASED_VOLUME if delta > 0 else TrendEvaluation.DECREASED_VOLUME

    def get_color_class(self, percentile: float) -> str:
        """Returns visual color class based on performance desirability, NOT numerical magnitude."""
        if self.direction in [MetricSemanticDirection.CONTEXT_DEPENDENT, MetricSemanticDirection.DESCRIPTIVE_ONLY]:
            return "neutral"

        pct = float(percentile)
        if pct >= 75:
            return "positive"
        elif pct >= 40:
            return "neutral"
        return "negative"


METRIC_SEMANTICS_REGISTRY: Dict[str, MetricSemanticDefinition] = {
    "ortg": MetricSemanticDefinition(
        canonical_name="ortg",
        ui_label="Offensive Rating (ORTG)",
        category="Team Efficiency",
        direction=MetricSemanticDirection.HIGHER_IS_BETTER,
        formula="100 * Points / Possessions",
        denominator="Team Offensive Possessions",
        unit="Pts / 100 poss",
        is_derived=True,
        sorting_preference="DESC",
        coach_explanation="Points generated per 100 offensive possessions. Higher indicates superior offensive efficiency regardless of game pace.",
        limitations=["Sensitive to small sample sizes (<400 possessions) and garbage time variance."]
    ),
    "drtg": MetricSemanticDefinition(
        canonical_name="drtg",
        ui_label="Defensive Rating (DRTG)",
        category="Team Efficiency",
        direction=MetricSemanticDirection.LOWER_IS_BETTER,
        formula="100 * Opponent Points / Opponent Possessions",
        denominator="Opponent Offensive Possessions",
        unit="Opp Pts / 100 poss",
        is_derived=True,
        sorting_preference="ASC",
        coach_explanation="Points allowed per 100 opponent possessions. LOWER IS BETTER. A lower number indicates stronger defensive efficiency.",
        limitations=["Opponent shooting variance (especially 3P%) heavily influences DRTG over small sample sizes."]
    ),
    "net_rtg": MetricSemanticDefinition(
        canonical_name="net_rtg",
        ui_label="Net Rating (NetRtg)",
        category="Team Efficiency",
        direction=MetricSemanticDirection.HIGHER_IS_BETTER,
        formula="ORTG - DRTG",
        denominator="100 Possessions",
        unit="Pts / 100 poss",
        is_derived=True,
        sorting_preference="DESC",
        coach_explanation="Net scoring differential per 100 possessions. The definitive measure of overall team dominance.",
        limitations=["Cumulative metric that does not isolate individual player contributions without lineup regression."]
    ),
    "efg_pct": MetricSemanticDefinition(
        canonical_name="efg_pct",
        ui_label="Effective Field Goal % (eFG%)",
        category="Four Factors",
        direction=MetricSemanticDirection.HIGHER_IS_BETTER,
        formula="(FGM + 0.5 * 3PM) / FGA * 100",
        denominator="Field Goal Attempts (FGA)",
        unit="%",
        is_derived=True,
        sorting_preference="DESC",
        coach_explanation="Shooting efficiency adjusting for 3-point makes. The single strongest empirical predictor of winning in JBBL (R² ≈ 70%).",
        limitations=["Does not incorporate free throw generation."]
    ),
    "tov_pct": MetricSemanticDefinition(
        canonical_name="tov_pct",
        ui_label="Turnover Rate (TOV%)",
        category="Four Factors",
        direction=MetricSemanticDirection.LOWER_IS_BETTER,
        formula="TOV / (FGA + 0.44 * FTA + TOV) * 100",
        denominator="Estimated Possessions",
        unit="%",
        is_derived=True,
        sorting_preference="ASC",
        coach_explanation="Percentage of offensive possessions ending in a turnover. LOWER IS BETTER. Turnovers directly concede opponent transition points.",
        limitations=["Does not distinguish dead-ball turnovers from live-ball turnovers without play-by-play data."]
    ),
    "orb_pct": MetricSemanticDefinition(
        canonical_name="orb_pct",
        ui_label="Offensive Rebound % (ORB%)",
        category="Four Factors",
        direction=MetricSemanticDirection.HIGHER_IS_BETTER,
        formula="ORB / (ORB + Opp DRB) * 100",
        denominator="Total Available Rebound Opportunities",
        unit="%",
        is_derived=True,
        sorting_preference="DESC",
        coach_explanation="Percentage of missed shots recovered by the offensive team. Measures second-chance opportunity generation.",
        limitations=["Aggressive crashing can compromise defensive transition balance if not tactically managed."]
    ),
    "ftr": MetricSemanticDefinition(
        canonical_name="ftr",
        ui_label="Free Throw Rate (FTR)",
        category="Four Factors",
        direction=MetricSemanticDirection.HIGHER_IS_BETTER,
        formula="FTA / FGA",
        denominator="Field Goal Attempts (FGA)",
        unit="FTA / FGA ratio",
        is_derived=True,
        sorting_preference="DESC",
        coach_explanation="Frequency of drawing fouls and reaching the free throw line relative to field goal attempts.",
        limitations=["Dependent on referee whistle tendencies and paint penetration style."]
    ),
    "pace": MetricSemanticDefinition(
        canonical_name="pace",
        ui_label="Pace (Possessions / 40 Min)",
        category="Team Style & Tempo",
        direction=MetricSemanticDirection.CONTEXT_DEPENDENT,
        formula="Possessions * 40 / Game Minutes",
        denominator="40 Regulation Minutes",
        unit="Poss / 40m",
        is_derived=True,
        sorting_preference="DESC",
        coach_explanation="Game tempo / estimated possessions per 40 regulation minutes. CONTEXT DEPENDENT: Faster is not inherently better. Pace explains <1% of win variance in JBBL.",
        limitations=["A high pace inflates raw counting totals (points, rebounds, turnovers) without indicating higher efficiency."]
    ),
    "ppg": MetricSemanticDefinition(
        canonical_name="ppg",
        ui_label="Points Per Game (PPG)",
        category="Scoring Production",
        direction=MetricSemanticDirection.HIGHER_IS_BETTER,
        formula="Total Points / Games Played",
        denominator="Games Played (GP)",
        unit="PTS",
        is_derived=True,
        sorting_preference="DESC",
        coach_explanation="Average points scored per game. Reflects overall scoring volume; heavily influenced by playing time and team pace.",
        limitations=["Conflates playing time with per-minute scoring ability."]
    ),
    "opp_ppg": MetricSemanticDefinition(
        canonical_name="opp_ppg",
        ui_label="Opponent PPG (Points Allowed)",
        category="Team Defense",
        direction=MetricSemanticDirection.LOWER_IS_BETTER,
        formula="Total Opponent Points / Games Played",
        denominator="Games Played (GP)",
        unit="Opp PTS",
        is_derived=True,
        sorting_preference="ASC",
        coach_explanation="Average points allowed per game. LOWER IS BETTER. Reflects raw points conceded; influenced by opponent pace.",
        limitations=["Heavily influenced by pace."]
    ),
    "win_pct": MetricSemanticDefinition(
        canonical_name="win_pct",
        ui_label="Win Percentage (Win %)",
        category="Team Performance",
        direction=MetricSemanticDirection.HIGHER_IS_BETTER,
        formula="Wins / Games Played",
        denominator="Games Played (GP)",
        unit="%",
        is_derived=True,
        sorting_preference="DESC",
        coach_explanation="Proportion of official matches won.",
        limitations=["Binary match outcome metric; does not reflect point differential."]
    ),
    "pts_per_40": MetricSemanticDefinition(
        canonical_name="pts_per_40",
        ui_label="Points Per 40 Min (PTS/40)",
        category="Player Production",
        direction=MetricSemanticDirection.HIGHER_IS_BETTER,
        formula="Points * 40 / Minutes Played",
        denominator="Minutes Played",
        unit="PTS / 40m",
        is_derived=True,
        sorting_preference="DESC",
        coach_explanation="Normalized scoring output per 40 regulation minutes. Removes playing-time bias to evaluate pure scoring rate.",
        limitations=["Can artificially inflate per-40 rates for low-minute bench players with small samples."]
    ),
    "ts_pct": MetricSemanticDefinition(
        canonical_name="ts_pct",
        ui_label="True Shooting % (TS%)",
        category="Player Efficiency",
        direction=MetricSemanticDirection.HIGHER_IS_BETTER,
        formula="Points / (2 * (FGA + 0.44 * FTA)) * 100",
        denominator="True Shooting Attempts (TSA)",
        unit="%",
        is_derived=True,
        sorting_preference="DESC",
        coach_explanation="Holistic individual shooting efficiency capturing 2-pointers, 3-pointers, and free throws in a single metric.",
        limitations=["Standard 0.44 FTA coefficient is an empirical approximation."]
    ),
    "reb_per_40": MetricSemanticDefinition(
        canonical_name="reb_per_40",
        ui_label="Rebounds Per 40 Min (REB/40)",
        category="Player Production",
        direction=MetricSemanticDirection.HIGHER_IS_BETTER,
        formula="Total Rebounds * 40 / Minutes Played",
        denominator="Minutes Played",
        unit="REB / 40m",
        is_derived=True,
        sorting_preference="DESC",
        coach_explanation="Normalized rebounding output per 40 regulation minutes.",
        limitations=["Does not separate contested from uncontested rebounds."]
    ),
    "ast_per_40": MetricSemanticDefinition(
        canonical_name="ast_per_40",
        ui_label="Assists Per 40 Min (AST/40)",
        category="Player Production",
        direction=MetricSemanticDirection.HIGHER_IS_BETTER,
        formula="Assists * 40 / Minutes Played",
        denominator="Minutes Played",
        unit="AST / 40m",
        is_derived=True,
        sorting_preference="DESC",
        coach_explanation="Normalized playmaking and assist creation per 40 regulation minutes.",
        limitations=["Dependent on teammates converting created opportunities."]
    ),
    "ast_to_tov": MetricSemanticDefinition(
        canonical_name="ast_to_tov",
        ui_label="Assist-to-Turnover Ratio (AST/TOV)",
        category="Ball Security",
        direction=MetricSemanticDirection.HIGHER_IS_BETTER,
        formula="Assists / Turnovers",
        denominator="Turnovers (TOV)",
        unit="Ratio",
        is_derived=True,
        target_range=(1.5, 3.5),
        sorting_preference="DESC",
        coach_explanation="Facilitation efficiency and decision-making security. Above 1.5 indicates clean ball distribution; above 2.0 is elite.",
        limitations=["High-usage lead ball-handlers face higher turnover exposure than spot-up passers."]
    ),
    "def_disruption": MetricSemanticDefinition(
        canonical_name="def_disruption",
        ui_label="Defensive Disruption Rate (STL+BLK/40)",
        category="Player Defense",
        direction=MetricSemanticDirection.HIGHER_IS_BETTER,
        formula="(Steals + Blocks) * 40 / Minutes Played",
        denominator="Minutes Played",
        unit="Events / 40m",
        is_derived=True,
        sorting_preference="DESC",
        coach_explanation="Defensive playmaking event rate combining steals and blocked shots per 40 minutes.",
        limitations=["Gambling for steals or blocks can compromise defensive positioning."]
    ),
    "tov_per_40": MetricSemanticDefinition(
        canonical_name="tov_per_40",
        ui_label="Turnovers Per 40 Min (TOV/40)",
        category="Ball Security",
        direction=MetricSemanticDirection.LOWER_IS_BETTER,
        formula="Turnovers * 40 / Minutes Played",
        denominator="Minutes Played",
        unit="TOV / 40m",
        is_derived=True,
        sorting_preference="ASC",
        coach_explanation="Turnover frequency per 40 regulation minutes. LOWER IS BETTER. Measures ball protection under court exposure.",
        limitations=["Lead initiators naturally have higher rates than off-ball finishers."]
    ),
    "f3a_rate": MetricSemanticDefinition(
        canonical_name="f3a_rate",
        ui_label="3-Point Attempt Rate (3PAr)",
        category="Shot Diet & Role",
        direction=MetricSemanticDirection.CONTEXT_DEPENDENT,
        formula="3PA / FGA * 100",
        denominator="Total Field Goal Attempts (FGA)",
        unit="%",
        is_derived=True,
        sorting_preference="DESC",
        coach_explanation="Proportion of a player's field goal attempts taken from beyond the arc. Describes tactical role and perimeter orientation.",
        limitations=["Role description, not quality: high 3PAr is only valuable if converted efficiently."]
    ),
    "mpg": MetricSemanticDefinition(
        canonical_name="mpg",
        ui_label="Minutes Per Game (MPG)",
        category="Rotation Role",
        direction=MetricSemanticDirection.CONTEXT_DEPENDENT,
        formula="Total Minutes / Games Played",
        denominator="Games Played (GP)",
        unit="MIN",
        is_derived=True,
        sorting_preference="DESC",
        coach_explanation="Average playing time per game. Reflects coach trust and rotation hierarchy.",
        limitations=["Descriptive volume; playing more minutes is not inherently a mark of statistical efficiency."]
    ),
    "fg_pct": MetricSemanticDefinition(
        canonical_name="fg_pct",
        ui_label="Field Goal % (FG%)",
        category="Shooting Efficiency",
        direction=MetricSemanticDirection.HIGHER_IS_BETTER,
        formula="FGM / FGA * 100",
        denominator="Field Goal Attempts (FGA)",
        unit="%",
        is_derived=True,
        sorting_preference="DESC",
        coach_explanation="Traditional field goal conversion percentage.",
        limitations=["Does not weight 3-point makes higher than 2-point makes; prefer eFG% or TS%."]
    ),
    "fg3_pct": MetricSemanticDefinition(
        canonical_name="fg3_pct",
        ui_label="3-Point % (3P%)",
        category="Shooting Efficiency",
        direction=MetricSemanticDirection.HIGHER_IS_BETTER,
        formula="3PM / 3PA * 100",
        denominator="3-Point Attempts (3PA)",
        unit="%",
        is_derived=True,
        sorting_preference="DESC",
        coach_explanation="Perimeter conversion percentage.",
        limitations=["Requires high attempt sample (>=200 3PA) to stabilize; single-season small samples are noisy."]
    ),
    "rpg": MetricSemanticDefinition(
        canonical_name="rpg",
        ui_label="Rebounds Per Game (RPG)",
        category="Player Production",
        direction=MetricSemanticDirection.HIGHER_IS_BETTER,
        formula="Total Rebounds / Games Played",
        denominator="Games Played (GP)",
        unit="REB",
        is_derived=True,
        sorting_preference="DESC",
        coach_explanation="Average rebounds secured per game.",
        limitations=["Heavily influenced by playing time."]
    ),
    "apg": MetricSemanticDefinition(
        canonical_name="apg",
        ui_label="Assists Per Game (APG)",
        category="Player Production",
        direction=MetricSemanticDirection.HIGHER_IS_BETTER,
        formula="Total Assists / Games Played",
        denominator="Games Played (GP)",
        unit="AST",
        is_derived=True,
        sorting_preference="DESC",
        coach_explanation="Average assists dished per game.",
        limitations=["Heavily influenced by playing time."]
    ),
    "spg": MetricSemanticDefinition(
        canonical_name="spg",
        ui_label="Steals Per Game (SPG)",
        category="Player Defense",
        direction=MetricSemanticDirection.HIGHER_IS_BETTER,
        formula="Total Steals / Games Played",
        denominator="Games Played (GP)",
        unit="STL",
        is_derived=True,
        sorting_preference="DESC",
        coach_explanation="Average steals per game.",
        limitations=["Heavily influenced by playing time."]
    ),
    "bpg": MetricSemanticDefinition(
        canonical_name="bpg",
        ui_label="Blocks Per Game (BPG)",
        category="Player Defense",
        direction=MetricSemanticDirection.HIGHER_IS_BETTER,
        formula="Total Blocks / Games Played",
        denominator="Games Played (GP)",
        unit="BLK",
        is_derived=True,
        sorting_preference="DESC",
        coach_explanation="Average blocks per game.",
        limitations=["Heavily influenced by playing time."]
    ),
}


def get_metric_semantic(metric_name: str) -> MetricSemanticDefinition:
    norm_key = str(metric_name).lower().strip()
    if norm_key in METRIC_SEMANTICS_REGISTRY:
        return METRIC_SEMANTICS_REGISTRY[norm_key]
    
    if "drtg" in norm_key or "opp_" in norm_key or "tov" in norm_key:
        direction = MetricSemanticDirection.LOWER_IS_BETTER
        sort_pref = "ASC"
    elif "pace" in norm_key or "mpg" in norm_key or "minutes" in norm_key or "rate" in norm_key:
        direction = MetricSemanticDirection.CONTEXT_DEPENDENT
        sort_pref = "DESC"
    else:
        direction = MetricSemanticDirection.HIGHER_IS_BETTER
        sort_pref = "DESC"

    return MetricSemanticDefinition(
        canonical_name=norm_key,
        ui_label=norm_key.replace("_", " ").title(),
        category="General Analytics",
        direction=direction,
        formula="Raw aggregation",
        denominator="Context",
        unit="",
        is_derived=True,
        sorting_preference=sort_pref,
        coach_explanation="General analytical dimension."
    )
