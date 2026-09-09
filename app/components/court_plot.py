"""Interactive 2D FIBA Half-Court Shot Map & Spatial Hot Zones using Plotly.

Provides:
1. Standard FIBA half-court 280x200 geometry markings.
2. 10 granular tactical shooting zones with empirical baseline benchmarks.
3. Sample-size-aware Bayesian smoothed efficiency coloring (Hot Blue / Neutral Slate / Cold Red).
4. Volume-weighted opacity scaling.
5. Strict identical-geometry Head-to-Head subplots for Player A vs Player B.
"""

import math
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


# ==============================================================================
# 1. ZONE DEFINITIONS & BASELINES (FIBA 280x200 Coordinate Grid)
# ==============================================================================

# Exact FIBA 3PT Arc Geometry
_R_3P = math.sqrt(115.0**2 + 25.0**2)  # ~117.68602
_theta_c_r = math.atan2(25.0, 115.0)  # Corner 3 Right intersection angle (~0.21376 rad, 12.25 deg)
_theta_c_l = math.pi - _theta_c_r      # Corner 3 Left intersection angle (~2.92783 rad, 167.75 deg)
_theta_arc_r = math.acos(45.0 / _R_3P) # Sector partition angle at x=185 (~1.17753 rad, 67.47 deg)
_theta_arc_l = math.pi - _theta_arc_r  # Sector partition angle at x=95 (~1.96406 rad, 112.53 deg)

_N_CURVE = 25

# 1. Restricted Area (semicircle R=35 centered at 140, 25 down to baseline y=0)
_theta_ra = np.linspace(0, np.pi, _N_CURVE)
_ra_x = [175.0] + list(140.0 + 35.0 * np.cos(_theta_ra)) + [105.0, 175.0]
_ra_y = [0.0] + list(25.0 + 35.0 * np.sin(_theta_ra)) + [0.0, 0.0]

# 2. Mid-Range Left (bounded by baseline, paint left x=95, partition ray at x=95, and 3PT arc down to corner 3)
_theta_m_l = np.linspace(_theta_arc_l, _theta_c_l, _N_CURVE)
_m_l_x = [25.0, 95.0, 95.0] + list(140.0 + _R_3P * np.cos(_theta_m_l)) + [25.0]
_m_l_y = [0.0, 0.0, 85.0] + list(25.0 + _R_3P * np.sin(_theta_m_l)) + [0.0]

# 3. Mid-Range Right (bounded by baseline, corner 3 line, 3PT arc up to x=185, and paint right x=185)
_theta_m_r = np.linspace(_theta_c_r, _theta_arc_r, _N_CURVE)
_m_r_x = [185.0, 255.0] + list(140.0 + _R_3P * np.cos(_theta_m_r)) + [185.0, 185.0]
_m_r_y = [0.0, 0.0] + list(25.0 + _R_3P * np.sin(_theta_m_r)) + [85.0, 0.0]

# 4. Mid-Range Center (bounded by free throw line y=85, side verticals x=95/185, and top 3PT arc)
_theta_m_c = np.linspace(_theta_arc_r, _theta_arc_l, _N_CURVE)
_m_c_x = [95.0, 185.0] + list(140.0 + _R_3P * np.cos(_theta_m_c)) + [95.0]
_m_c_y = [85.0, 85.0] + list(25.0 + _R_3P * np.sin(_theta_m_c)) + [85.0]

# 5. Above Break 3 Left / Left Wing 3 (bounded by y=50, 3PT arc, vertical partition at x=95, half-court y=200, and sideline x=0)
_theta_ab_l = np.linspace(_theta_c_l, _theta_arc_l, _N_CURVE)
_ab_l_x = [0.0, 25.0] + list(140.0 + _R_3P * np.cos(_theta_ab_l)) + [95.0, 0.0, 0.0]
_ab_l_y = [50.0, 50.0] + list(25.0 + _R_3P * np.sin(_theta_ab_l)) + [200.0, 200.0, 50.0]

