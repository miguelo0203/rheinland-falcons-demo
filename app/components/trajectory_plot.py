"""Longitudinal Performance Trajectory & Baseline Comparison using Plotly."""

import pandas as pd
import plotly.graph_objects as go
from typing import Optional

def render_trajectory_chart(df_game_log: pd.DataFrame, player_name: str, baseline_ppg: float, baseline_ts: float) -> go.Figure:
    """Plots chronological points and True Shooting with 4-game rolling series vs baseline."""
    fig = go.Figure()
    
    if df_game_log.empty:
        fig.add_annotation(
            text="No game log data available.",
            xref="paper", yref="paper", x=0.5, y=0.5,
            showarrow=False, font=dict(size=14, color="#64748B")
        )
        return fig
        
    df_sorted = df_game_log.sort_values("game_date").reset_index(drop=True)
    df_sorted["game_idx"] = range(1, len(df_sorted) + 1)
    
    # Calculate rolling 4-game average if >= 4
    df_sorted["rolling_4_ppg"] = df_sorted["points"].rolling(window=4, min_periods=1).mean()
    df_sorted["rolling_4_ts"] = df_sorted["ts_pct"].rolling(window=4, min_periods=1).mean()
    
    x_labels = df_sorted.apply(lambda r: f"G{r['game_idx']}: {str(r.get('game_date', ''))[:10]}<br>vs {r.get('opponent_name', '')}", axis=1)
    
    # 1. Single Game Points (Bar / Scatter)
    fig.add_trace(go.Bar(
        x=x_labels,
        y=df_sorted["points"],
        name="Single Game Points",
        marker_color="rgba(148, 163, 184, 0.45)",
        hovertemplate="<b>%{x}</b><br>Points: %{y}<extra></extra>"
    ))
    
    # 2. Season Average Baseline PPG (Horizontal Line)
    fig.add_trace(go.Scatter(
        x=x_labels,
        y=[baseline_ppg] * len(df_sorted),
        mode="lines",
        name=f"Season Baseline ({baseline_ppg:.1f} PPG)",
        line=dict(color="#64748B", width=1.5, dash="dash"),
        hovertemplate=f"Season Baseline: {baseline_ppg:.1f} PPG<extra></extra>"
    ))
    
    # 3. Rolling 4-Game Trajectory (Gold Line)
    fig.add_trace(go.Scatter(
        x=x_labels,
        y=df_sorted["rolling_4_ppg"],
        mode="lines+markers",
        name="4-Game Rolling PPG",
        line=dict(color="#D97706", width=3),
        marker=dict(size=7, color="#B45309"),
        hovertemplate="4-Game Rolling PPG: %{y:.1f}<extra></extra>"
    ))
    
    fig.update_layout(
        title=dict(
            text=f"<b>Scoring Trajectory & Rolling Dynamics: {player_name}</b>",
            font=dict(size=15, color="#1E293B")
        ),
        xaxis=dict(
            title="Chronological Matches",
            tickfont=dict(size=9, color="#64748B"),
            showgrid=False
        ),
        yaxis=dict(
            title="Points Scored",
            tickfont=dict(size=10, color="#64748B"),
            gridcolor="#F1F5F9"
        ),
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF",
        autosize=True,
        height=380,
        margin=dict(l=40, r=20, t=50, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    return fig
