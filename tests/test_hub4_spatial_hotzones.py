import math
import pytest
import pandas as pd
import numpy as np
from app.services.data_service import DataService
from app.components.court_plot import (
    ZONE_DEFINITIONS,
    classify_granular_zone,
    calculate_spatial_zone_summary,
    create_court_shapes,
    render_shot_chart,
    render_shot_comparison_chart,
    is_inside_3pt_line
)

@pytest.fixture
def data_service():
    return DataService()

@pytest.fixture
def falcons_shots(data_service):
    return data_service.get_team_shots('SEA_2025', is_falcons_only=True)

class TestGranularZoneClassification:
    def test_all_10_zones_defined(self):
        assert len(ZONE_DEFINITIONS) == 10
        expected_zones = {
            'PAINT_NON_RA', 'RESTRICTED_AREA', 'MID_RANGE_LEFT', 'MID_RANGE_CENTER',
            'MID_RANGE_RIGHT', 'CORNER_3_LEFT', 'CORNER_3_RIGHT', 'ABOVE_BREAK_3_LEFT',
            'ABOVE_BREAK_3_CENTER', 'ABOVE_BREAK_3_RIGHT'
        }
        assert set(ZONE_DEFINITIONS.keys()) == expected_zones

    def test_restricted_area_classification(self):
        assert classify_granular_zone(140.0, 25.0, '2PT', 'OBSERVED') == 'RESTRICTED_AREA'
        assert classify_granular_zone(150.0, 35.0, '2PT', 'OBSERVED') == 'RESTRICTED_AREA'

    def test_paint_non_ra_classification(self):
        assert classify_granular_zone(140.0, 70.0, '2PT', 'OBSERVED') == 'PAINT_NON_RA'
        assert classify_granular_zone(100.0, 40.0, '2PT', 'OBSERVED') == 'PAINT_NON_RA'

    def test_corner_3pt_classification(self):
        assert classify_granular_zone(15.0, 25.0, '3PT', 'OBSERVED') == 'CORNER_3_LEFT'
        assert classify_granular_zone(265.0, 25.0, '3PT', 'OBSERVED') == 'CORNER_3_RIGHT'

    def test_above_break_3pt_classification(self):
        assert classify_granular_zone(50.0, 150.0, '3PT', 'OBSERVED') == 'ABOVE_BREAK_3_LEFT'
        assert classify_granular_zone(140.0, 180.0, '3PT', 'OBSERVED') == 'ABOVE_BREAK_3_CENTER'
        assert classify_granular_zone(230.0, 150.0, '3PT', 'OBSERVED') == 'ABOVE_BREAK_3_RIGHT'

    def test_unobserved_or_nan_coords(self):
        assert classify_granular_zone(np.nan, 25.0, '2PT', 'OBSERVED') == 'UNKNOWN'
        assert classify_granular_zone(140.0, 25.0, '2PT', 'NOT_AVAILABLE') == 'UNKNOWN'


class TestCompleteSpatialPartitionAndCoverage:
    def test_100_percent_grid_coverage_no_gaps_no_overlaps(self):
        """Tests 40,000 grid points across the half-court ensuring every point maps to exactly 1 zone."""
        xs = np.linspace(0.5, 279.5, 200)
        ys = np.linspace(0.5, 199.5, 200)
        
        for x in xs:
            for y in ys:
                z = classify_granular_zone(x, y)
                assert z in ZONE_DEFINITIONS, f"Gapped / unclassified coordinate at ({x}, {y}): got {z}"

    def test_polygon_area_conservation_shoelace(self):
        """Verifies that the sum of polygon areas strictly equals half-court area (280 * 200 = 56,000)."""
        def poly_area(x, y):
            return 0.5 * abs(sum(x[i] * y[i+1] - x[i+1] * y[i] for i in range(len(x)-1)))

        total_poly_area = 0.0
        # For Restricted Area + Paint Non-RA, Paint box covers the RA footprint, so we sum Paint box + non-paint zones
        for zid, zinfo in ZONE_DEFINITIONS.items():
            if zid == 'RESTRICTED_AREA':
                continue  # RA sits inside Paint box footprint
            total_poly_area += poly_area(zinfo['x'], zinfo['y'])

        # Total area of half court [0, 280] x [0, 200] is 56,000.0
        assert abs(total_poly_area - 56000.0) < 5.0, f"Total polygon area {total_poly_area} != 56000.0"

    def test_boundary_perturbation_resilience(self):
        """Tests critical boundaries with +/- 0.1 coordinate perturbations."""
        # 1. Paint vs Mid-Range Left / Right
        assert classify_granular_zone(94.9, 60.0) == 'MID_RANGE_LEFT'
        assert classify_granular_zone(95.1, 60.0) == 'PAINT_NON_RA'
        assert classify_granular_zone(184.9, 60.0) == 'PAINT_NON_RA'
        assert classify_granular_zone(185.1, 60.0) == 'MID_RANGE_RIGHT'

        # 2. Paint vs Mid-Range Center (Free Throw line y=85)
        assert classify_granular_zone(140.0, 84.9) == 'PAINT_NON_RA'
        assert classify_granular_zone(140.0, 85.1) == 'MID_RANGE_CENTER'

        # 3. Corner 3 vs Wing 3 (y=50)
        assert classify_granular_zone(15.0, 49.9) == 'CORNER_3_LEFT'
        assert classify_granular_zone(15.0, 50.1) == 'ABOVE_BREAK_3_LEFT'
        assert classify_granular_zone(265.0, 49.9) == 'CORNER_3_RIGHT'
        assert classify_granular_zone(265.0, 50.1) == 'ABOVE_BREAK_3_RIGHT'

    def test_hard_shot_type_constraints(self):
        """Guarantees 3PT never classifies as 2PT zone and 2PT never classifies as 3PT zone."""
        # A 3PT tagged shot near the rim must map to a 3PT zone
        z_3p = classify_granular_zone(140.0, 25.0, shot_type='3PT')
        assert '3' in z_3p or 'CORNER' in z_3p

        # A 2PT tagged shot beyond the arc must map to a 2PT zone
        z_2p = classify_granular_zone(140.0, 180.0, shot_type='2PT')
        assert z_2p in ['RESTRICTED_AREA', 'PAINT_NON_RA', 'MID_RANGE_LEFT', 'MID_RANGE_CENTER', 'MID_RANGE_RIGHT']