# 6. Above Break 3 Right / Right Wing 3 (bounded by y=50, sideline x=280, half-court y=200, vertical partition at x=185, and 3PT arc)
_theta_ab_r = np.linspace(_theta_arc_r, _theta_c_r, _N_CURVE)
_ab_r_x = [280.0, 185.0] + list(140.0 + _R_3P * np.cos(_theta_ab_r)) + [280.0, 280.0]
_ab_r_y = [200.0, 200.0] + list(25.0 + _R_3P * np.sin(_theta_ab_r)) + [50.0, 200.0]

# 7. Above Break 3 Center / Top Key 3 (bounded by 3PT top arc, verticals x=95/185, and half-court y=200)
_theta_ab_c = np.linspace(_theta_arc_l, _theta_arc_r, _N_CURVE)
_ab_c_x = [95.0] + list(140.0 + _R_3P * np.cos(_theta_ab_c)) + [185.0, 95.0, 95.0]
_ab_c_y = [200.0] + list(25.0 + _R_3P * np.sin(_theta_ab_c)) + [200.0, 200.0, 200.0]

ZONE_DEFINITIONS: Dict[str, Dict[str, Any]] = {
    "PAINT_NON_RA": {
        "x": [95.0, 185.0, 185.0, 95.0, 95.0],
        "y": [0.0, 0.0, 85.0, 85.0, 0.0],
        "cx": 140,
        "cy": 62,
        "name": "Paint (Non-RA)",
        "category": "PAINT",
        "canonical_zone": "PAINT_NON_RA",
        "league_fg_pct": 38.4,
    },
    "RESTRICTED_AREA": {
        "x": _ra_x,
        "y": _ra_y,
        "cx": 140,
        "cy": 22,
        "name": "Restricted Area",
        "category": "RA",
        "canonical_zone": "RESTRICTED_AREA",
        "league_fg_pct": 56.3,
    },
    "MID_RANGE_LEFT": {
        "x": _m_l_x,
        "y": _m_l_y,
        "cx": 60,
        "cy": 50,
        "name": "Mid-Range Left",
        "category": "MID",
        "canonical_zone": "MID_RANGE",
        "league_fg_pct": 33.8,
    },
    "MID_RANGE_CENTER": {
        "x": _m_c_x,
        "y": _m_c_y,
        "cx": 140,
        "cy": 108,
        "name": "Mid-Range Center",
        "category": "MID",
        "canonical_zone": "MID_RANGE",
        "league_fg_pct": 33.8,
    },
    "MID_RANGE_RIGHT": {
        "x": _m_r_x,
        "y": _m_r_y,
        "cx": 220,
        "cy": 50,
        "name": "Mid-Range Right",
        "category": "MID",
        "canonical_zone": "MID_RANGE",
        "league_fg_pct": 33.8,
    },
    "CORNER_3_LEFT": {
        "x": [0.0, 25.0, 25.0, 0.0, 0.0],
        "y": [0.0, 0.0, 50.0, 50.0, 0.0],
        "cx": 12.5,
        "cy": 25,
        "name": "Corner 3 Left",
        "category": "CORNER_3PT",
        "canonical_zone": "CORNER_3PT",
        "league_fg_pct": 24.4,
    },
    "CORNER_3_RIGHT": {
        "x": [255.0, 280.0, 280.0, 255.0, 255.0],
        "y": [0.0, 0.0, 50.0, 50.0, 0.0],
        "cx": 267.5,
        "cy": 25,
        "name": "Corner 3 Right",
        "category": "CORNER_3PT",
        "canonical_zone": "CORNER_3PT",
        "league_fg_pct": 24.4,
    },
    "ABOVE_BREAK_3_LEFT": {
        "x": _ab_l_x,
        "y": _ab_l_y,
        "cx": 50,
        "cy": 145,
        "name": "Wing 3 Left",
        "category": "ABOVE_BREAK_3PT",
        "canonical_zone": "ABOVE_THE_BREAK_3PT",
        "league_fg_pct": 25.6,
    },
    "ABOVE_BREAK_3_CENTER": {
        "x": _ab_c_x,
        "y": _ab_c_y,
        "cx": 140,
        "cy": 168,
        "name": "Above Break 3",
        "category": "ABOVE_BREAK_3PT",
        "canonical_zone": "ABOVE_THE_BREAK_3PT",
        "league_fg_pct": 25.6,
    },
    "ABOVE_BREAK_3_RIGHT": {
        "x": _ab_r_x,
        "y": _ab_r_y,
        "cx": 230,
        "cy": 145,
        "name": "Wing 3 Right",
        "category": "ABOVE_BREAK_3PT",
        "canonical_zone": "ABOVE_THE_BREAK_3PT",
        "league_fg_pct": 25.6,
    },
}


