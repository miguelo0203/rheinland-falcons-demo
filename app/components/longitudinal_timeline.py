"""Longitudinal Career Timeline & Multi-Metric Trajectory Component.

Rheinland Falcons Basketball — JBBL / NBBL Player Development Platform.
Visualizes career longitudinal trends across 14 selectable rate, boxscore, and on-court metrics.
Strictly isolates U16 vs U19 with distinct color palettes, marks category transitions,
and preserves visual honesty (missing values rendered as gaps, never false zeros).
"""

from typing import Dict, Optional
import numpy as np
import pandas as pd
import plotly.graph_objects as go

METRIC_CONFIG: Dict[str, Dict[str, str]] = {
    "net_rtg": {
        "label": "Net Rating (PBP On-Court)",
        "unit": "per 100 poss",
        "format": "+0.1f",
        "category": "Efficiency & On-Court Impact"
    },
    "ortg": {
        "label": "Offensive Rating (PBP)",
        "unit": "per 100 poss",
        "format": "0.1f",
        "category": "Efficiency & On-Court Impact"
    },
    "drtg": {
        "label": "Defensive Rating (PBP)",
        "unit": "per 100 poss",
        "format": "0.1f",
        "category": "Efficiency & On-Court Impact"
    },
    "ts_pct": {
        "label": "True Shooting Percentage (TS%)",
        "unit": "%",
        "format": "0.1f",
        "category": "Efficiency & On-Court Impact"
    },
    "efg_pct": {
        "label": "Effective Field Goal % (eFG%)",
        "unit": "%",
        "format": "0.1f",
        "category": "Efficiency & On-Court Impact"
    },
    "usage_pct": {
        "label": "Usage Percentage (USG%)",
        "unit": "%",
        "format": "0.1f",
        "category": "Volume & Role"
    },
    "points": {
        "label": "Points Scored (PTS)",
        "unit": "pts",
        "format": "d",
        "category": "Traditional Boxscore"
    },
    "trb": {
        "label": "Total Rebounds (REB)",
        "unit": "reb",
        "format": "d",
        "category": "Traditional Boxscore"
    },
    "ast": {
        "label": "Assists (AST)",
        "unit": "ast",
        "format": "d",
        "category": "Traditional Boxscore"
    },
    "ast_to_tov": {
        "label": "Assist-to-Turnover Ratio (AST/TOV)",
        "unit": "ratio",
        "format": "0.2f",
        "category": "Efficiency & On-Court Impact"
    },
    "stl": {
        "label": "Steals (STL)",
        "unit": "stl",
        "format": "d",
        "category": "Traditional Boxscore"
    },
    "blk": {
        "label": "Blocks (BLK)",
        "unit": "blk",
        "format": "d",
        "category": "Traditional Boxscore"
    },
    "tov": {
        "label": "Turnovers (TOV)",
        "unit": "tov",
        "format": "d",
        "category": "Traditional Boxscore"
    },
    "minutes": {
        "label": "Minutes Played (MIN)",
        "unit": "min",
        "format": "0.1f",
        "category": "Volume & Role"
    }
}

