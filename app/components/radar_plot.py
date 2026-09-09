"""6-Axis JBBL Percentile Spider/Radar Chart using Plotly."""

import plotly.graph_objects as go
from typing import Dict, Any

def render_percentile_radar(percentiles: Dict[str, float], player_name: str) -> go.Figure:
    """Creates closed polygon radar chart comparing player to JBBL qualified benchmark."""
    
    categories = [
        'Scoring<br>(PTS/40)',
        'Efficiency<br>(TS%)',
        'Rebounding<br>(REB/40)',
        'Playmaking<br>(AST/40)',
        'Ball Security<br>(AST/TOV)',
        'Disruption<br>(STL+BLK/40)'
    ]
    
    # Order values matching categories
    values = [
        percentiles.get('pts_per_40', 50.0) or 50.0,
        percentiles.get('ts_pct', 50.0) or 50.0,
        percentiles.get('reb_per_40', 50.0) or 50.0,
        percentiles.get('ast_per_40', 50.0) or 50.0,
        percentiles.get('ast_to_tov', 50.0) or 50.0,
        percentiles.get('def_disruption', 50.0) or 50.0
    ]
    
    # Close polygon
    categories_closed = categories + [categories[0]]
    values_closed = values + [values[0]]
    median_benchmark = [50.0] * len(categories_closed)
    
    fig = go.Figure()
    
    # 50th Percentile Reference Circle (JBBL League Median)
    fig.add_trace(go.Scatterpolar(
        r=median_benchmark,
        theta=categories_closed,
        mode='lines',
        name='JBBL Median (50th %ile)',
        line=dict(color='#94A3B8', width=1.5, dash='dash'),
        hoverinfo='skip'
    ))
    
    # Player Percentile Shape
    fig.add_trace(go.Scatterpolar(
        r=values_closed,
        theta=categories_closed,
        fill='toself',
        fillcolor='rgba(217, 119, 6, 0.25)', # FALCONS gold accent
        name=player_name,
        line=dict(color='#D97706', width=2.5),
        marker=dict(size=6, color='#B45309'),
        hoverinfo='text',
        text=[f"{cat.replace('<br>', ' ')}: {val:.1f}th %ile" for cat, val in zip(categories_closed, values_closed)]
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                tickvals=[25, 50, 75, 100],
                ticktext=['25%', '50%', '75%', '100%'],
                tickfont=dict(size=9, color='#64748B'),
                linecolor='#CBD5E1',
                gridcolor='#E2E8F0'
            ),
            angularaxis=dict(
                tickfont=dict(size=11, color='#1E293B', family='Arial Black, sans-serif'),
                linecolor='#CBD5E1',
                gridcolor='#E2E8F0'
            )
        ),
        title=dict(
            text=f"<b>{player_name}</b> vs Qualified JBBL Population",
            font=dict(size=15, color='#1E293B')
        ),
        paper_bgcolor='#FFFFFF',
        plot_bgcolor='#FFFFFF',
        autosize=True,
        height=390,
        margin=dict(l=35, r=35, t=45, b=25),
        showlegend=True,
        legend=dict(orientation='h', yanchor='top', y=-0.08, xanchor='center', x=0.5)
    )
    return fig