def is_inside_3pt_line(x: float, y: float) -> bool:
    """Returns True if (x, y) is inside the 2PT shooting region."""
    if y <= 50.0:
        return 25.0 <= x <= 255.0
    dx = x - 140.0
    dy = y - 25.0
    return (dx * dx + dy * dy) < (115.0**2 + 25.0**2)


def classify_granular_zone(
    x: float,
    y: float,
    shot_type: Optional[str] = None,
    status: str = "OBSERVED"
) -> str:
    """Classifies shot coordinates into one of the 10 contiguous shooting zones.
    
    Guarantees:
    1. Continuous spatial partition of [0, 280] x [0, 200] with 0 gaps and 0 overlaps.
    2. Hard shot_type constraints (3PT cannot map to 2PT, 2PT cannot map to 3PT).
    3. Seamless transition between Mid-Range and 3PT wings.
    """
    if status != "OBSERVED" or pd.isna(x) or pd.isna(y):
        return "UNKNOWN"
    if x < 0.0 or x > 280.0 or y < 0.0 or y > 200.0:
        return "UNKNOWN"

    in_2p = is_inside_3pt_line(x, y)

    # 3PT shots partition
    if shot_type == "3PT" or (shot_type != "2PT" and not in_2p):
        if y <= 50.0:
            return "CORNER_3_LEFT" if x <= 140.0 else "CORNER_3_RIGHT"
        else:
            if x < 95.0:
                return "ABOVE_BREAK_3_LEFT"
            elif x > 185.0:
                return "ABOVE_BREAK_3_RIGHT"
            else:
                return "ABOVE_BREAK_3_CENTER"
    else:  # 2PT shots partition
        dx = x - 140.0
        dy = y - 25.0
        dist = math.sqrt(dx * dx + dy * dy)
        if dist <= 35.0:
            return "RESTRICTED_AREA"
        elif dist <= 75.0 and abs(dx) <= 45.0 and y <= 85.0:
            return "PAINT_NON_RA"
        else:
            if x < 95.0:
                return "MID_RANGE_LEFT"
            elif x > 185.0:
                return "MID_RANGE_RIGHT"
            else:
                return "MID_RANGE_CENTER"


# ==============================================================================
# 2. STATISTICAL ZONE SUMMARY & BAYESIAN EFFICIENCY SHADING
# ==============================================================================