class TestSpatialZoneSummaryCalculations:
    def test_summary_with_real_falcons_shots(self, falcons_shots):
        assert len(falcons_shots) == 1045
        summaries = calculate_spatial_zone_summary(falcons_shots)
        assert len(summaries) == 10

        ra_sum = summaries['RESTRICTED_AREA']
        assert ra_sum['fga'] > 400
        assert ra_sum['fgm'] > 200
        assert ra_sum['fg_pct'] > 55.0
        assert any(t in ra_sum['tier_label'] for t in ['🔥', '⚡', 'Above Baseline'])
        assert ra_sum['color_hex'] in ['#0284C7', '#38BDF8']

    def test_bayesian_shrinkage_dampens_small_sample(self):
        df_small = pd.DataFrame([
            {'x_coord': 50.0, 'y_coord': 150.0, 'shot_type': '3PT', 'is_made': True, 'points': 3, 'shot_location_status': 'OBSERVED'},
            {'x_coord': 50.0, 'y_coord': 150.0, 'shot_type': '3PT', 'is_made': True, 'points': 3, 'shot_location_status': 'OBSERVED'},
        ])
        sums = calculate_spatial_zone_summary(df_small)
        z = sums['ABOVE_BREAK_3_LEFT']
        assert z['fga'] == 2
        assert z['fg_pct'] == 100.0
        raw_delta = 100.0 - 25.6
        assert z['shrunk_delta'] < raw_delta
        assert abs(z['shrunk_delta'] - round(raw_delta * (2.0 / 7.0), 1)) <= 0.2

    def test_empty_dataframe_handling(self):
        df_empty = pd.DataFrame(columns=['x_coord', 'y_coord', 'shot_type', 'is_made', 'points'])
        sums = calculate_spatial_zone_summary(df_empty)
        assert len(sums) == 10
        for zid, z in sums.items():
            assert z['fga'] == 0
            assert z['fgm'] == 0
            assert z['fg_pct'] == 0.0
            assert z['shrunk_delta'] == 0.0


class TestCourtRenderingAndGeometryIntegrity:
    def test_render_shot_chart_modes(self, falcons_shots):
        fig_both = render_shot_chart(falcons_shots, show_hot_zones=True, show_shots=True, show_labels=True)
        assert len(fig_both.data) >= 12
        assert len(fig_both.layout.annotations) >= 10

        fig_hot_only = render_shot_chart(falcons_shots, show_hot_zones=True, show_shots=False, show_labels=True)
        assert len(fig_hot_only.data) == 10

        fig_shots_only = render_shot_chart(falcons_shots, show_hot_zones=False, show_shots=True, show_labels=False)
        assert len(fig_shots_only.data) == 2

    def test_head_to_head_strictly_identical_geometry(self, falcons_shots):
        df_a = falcons_shots[falcons_shots['player_name'] == 'Julian Wagner']
        df_b = falcons_shots[falcons_shots['player_name'] == 'Lukas Weber']

        fig_cmp = render_shot_comparison_chart(
            df_a, df_b,
            name_a='Julian Wagner', name_b='Lukas Weber',
            show_hot_zones=True, show_shots=True, scale_mode='shared'
        )

        assert list(fig_cmp.layout.xaxis.range) == [-10, 290]
        assert list(fig_cmp.layout.xaxis2.range) == [-10, 290]
        assert list(fig_cmp.layout.yaxis.range) == [-10, 210]
        assert list(fig_cmp.layout.yaxis2.range) == [-10, 210]

        assert fig_cmp.layout.yaxis.scaleanchor == 'x'
        assert fig_cmp.layout.yaxis2.scaleanchor == 'x2'
        assert fig_cmp.layout.yaxis.scaleratio == 1
        assert fig_cmp.layout.yaxis2.scaleratio == 1
