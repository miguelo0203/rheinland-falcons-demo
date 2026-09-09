"""Automated Unit & Regression Tests for Metric Semantics Registry & Epistemic Rules."""

import pytest
import pandas as pd
import numpy as np
from python.analytics.metric_semantics import (
    MetricSemanticDirection,
    TrendEvaluation,
    get_metric_semantic,
    METRIC_SEMANTICS_REGISTRY
)


def test_01_all_canonical_metrics_registered():
    """Verifies all core analytical metrics are present in registry."""
    core_metrics = [
        "ortg", "drtg", "net_rtg", "efg_pct", "tov_pct", "orb_pct", "ftr",
        "pace", "ppg", "opp_ppg", "win_pct", "pts_per_40", "ts_pct",
        "reb_per_40", "ast_per_40", "ast_to_tov", "def_disruption", "tov_per_40"
    ]
    for m in core_metrics:
        sem = get_metric_semantic(m)
        assert sem is not None
        assert sem.canonical_name == m
        assert len(sem.coach_explanation) > 0


def test_02_defensive_rating_inverted_percentile():
    """Verifies DRTG (lower is better) assigns higher percentiles to lower raw points allowed."""
    sem = get_metric_semantic("drtg")
    assert sem.direction == MetricSemanticDirection.LOWER_IS_BETTER
    assert sem.sorting_preference == "ASC"

    # Distribution of league DRTG: [80, 85, 90, 95, 100]
    dist = pd.Series([80.0, 85.0, 90.0, 95.0, 100.0])
    
    # Excellent defense: 80 points allowed -> should be 100th percentile (top defense)
    pct_top = sem.calculate_percentile(80.0, dist)
    assert pct_top == 100.0
    assert sem.classify_contextual_tier(pct_top) == "TOP_TIER"

    # Poor defense: 100 points allowed -> should be 20th percentile
    pct_bottom = sem.calculate_percentile(100.0, dist)
    assert pct_bottom == 20.0
    assert sem.classify_contextual_tier(pct_bottom) == "BELOW_AVERAGE"


def test_03_turnover_rate_inverted_percentile():
    """Verifies TOV% (lower is better) correctly rewards ball security with higher percentiles."""
    sem = get_metric_semantic("tov_pct")
    assert sem.direction == MetricSemanticDirection.LOWER_IS_BETTER
    assert sem.sorting_preference == "ASC"

    dist = pd.Series([15.0, 20.0, 25.0, 30.0])
    pct_clean = sem.calculate_percentile(15.0, dist)
    assert pct_clean == 100.0


def test_04_pace_context_dependent_style_tiers():
    """Verifies Pace is context-dependent and never uses derogatory performance labels."""
    sem = get_metric_semantic("pace")
    assert sem.direction == MetricSemanticDirection.CONTEXT_DEPENDENT
    
    # Fast pace (>75th %ile)
    assert sem.classify_contextual_tier(85.0) == "HIGH_TEMPO"
    # Slow half-court pace (<25th %ile)
    assert sem.classify_contextual_tier(15.0) == "HALF_COURT_TEMPO"
    # Balanced tempo
    assert sem.classify_contextual_tier(50.0) == "BALANCED_TEMPO"


def test_05_delta_trend_semantic_evaluation():
    """Verifies delta increases/decreases are evaluated according to metric direction."""
    # DRTG: 105 -> 98 (delta = -7.0) is IMPROVEMENT
    sem_drtg = get_metric_semantic("drtg")
    assert sem_drtg.evaluate_delta(-7.0) == TrendEvaluation.IMPROVED
    assert sem_drtg.evaluate_delta(+7.0) == TrendEvaluation.DETERIORATED

    # ORTG: 100 -> 110 (delta = +10.0) is IMPROVEMENT
    sem_ortg = get_metric_semantic("ortg")
    assert sem_ortg.evaluate_delta(+10.0) == TrendEvaluation.IMPROVED
    assert sem_ortg.evaluate_delta(-10.0) == TrendEvaluation.DETERIORATED

    # Pace: 70 -> 75 is FASTER_PACE, not better/worse
    sem_pace = get_metric_semantic("pace")
    assert sem_pace.evaluate_delta(+5.0) == TrendEvaluation.FASTER_PACE
    assert sem_pace.evaluate_delta(-5.0) == TrendEvaluation.SLOWER_PACE


def test_06_color_class_semantics():
    """Verifies color communicates desirability rather than raw magnitude."""
    sem_drtg = get_metric_semantic("drtg")
    # 90th percentile in defense (meaning top 10% fewest points conceded) is POSITIVE
    assert sem_drtg.get_color_class(90.0) == "positive"
    assert sem_drtg.get_color_class(20.0) == "negative"

    sem_pace = get_metric_semantic("pace")
    # Pace is always neutral
    assert sem_pace.get_color_class(95.0) == "neutral"
    assert sem_pace.get_color_class(10.0) == "neutral"