def calculate_spatial_zone_summary(
    df_shots: pd.DataFrame,
    total_volume_ref: Optional[int] = None,
    prior_weight: float = 5.0
) -> Dict[str, Dict[str, Any]]:
    """Calculates sample-size-aware efficiency, Bayesian shrinkage, and RGBA shading for each zone."""
    if df_shots.empty or "x_coord" not in df_shots.columns:
        df_valid = pd.DataFrame()
    else:
        df_valid = df_shots.dropna(subset=["x_coord", "y_coord"]).copy()
        if "gran_zone" not in df_valid.columns:
            df_valid["gran_zone"] = df_valid.apply(
                lambda r: classify_granular_zone(
                    r["x_coord"], r["y_coord"], r.get("shot_type", "2PT"), r.get("shot_location_status", "OBSERVED")
                ),
                axis=1
            )

    tot_shots = len(df_valid)
    vol_ref = total_volume_ref if (total_volume_ref is not None and total_volume_ref > 0) else max(1, tot_shots)

    summaries = {}
    for zone_id, meta in ZONE_DEFINITIONS.items():
        if df_valid.empty:
            zdf = pd.DataFrame()
        else:
            zdf = df_valid[df_valid["gran_zone"] == zone_id]

        fga = len(zdf)
        fgm = int((zdf["is_made"] == True).sum()) if fga > 0 else 0
        pts = int(zdf["points"].sum()) if (fga > 0 and "points" in zdf.columns) else (fgm * 3 if "3" in zone_id else fgm * 2)
        fg_pct = round(fgm * 100.0 / fga, 1) if fga > 0 else 0.0
        eppa = round(pts / max(1, fga), 2) if fga > 0 else 0.0
        base_fg = meta["league_fg_pct"]

        # Bayesian shrinkage toward league baseline: Delta_shrunk = (FG% - Base) * (FGA / (FGA + k))
        raw_delta = round(fg_pct - base_fg, 1) if fga > 0 else 0.0
        shrunk_delta = round(raw_delta * (fga / (fga + prior_weight)), 1) if fga > 0 else 0.0

        # Opacity scaled by attempt volume
        # Minimum opacity = 0.20, Max = 0.70
        volume_share = fga / max(5.0, vol_ref * 0.20)
        opacity = min(0.70, max(0.18, 0.20 + 0.50 * min(1.0, volume_share))) if fga > 0 else 0.05

        # Color classification based on Bayesian smoothed delta
        # Blue = Hot / Efficient | Slate = Average | Red = Cold / Depressed
        if fga == 0:
            color_hex = "#94A3B8"
            fill_rgba = "rgba(226, 232, 240, 0.15)"
            line_color = "rgba(203, 213, 225, 0.5)"
            tier_label = "No Attempts"
        elif shrunk_delta >= 6.0:
            color_hex = "#0284C7"  # Deep Royal / Sky Blue
            fill_rgba = f"rgba(2, 132, 199, {opacity:.2f})"
            line_color = "#0369A1"
            tier_label = "🔥 High Efficiency (+Hot)"
        elif shrunk_delta >= 2.0:
            color_hex = "#38BDF8"  # Light Sky Blue
            fill_rgba = f"rgba(56, 189, 248, {opacity:.2f})"
            line_color = "#0284C7"
            tier_label = "⚡ Above Baseline (+Warm)"
        elif shrunk_delta <= -6.0:
            color_hex = "#E11D48"  # Deep Rose / Crimson Red
            fill_rgba = f"rgba(225, 29, 72, {opacity:.2f})"
            line_color = "#BE123C"
            tier_label = "❄️ Depressed Efficiency (-Cold)"
        elif shrunk_delta <= -2.0:
            color_hex = "#FB7185"  # Soft Coral
            fill_rgba = f"rgba(251, 113, 133, {opacity:.2f})"
            line_color = "#E11D48"
            tier_label = "⚠️ Below Baseline (-Cool)"
        else:
            color_hex = "#94A3B8"  # Slate Gray
            fill_rgba = f"rgba(148, 163, 184, {opacity:.2f})"
            line_color = "#64748B"
            tier_label = "⚖️ League Baseline Level"

        # Annotation text
        if fga > 0:
            annot_text = f"<b>{fgm}/{fga}</b><br><span style='font-size:10px;'>{fg_pct:.1f}%</span>"
        else:
            annot_text = "<span style='color:#94A3B8; font-size:10px;'>0 att</span>"

        # Rich hover tooltip
        hover_text = (
            f"<b>{meta['name']}</b><br>"
            f"<b>Status:</b> {tier_label}<br>"
            f"<b>Attempts:</b> {fga} ({round(fga * 100.0 / max(1, tot_shots), 1)}% of diet)<br>"
            f"<b>Makes:</b> {fgm} / {fga} (<b>{fg_pct:.1f}% FG</b>)<br>"
            f"<b>Points Yield:</b> {pts} PTS (<b>{eppa:.2f} EPPA</b>)<br>"
            f"<b>League Baseline:</b> {base_fg:.1f}% (Δ: {raw_delta:+.1f} pp)<br>"
            f"<b>Bayesian Adjusted Δ:</b> {shrunk_delta:+.1f} pp (N={fga})"
        )

        summaries[zone_id] = {
            "name": meta["name"],
            "cx": meta["cx"],
            "cy": meta["cy"],
            "poly_x": meta["x"],
            "poly_y": meta["y"],
            "fga": fga,
            "fgm": fgm,
            "pts": pts,
            "fg_pct": fg_pct,
            "eppa": eppa,
            "base_fg": base_fg,
            "raw_delta": raw_delta,
            "shrunk_delta": shrunk_delta,
            "tier_label": tier_label,
            "color_hex": color_hex,
            "fill_rgba": fill_rgba,
            "line_color": line_color,
            "opacity": opacity,
            "annot_text": annot_text,
            "hover_text": hover_text,
        }

    return summaries


