"""Automated Unit & Regression Tests for Player Development Trajectory Engine."""

import pytest
import pandas as pd
import numpy as np
from python.analytics.player_trends import (
    TrajectoryStatus,
    TrajectoryConfidence,
    evaluate_player_trajectory
)


def test_01_insufficient_sample_handling():
    """Verifies small sample players (<4 games) are safely classified as INSUFFICIENT_SAMPLE."""
    df_empty = pd.DataFrame()
    res_empty = evaluate_player_trajectory(df_empty, "PLY_TEST", "Test Player")
    assert res_empty.overall_status == TrajectoryStatus.INCONCLUSIVE
    assert res_empty.confidence == TrajectoryConfidence.INSUFFICIENT_SAMPLE

    df_small = pd.DataFrame({
        "game_date": ["2024-10-01", "2024-10-08"],
        "minutes": [10.0, 12.0],
        "points": [4, 6],
        "fga": [3, 5],
        "fta": [0, 2],
        "trb": [2, 3],
        "ast": [1, 1]
    })
    res_small = evaluate_player_trajectory(df_small, "PLY_TEST", "Test Player")
    assert res_small.overall_status == TrajectoryStatus.INCONCLUSIVE
    assert res_small.confidence == TrajectoryConfidence.INSUFFICIENT_SAMPLE


def test_02_improving_trajectory_detection():
    """Verifies upward scoring and efficiency trajectory is correctly identified."""
    # 8 games: first 4 modest, last 4 surging
    df = pd.DataFrame({
        "game_date": [f"2024-10-{i:02d}" for i in range(1, 9)],
        "minutes": [20.0] * 8,
        "points": [10, 10, 10, 10, 18, 20, 19, 21],  # baseline 14.75, recent 19.5 (+4.75)
        "fga": [8, 8, 8, 8, 12, 12, 12, 12],
        "fta": [2, 2, 2, 2, 4, 4, 4, 4],
        "trb": [4, 4, 4, 4, 4, 4, 4, 4],
        "ast": [2, 2, 2, 2, 2, 2, 2, 2]
    })
    res = evaluate_player_trajectory(df, "PLY_TEST", "Test Player")
    assert res.overall_status == TrajectoryStatus.IMPROVING
    assert res.confidence == TrajectoryConfidence.MODERATE_EVIDENCE
    assert res.delta_ppg > 3.0
    assert len(res.improving_areas) > 0
    assert len(res.film_hypotheses) > 0


def test_03_stable_trajectory_within_baseline():
    """Verifies steady performance matching baseline is classified as STABLE."""
    df = pd.DataFrame({
        "game_date": [f"2024-10-{i:02d}" for i in range(1, 17)],
        "minutes": [25.0] * 16,
        "points": [12] * 16,
        "fga": [10] * 16,
        "fta": [2] * 16,
        "trb": [5] * 16,
        "ast": [3] * 16
    })
    res = evaluate_player_trajectory(df, "PLY_TEST", "Test Player")
    assert res.overall_status == TrajectoryStatus.STABLE
    assert res.confidence == TrajectoryConfidence.STRONG_EVIDENCE
    assert abs(res.delta_ppg) < 0.1


def test_04_role_change_detection():
    """Verifies minutes contraction or expansion is flagged in the trajectory summary."""
    df_minutes_drop = pd.DataFrame({
        "game_date": [f"2024-10-{i:02d}" for i in range(1, 9)],
        "minutes": [25.0, 25.0, 25.0, 25.0, 10.0, 10.0, 10.0, 10.0],
        "points": [10, 10, 10, 10, 4, 4, 4, 4],
        "fga": [8, 8, 8, 8, 3, 3, 3, 3],
        "fta": [2, 2, 2, 2, 0, 0, 0, 0],
        "trb": [4, 4, 4, 4, 1, 1, 1, 1],
        "ast": [2, 2, 2, 2, 0, 0, 0, 0]
    })
    res = evaluate_player_trajectory(df_minutes_drop, "PLY_TEST", "Test Player")
    assert res.role_change_note is not None
    assert "Rotation contraction" in res.role_change_note