def render_longitudinal_timeline(
    df_career_log: pd.DataFrame,
    player_name: str,
    metric_key: str = "net_rtg"
) -> go.Figure:
    """Generates a comprehensive longitudinal timeline for any of 14 metrics.
    
    Features:
    - Discrete game markers colored by category (U16: #0284C7, U19: #7C3AED)
    - Dashed baseline career average line
    - Rolling 4-game smoothed trend line
    - Visual category transition marker when multi-category history exists
    - Missing metrics handled cleanly with gap breaks (no false drops to 0)
    """
    fig = go.Figure()

    cfg = METRIC_CONFIG.get(metric_key, {
        "label": metric_key.replace("_", " ").title(),
        "unit": "",
        "format": "0.1f"
    })
    metric_label = cfg["label"]
    metric_unit = cfg["unit"]

    if df_career_log.empty or metric_key not in df_career_log.columns:
        fig.add_annotation(
            text=f"No career data available for {player_name}.",
            xref="paper", yref="paper", x=0.5, y=0.5,
            showarrow=False, font=dict(size=14, color="#64748B")
        )
        fig.update_layout(height=420, plot_bgcolor="#FFFFFF", paper_bgcolor="#FFFFFF")
        return fig

    # Ensure chronological sort
    df_sorted = df_career_log.sort_values(["game_date", "game_id"]).reset_index(drop=True).copy()
    df_sorted["game_idx"] = range(1, len(df_sorted) + 1)

    # Convert metric series to numeric, preserving NaNs
    series = pd.to_numeric(df_sorted[metric_key], errors="coerce")
    df_sorted["_metric_val"] = series

    # Format x-axis tick labels
    x_indices = list(range(len(df_sorted)))
    x_labels = [
        f"G{r['game_idx']}: {str(r.get('game_date', ''))[:10]}<br>vs {str(r.get('opponent_name', ''))[:14]}"
        for _, r in df_sorted.iterrows()
    ]

    # X-axis tick decimation for long careers (> 30 appearances)
    # Reduces visual crowding while preserving all underlying data points and traces
    if len(df_sorted) > 30:
        step = 5
        tick_indices = list(range(0, len(df_sorted), step))
        if (len(df_sorted) - 1) not in tick_indices:
            tick_indices.append(len(df_sorted) - 1)
        display_tickvals = tick_indices
        display_ticktext = [x_labels[i] for i in tick_indices]
    else:
        display_tickvals = x_indices
        display_ticktext = x_labels

    # Calculate rolling 4-game average over valid values
    rolling_series = series.rolling(window=4, min_periods=1).mean()
    valid_vals = series.dropna()

    # If all values are NaN for this metric
    if valid_vals.empty:
        fig.add_annotation(
            text=f"No recorded {metric_label} data available across these appearances.<br><span style='font-size:11px; color:#94A3B8;'>PBP stint or possession data may not be logged for this selection.</span>",
            xref="paper", yref="paper", x=0.5, y=0.5,
            showarrow=False, font=dict(size=13, color="#64748B"), align="center"
        )
        fig.update_layout(
            title=dict(
                text=f"<b>Longitudinal Development: {player_name} — {metric_label}</b>",
                font=dict(size=15, color="#1E293B")
            ),
            height=420,
            plot_bgcolor="#FFFFFF",
            paper_bgcolor="#FFFFFF"
        )
        return fig

    # Career baseline average
    baseline_avg = float(valid_vals.mean())

    # Split into U16 and U19 subsets for discrete markers
    u16_mask = (df_sorted["squad"] == "U16") & series.notna()
    u19_mask = (df_sorted["squad"] == "U19") & series.notna()
    other_mask = (~df_sorted["squad"].isin(["U16", "U19"])) & series.notna()

    # 1. Career Baseline (Horizontal Dashed Line)
    fig.add_trace(go.Scatter(
        x=x_indices,
        y=[baseline_avg] * len(df_sorted),
        mode="lines",
        name=f"Career Baseline ({baseline_avg:.1f} {metric_unit})",
        line=dict(color="#94A3B8", width=1.5, dash="dash"),
        hoverinfo="skip"
    ))

    # 2. Rolling 4-Game Trend Line
    fig.add_trace(go.Scatter(
        x=x_indices,
        y=rolling_series,
        mode="lines",
        name="4-Game Rolling Trend",
        line=dict(color="#D97706", width=2.8),
        connectgaps=True,
        hovertemplate="<b>4-Game Trend</b>: %{y:.1f} " + metric_unit + "<extra></extra>"
    ))

    # Helper for tooltips with contextual possession sample volume for on-court ratings
    def _make_hover(subset: pd.DataFrame) -> list:
        hovers = []
        for _, r in subset.iterrows():
            val = r["_metric_val"]
            if pd.notna(val):
                if metric_key == "net_rtg" or cfg.get("format") == "+0.1f":
                    val_str = f"{val:+.1f}"
                elif cfg.get("format") == "d":
                    val_str = f"{int(round(val))}"
                elif cfg.get("format") == "0.2f":
                    val_str = f"{val:.2f}"
                else:
                    val_str = f"{val:.1f}"
            else:
                val_str = "N/A"

            # Possession sample volume context for on-court ratings (Net Rtg, ORtg, DRtg)
            poss_info = ""
            if metric_key in ["net_rtg", "ortg", "drtg"]:
                poss = r.get("stint_poss")
                if pd.notna(poss):
                    poss_val = float(poss)
                    if poss_val < 10.0:
                        poss_info = f"<br>Possessions: {poss_val:.1f} (Low Volume)"
                    else:
                        poss_info = f"<br>Possessions: {poss_val:.1f}"
                else:
                    poss_info = "<br>Possessions: Unavailable"

            h = (
                f"<b>Game {r['game_idx']}: {r.get('squad', 'Academy')}</b><br>"
                f"Date: {str(r.get('game_date', ''))[:10]}<br>"
                f"Opponent: {r.get('opponent_name', '')} ({r.get('result', '')} {r.get('final_score', '')})<br>"
                f"MIN: {r.get('minutes', 0.0):.1f}<br>"
                f"<b>{metric_label}: {val_str} {metric_unit}</b>"
                f"{poss_info}"
            )
            hovers.append(h)
        return hovers

    # 3. U16 Game Markers (Sky Blue)
    if u16_mask.any():
        df_u16 = df_sorted[u16_mask]
        fig.add_trace(go.Scatter(
            x=df_u16.index.tolist(),
            y=df_u16["_metric_val"],
            mode="markers",
            name="U16 (JBBL) Matches",
            marker=dict(size=9, color="#0284C7", symbol="circle", line=dict(color="#0369A1", width=1.5)),
            hovertext=_make_hover(df_u16),
            hoverinfo="text"
        ))

    # 4. U19 Game Markers (Violet / Purple)
    if u19_mask.any():
        df_u19 = df_sorted[u19_mask]
        fig.add_trace(go.Scatter(
            x=df_u19.index.tolist(),
            y=df_u19["_metric_val"],
            mode="markers",
            name="U19 (NBBL) Matches",
            marker=dict(size=10, color="#7C3AED", symbol="diamond", line=dict(color="#5B21B6", width=1.5)),
            hovertext=_make_hover(df_u19),
            hoverinfo="text"
        ))

    # 5. Other/Unspecified Squad Markers
    if other_mask.any():
        df_other = df_sorted[other_mask]
        fig.add_trace(go.Scatter(
            x=df_other.index.tolist(),
            y=df_other["_metric_val"],
            mode="markers",
            name="Academy Matches",
            marker=dict(size=8, color="#64748B", symbol="circle"),
            hovertext=_make_hover(df_other),
            hoverinfo="text"
        ))

    # 6. Category Transition Marker (when both U16 and U19 exist)
    has_u16 = (df_sorted["squad"] == "U16").any()
    has_u19 = (df_sorted["squad"] == "U19").any()

    if has_u16 and has_u19:
        first_u19_idx = df_sorted[df_sorted["squad"] == "U19"].index.min()
        if pd.notna(first_u19_idx) and first_u19_idx > 0:
            divider_x = first_u19_idx - 0.5
            fig.add_vline(
                x=divider_x,
                line_width=2,
                line_dash="dashdot",
                line_color="#7C3AED",
                annotation_text="<b>U16 ➔ U19 Transition</b>",
                annotation_position="top right",
                annotation_font=dict(size=11, color="#7C3AED")
            )
            fig.add_vrect(
                x0=divider_x,
                x1=len(df_sorted) - 0.5,
                fillcolor="rgba(124, 58, 237, 0.05)",
                layer="below",
                line_width=0
            )

    fig.update_layout(
        title=dict(
            text=f"<b>Longitudinal Development Timeline: {player_name}</b><br><span style='font-size:12px; color:#64748B;'>Tracking {metric_label} across {len(df_sorted)} career appearances · Amber: 4-Game Trend · Dashed: Career Baseline</span>",
            font=dict(size=15, color="#1E293B")
        ),
        xaxis=dict(
            title="Chronological Matches (Career Order)",
            tickmode="array",
            tickvals=display_tickvals,
            ticktext=display_ticktext,
            tickfont=dict(size=8.5, color="#64748B"),
            showgrid=False,
            range=[-0.5, len(df_sorted) - 0.5]
        ),
        yaxis=dict(
            title=f"{metric_label} ({metric_unit})",
            tickfont=dict(size=10, color="#64748B"),
            gridcolor="#F1F5F9",
            zeroline=True,
            zerolinecolor="#CBD5E1",
            zerolinewidth=1
        ),
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF",
        autosize=True,
        height=430,
        margin=dict(l=45, r=25, t=65, b=65),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=10)
        )
    )

    return fig