# ==============================================================================
# 3. COURT SHAPES GENERATOR (FIBA Half-Court)
# ==============================================================================

def create_court_shapes(x_offset: float = 0.0) -> List[dict]:
    """Draws standard 280x200 half-court markings with optional horizontal offset for subplots."""
    shapes = []

    # 1. Outer Boundary (Baseline y=0, Sidelines x=0/280, Half-court y=200)
    shapes.append(dict(
        type="rect",
        x0=x_offset + 0, y0=0, x1=x_offset + 280, y1=200,
        line=dict(color="#CBD5E1", width=2),
        fillcolor="rgba(248, 250, 252, 0.2)"
    ))

    # 2. Paint / Key (95 to 185, 0 to 85)
    shapes.append(dict(
        type="rect",
        x0=x_offset + 95, y0=0, x1=x_offset + 185, y1=85,
        line=dict(color="#94A3B8", width=1.75),
        fillcolor="rgba(0,0,0,0)"
    ))

    # 3. Free Throw Circle (Center 140, 85, Radius 30)
    shapes.append(dict(
        type="circle",
        x0=x_offset + 110, y0=55, x1=x_offset + 170, y1=115,
        line=dict(color="#94A3B8", width=1.5, dash="dash"),
        fillcolor="rgba(0,0,0,0)"
    ))

    # 4. Backboard (125 to 155 at y=18) & Basket (Center 140, 25)
    shapes.append(dict(
        type="line",
        x0=x_offset + 125, y0=18, x1=x_offset + 155, y1=18,
        line=dict(color="#334155", width=3)
    ))
    shapes.append(dict(
        type="circle",
        x0=x_offset + 135, y0=20, x1=x_offset + 145, y1=30,
        line=dict(color="#EF4444", width=2),
        fillcolor="rgba(239, 68, 68, 0.4)"
    ))

    # 5. Restricted Area Arc (Radius 22 around 140, 25)
    theta = np.linspace(0, np.pi, 50)
    r_ra = 22
    x_ra = x_offset + 140 + r_ra * np.cos(theta)
    y_ra = 25 + r_ra * np.sin(theta)
    path_ra = f"M {x_ra[0]},{y_ra[0]} " + " ".join([f"L {x},{y}" for x, y in zip(x_ra[1:], y_ra[1:])])
    shapes.append(dict(
        type="path", path=path_ra,
        line=dict(color="#0284C7", width=1.5, dash="dot")
    ))

    # 6. 3-Point Line (Corners: x=25, x=255 up to y=50, Arc radius ~117 around 140, 25)
    shapes.append(dict(
        type="line",
        x0=x_offset + 25, y0=0, x1=x_offset + 25, y1=50,
        line=dict(color="#64748B", width=2)
    ))
    shapes.append(dict(
        type="line",
        x0=x_offset + 255, y0=0, x1=x_offset + 255, y1=50,
        line=dict(color="#64748B", width=2)
    ))
    theta_3p = np.linspace(0.22, np.pi - 0.22, 60)
    r_3p = 117
    x_3p = x_offset + 140 + r_3p * np.cos(theta_3p)
    y_3p = 25 + r_3p * np.sin(theta_3p)
    path_3p = f"M {x_offset + 255},50 L {x_3p[0]},{y_3p[0]} " + " ".join([f"L {x},{y}" for x, y in zip(x_3p[1:], y_3p[1:])]) + f" L {x_offset + 25},50"
    shapes.append(dict(
        type="path", path=path_3p,
        line=dict(color="#64748B", width=2)
    ))

    return shapes


# ==============================================================================
# 4. PRIMARY COURT CHART RENDERER (Team & Player Shot Map)
# ==============================================================================

def render_shot_chart(
    df_shots: pd.DataFrame,
    title: str = "Tactical Court Shot Map",
    height: int = 460,
    show_hot_zones: bool = True,
    show_shots: bool = True,
    show_labels: bool = True,
    show_zones: Optional[bool] = None,
    total_volume_ref: Optional[int] = None,
    **kwargs: Any
) -> go.Figure:
    """Creates Plotly interactive court chart with optional Hot Zones and Made/Missed shot markers."""
    if show_zones is not None:
        show_hot_zones = show_zones

    fig = go.Figure()

    # 1. Hot Zones Layer (Rendered as closed polygon traces with hover tooltips)
    if show_hot_zones:
        zone_sums = calculate_spatial_zone_summary(df_shots, total_volume_ref=total_volume_ref)
        for zid, zinfo in zone_sums.items():
            fig.add_trace(go.Scatter(
                x=zinfo["poly_x"],
                y=zinfo["poly_y"],
                fill="toself",
                fillcolor=zinfo["fill_rgba"],
                line=dict(color=zinfo["line_color"], width=1.2),
                mode="lines",
                name=zinfo["name"],
                text=zinfo["hover_text"],
                hoverinfo="text",
                showlegend=False
            ))

            # Centered metric label
            if show_labels:
                fig.add_annotation(
                    x=zinfo["cx"],
                    y=zinfo["cy"],
                    text=zinfo["annot_text"],
                    showarrow=False,
                    font=dict(size=11, color="#0F172A", family="Inter, sans-serif"),
                    align="center",
                    bgcolor="rgba(255, 255, 255, 0.65)",
                    bordercolor="rgba(226, 232, 240, 0.8)",
                    borderwidth=1,
                    borderpad=2
                )

    # 2. Add court boundary markings on top
    shapes = create_court_shapes()
    for s in shapes:
        fig.add_shape(s)

    # 3. Individual Shot Markers (Makes & Misses)
    if show_shots and not df_shots.empty and "x_coord" in df_shots.columns:
        df_valid = df_shots.dropna(subset=["x_coord", "y_coord"]).copy()

        # Misses (Red X)
        misses = df_valid[df_valid["is_made"] == False]
        if not misses.empty:
            hover_text_miss = misses.apply(
                lambda r: (
                    f"<b>❌ MISSED {r.get('shot_type', '2PT')}</b><br>"
                    f"<b>Shooter:</b> {r.get('player_name', 'Unknown')}<br>"
                    f"<b>Zone:</b> {str(r.get('shot_zone', '')).replace('_', ' ').title()}<br>"
                    f"<b>Match:</b> {r.get('game_date', '')} vs {r.get('opponent_name', '')}<br>"
                    f"<b>Period:</b> Q{r.get('period', 1)} · {int(r.get('game_seconds_remaining', 0))//60:02d}:{int(r.get('game_seconds_remaining', 0))%60:02d} rem"
                ),
                axis=1
            )
            fig.add_trace(go.Scatter(
                x=misses["x_coord"], y=misses["y_coord"],
                mode="markers",
                name="Missed Shot",
                marker=dict(symbol="x", size=7.5, color="#EF4444", line=dict(width=1.5)),
                text=hover_text_miss,
                hoverinfo="text"
            ))

        # Makes (Green Circle)
        makes = df_valid[df_valid["is_made"] == True]
        if not makes.empty:
            hover_text_make = makes.apply(
                lambda r: (
                    f"<b>✅ MADE {r.get('shot_type', '2PT')}</b><br>"
                    f"<b>Shooter:</b> {r.get('player_name', 'Unknown')}<br>"
                    f"<b>Zone:</b> {str(r.get('shot_zone', '')).replace('_', ' ').title()}<br>"
                    f"<b>Match:</b> {r.get('game_date', '')} vs {r.get('opponent_name', '')}<br>"
                    f"<b>Period:</b> Q{r.get('period', 1)} · {int(r.get('game_seconds_remaining', 0))//60:02d}:{int(r.get('game_seconds_remaining', 0))%60:02d} rem<br>"
                    f"<b>Assist:</b> {r.get('assisted_by_name', 'Unassisted')}"
                ),
                axis=1
            )
            fig.add_trace(go.Scatter(
                x=makes["x_coord"], y=makes["y_coord"],
                mode="markers",
                name="Made Shot",
                marker=dict(symbol="circle", size=8.5, color="#10B981", line=dict(color="#047857", width=1.5)),
                text=hover_text_make,
                hoverinfo="text"
            ))

    if df_shots.empty or "x_coord" not in df_shots.columns:
        fig.add_annotation(
            text="No shot coordinates available for this selection.",
            xref="paper", yref="paper", x=0.5, y=0.5,
            showarrow=False, font=dict(size=14, color="#64748B")
        )

    fig.update_layout(
        title=dict(text=title, font=dict(size=15, color="#0F172A", family="Inter, sans-serif")),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-10, 290], constrain="domain"),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-10, 210], scaleanchor="x", scaleratio=1, constrain="domain"),
        plot_bgcolor="#F8FAFC",
        paper_bgcolor="#FFFFFF",
        autosize=True,
        height=height,
        margin=dict(l=10, r=10, t=40, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    return fig


# ==============================================================================
# 5. HEAD-TO-HEAD COMPARISON RENDERER (Player A vs Player B)
# ==============================================================================

def render_shot_comparison_chart(
    df_a: pd.DataFrame,
    df_b: pd.DataFrame,
    name_a: str = "Player A",
    name_b: str = "Player B",
    height: int = 440,
    show_hot_zones: bool = True,
    show_shots: bool = True,
    show_zones: Optional[bool] = None,
    scale_mode: str = "shared",
    **kwargs: Any
) -> go.Figure:
    """Creates side-by-side 2D court comparison subplots with strictly identical FIBA geometry and scaling."""
    if show_zones is not None:
        show_hot_zones = show_zones
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=(
            f"<b>{name_a}</b> ({len(df_a)} shots)",
            f"<b>{name_b}</b> ({len(df_b)} shots)"
        ),
        horizontal_spacing=0.06
    )

    # Reference volume for shared vs relative scale
    vol_ref_a = max(len(df_a), len(df_b)) if scale_mode == "shared" else len(df_a)
    vol_ref_b = max(len(df_a), len(df_b)) if scale_mode == "shared" else len(df_b)

    # 1. Hot Zones for Player A (col=1)
    if show_hot_zones:
        zone_sums_a = calculate_spatial_zone_summary(df_a, total_volume_ref=vol_ref_a)
        for zid, zinfo in zone_sums_a.items():
            fig.add_trace(go.Scatter(
                x=zinfo["poly_x"], y=zinfo["poly_y"],
                fill="toself", fillcolor=zinfo["fill_rgba"],
                line=dict(color=zinfo["line_color"], width=1.0),
                mode="lines", showlegend=False,
                text=f"<b>{name_a}</b><br>" + zinfo["hover_text"],
                hoverinfo="text"
            ), row=1, col=1)

            fig.add_annotation(
                x=zinfo["cx"], y=zinfo["cy"],
                text=zinfo["annot_text"],
                showarrow=False,
                font=dict(size=10, color="#0F172A", family="Inter, sans-serif"),
                align="center",
                bgcolor="rgba(255, 255, 255, 0.6)",
                bordercolor="rgba(226, 232, 240, 0.7)",
                borderwidth=1,
                borderpad=1,
                row=1, col=1
            )

        # Hot Zones for Player B (col=2)
        zone_sums_b = calculate_spatial_zone_summary(df_b, total_volume_ref=vol_ref_b)
        for zid, zinfo in zone_sums_b.items():
            fig.add_trace(go.Scatter(
                x=zinfo["poly_x"], y=zinfo["poly_y"],
                fill="toself", fillcolor=zinfo["fill_rgba"],
                line=dict(color=zinfo["line_color"], width=1.0),
                mode="lines", showlegend=False,
                text=f"<b>{name_b}</b><br>" + zinfo["hover_text"],
                hoverinfo="text"
            ), row=1, col=2)

            fig.add_annotation(
                x=zinfo["cx"], y=zinfo["cy"],
                text=zinfo["annot_text"],
                showarrow=False,
                font=dict(size=10, color="#0F172A", family="Inter, sans-serif"),
                align="center",
                bgcolor="rgba(255, 255, 255, 0.6)",
                bordercolor="rgba(226, 232, 240, 0.7)",
                borderwidth=1,
                borderpad=1,
                row=1, col=2
            )

    # 2. Add court boundary markings to both subplots
    shapes_a = create_court_shapes(x_offset=0)
    for s in shapes_a:
        fig.add_shape(s, row=1, col=1)

    shapes_b = create_court_shapes(x_offset=0)
    for s in shapes_b:
        fig.add_shape(s, row=1, col=2)

    # 3. Plot Player A Shots (col=1)
    if show_shots and not df_a.empty:
        df_a_valid = df_a.dropna(subset=["x_coord", "y_coord"])
        misses_a = df_a_valid[df_a_valid["is_made"] == False]
        makes_a = df_a_valid[df_a_valid["is_made"] == True]

        if not misses_a.empty:
            fig.add_trace(go.Scatter(
                x=misses_a["x_coord"], y=misses_a["y_coord"],
                mode="markers", name=f"{name_a} Miss",
                marker=dict(symbol="x", size=6.5, color="#EF4444", line=dict(width=1.2)),
                showlegend=False,
                hovertext=misses_a.apply(lambda r: f"{name_a}: MISSED {r.get('shot_type', '')} ({r.get('shot_zone', '')})", axis=1),
                hoverinfo="text"
            ), row=1, col=1)

        if not makes_a.empty:
            fig.add_trace(go.Scatter(
                x=makes_a["x_coord"], y=makes_a["y_coord"],
                mode="markers", name=f"{name_a} Make",
                marker=dict(symbol="circle", size=7.5, color="#10B981", line=dict(color="#047857", width=1.2)),
                showlegend=False,
                hovertext=makes_a.apply(lambda r: f"{name_a}: MADE {r.get('shot_type', '')} ({r.get('shot_zone', '')})", axis=1),
                hoverinfo="text"
            ), row=1, col=1)

    # 4. Plot Player B Shots (col=2)
    if show_shots and not df_b.empty:
        df_b_valid = df_b.dropna(subset=["x_coord", "y_coord"])
        misses_b = df_b_valid[df_b_valid["is_made"] == False]
        makes_b = df_b_valid[df_b_valid["is_made"] == True]

        if not misses_b.empty:
            fig.add_trace(go.Scatter(
                x=misses_b["x_coord"], y=misses_b["y_coord"],
                mode="markers", name=f"{name_b} Miss",
                marker=dict(symbol="x", size=6.5, color="#EF4444", line=dict(width=1.2)),
                showlegend=False,
                hovertext=misses_b.apply(lambda r: f"{name_b}: MISSED {r.get('shot_type', '')} ({r.get('shot_zone', '')})", axis=1),
                hoverinfo="text"
            ), row=1, col=2)

        if not makes_b.empty:
            fig.add_trace(go.Scatter(
                x=makes_b["x_coord"], y=makes_b["y_coord"],
                mode="markers", name=f"{name_b} Make",
                marker=dict(symbol="circle", size=7.5, color="#10B981", line=dict(color="#047857", width=1.2)),
                showlegend=False,
                hovertext=makes_b.apply(lambda r: f"{name_b}: MADE {r.get('shot_type', '')} ({r.get('shot_zone', '')})", axis=1),
                hoverinfo="text"
            ), row=1, col=2)

    # 5. STRICT GEOMETRY LOCK (Identical axes, identical aspect ratios, identical bounds)
    fig.update_layout(
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-10, 290], constrain="domain"),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-10, 210], scaleanchor="x", scaleratio=1, constrain="domain"),
        xaxis2=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-10, 290], constrain="domain"),
        yaxis2=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-10, 210], scaleanchor="x2", scaleratio=1, constrain="domain"),
        plot_bgcolor="#F8FAFC",
        paper_bgcolor="#FFFFFF",
        height=height,
        margin=dict(l=10, r=10, t=40, b=10)
    )
    return fig

