"""Professional UI and Evidence Presentation Components for Rheinland Falcons Analytics.

Implements clean, dense, evidence-first visual hierarchy:
    DATA -> CONTEXT -> INTERPRETATION -> ACTION
Provides both HTML-string renderers and native Streamlit container display methods.
"""

from typing import Any, Dict, List, Optional, Union
import streamlit as st
import pandas as pd
import numpy as np

def clean_html(raw_html: str) -> str:
    """Removes leading indentation and blank lines to prevent Streamlit markdown code-block parsing."""
    lines = [line.strip() for line in raw_html.strip().splitlines() if line.strip()]
    return "".join(lines)

def get_custom_css() -> str:
    """Returns custom CSS for the clean professional Rheinland Falcons theme."""
    return """
<style>
/* Base typography and layout reset */
.main .block-container {
    padding-top: 1.25rem;
    padding-bottom: 2.5rem;
    padding-left: 2rem;
    padding-right: 2rem;
    max-width: 1400px;
}

/* App Header */
.hm-header-container {
    border-bottom: 2px solid #e2e8f0;
    padding-bottom: 0.75rem;
    margin-bottom: 1.25rem;
}
.hm-club-title {
    font-size: 0.85rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #0284c7;
    margin-bottom: 0.1rem;
}
.hm-main-title {
    font-size: 1.85rem;
    font-weight: 800;
    color: #0f172a;
    letter-spacing: -0.02em;
    margin: 0;
    line-height: 1.2;
}
.hm-subtitle {
    font-size: 0.9rem;
    color: #64748b;
    margin-top: 0.25rem;
}

/* Player Scouting Identity Card */
.hm-player-card {
    background-color: #f8fafc;
    border: 1px solid #e2e8f0;
    border-left: 4px solid #0284c7;
    border-radius: 6px;
    padding: 0.85rem 1.15rem;
    margin-bottom: 1.25rem;
}
.hm-player-name {
    font-size: 1.35rem;
    font-weight: 700;
    color: #0f172a;
    margin-bottom: 0.15rem;
}
.hm-player-meta {
    font-size: 0.85rem;
    color: #475569;
    font-weight: 500;
}
.hm-player-stats-row {
    margin-top: 0.45rem;
    font-size: 0.85rem;
    color: #334155;
    display: flex;
    gap: 1rem;
    flex-wrap: wrap;
}
.hm-stat-chip {
    background: #ffffff;
    border: 1px solid #cbd5e1;
    padding: 0.2rem 0.5rem;
    border-radius: 4px;
    font-weight: 600;
}

/* KPI Cards */
.hm-kpi-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 6px;
    padding: 0.85rem 1rem;
    height: 100%;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.03);
}
.hm-kpi-label {
    font-size: 0.75rem;
    font-weight: 700;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    color: #64748b;
    margin-bottom: 0.25rem;
}
.hm-kpi-value {
    font-size: 1.45rem;
    font-weight: 800;
    color: #0f172a;
    line-height: 1.1;
    margin-bottom: 0.35rem;
}
.hm-kpi-percentile {
    font-size: 0.8rem;
    font-weight: 700;
    color: #0369a1;
    margin-bottom: 0.35rem;
}
.hm-kpi-volume {
    font-size: 0.75rem;
    color: #64748b;
    line-height: 1.25;
    border-top: 1px dashed #e2e8f0;
    padding-top: 0.35rem;
    margin-top: 0.35rem;
}

/* Badges */
.hm-badge {
    display: inline-block;
    font-size: 0.68rem;
    font-weight: 700;
    padding: 0.15rem 0.45rem;
    border-radius: 3px;
    letter-spacing: 0.03em;
    text-transform: uppercase;
}
.hm-badge-established {
    background-color: #dcfce7;
    color: #166534;
    border: 1px solid #bbf7d0;
}
.hm-badge-usable {
    background-color: #e0f2fe;
    color: #0369a1;
    border: 1px solid #bae6fd;
}
.hm-badge-emerging {
    background-color: #fef3c7;
    color: #92400e;
    border: 1px solid #fde68a;
}
.hm-badge-descriptive {
    background-color: #fee2e2;
    color: #991b1b;
    border: 1px solid #fecaca;
}

/* Evidence Cards */
.hm-evidence-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-top: 3px solid #0f172a;
    border-radius: 6px;
    padding: 1.1rem 1.25rem;
    margin-bottom: 1rem;
    box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.04);
}
.hm-evidence-cat {
    font-size: 0.8rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: #0284c7;
    margin-bottom: 0.25rem;
}
.hm-evidence-headline {
    font-size: 1.15rem;
    font-weight: 700;
    color: #0f172a;
    margin-bottom: 0.75rem;
}
.hm-evidence-section {
    margin-bottom: 0.6rem;
    font-size: 0.88rem;
    line-height: 1.4;
}
.hm-evidence-section-title {
    font-size: 0.75rem;
    font-weight: 700;
    text-transform: uppercase;
    color: #475569;
    margin-bottom: 0.15rem;
}
.hm-evidence-obs {
    color: #0f172a;
    font-weight: 500;
}
.hm-evidence-ctx {
    color: #334155;
}
.hm-evidence-interp {
    background-color: #f8fafc;
    border-left: 3px solid #0284c7;
    padding: 0.5rem 0.75rem;
    font-size: 0.88rem;
    color: #0f172a;
    border-radius: 0 4px 4px 0;
    margin-top: 0.5rem;
    margin-bottom: 0.5rem;
}

/* Video Hypothesis Card */
.hm-film-card {
    background: #fffbeb;
    border: 1px solid #fef3c7;
    border-left: 4px solid #d97706;
    border-radius: 6px;
    padding: 0.85rem 1.1rem;
    margin-bottom: 0.85rem;
}
.hm-film-title {
    font-size: 0.75rem;
    font-weight: 800;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    color: #b45309;
    margin-bottom: 0.25rem;
}
.hm-film-question {
    font-size: 0.92rem;
    font-weight: 600;
    color: #78350f;
    line-height: 1.35;
}
.hm-film-anchor {
    font-size: 0.78rem;
    color: #92400e;
    margin-top: 0.35rem;
}

/* Provenance Footer */
.hm-provenance-box {
    background: #f1f5f9;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    padding: 0.75rem 1rem;
    font-size: 0.8rem;
    color: #475569;
    margin-top: 1.5rem;
}
</style>
"""

def render_badge(stability_tier: str) -> str:
    """Renders a clean styled HTML stability badge."""
    tier = str(stability_tier).upper()
    if "ESTABLISHED" in tier:
        return '<span class="hm-badge hm-badge-established">ESTABLISHED SIGNAL</span>'
    elif "USABLE" in tier:
        return '<span class="hm-badge hm-badge-usable">USABLE SIGNAL</span>'
    elif "EMERGING" in tier:
        return '<span class="hm-badge hm-badge-emerging">EMERGING SIGNAL</span>'
    else:
        return '<span class="hm-badge hm-badge-descriptive">LOW SAMPLE</span>'

def render_app_header(competition: str = "JBBL", season: str = "2025/26"):
    """Renders the top application header."""
    season_clean = season.replace("SEA_", "")
    if len(season_clean) == 4 and season_clean.isdigit():
        season_clean = f"{season_clean}/{str(int(season_clean)+1)[-2:]}"
    comp_clean = competition.replace("CMP_", "")
    
    st.markdown(clean_html(f"""
    <div class="hm-header-container">
        <div class="hm-club-title">Rheinland Falcons Rheinland · Youth Basketball Intelligence</div>
        <h1 class="hm-main-title">Player Intelligence & Scouting Dossier</h1>
        <div class="hm-subtitle"><strong>{comp_clean}</strong> · Season <strong>{season_clean}</strong> · Official Matches · Evidence-First Decision Support</div>
    </div>
    """), unsafe_allow_html=True)

def render_player_identity(bio: Dict[str, Any], stats: Dict[str, Any]):
    """Renders the player identity card with biometrics and rotational exposure."""
    name = bio.get("canonical_name") or bio.get("name") or "Unknown Player"
    pos = bio.get("position") or "Guard / Wing"
    age = bio.get("age_display") or "N/A"
    birth = bio.get("birth_year") or "N/A"
    height = bio.get("height_display") or "N/A"
    nat = bio.get("nationality_display") or bio.get("nationality") or "DE"
    
    gp = stats.get("gp", 0)
    dnp = stats.get("dnp_count", 0)
    tot_min = stats.get("total_min", 0.0)
    mpg = stats.get("mpg", 0.0)
    min_share = stats.get("min_share_pct", 0.0)

    st.markdown(clean_html(f"""
    <div class="hm-player-card">
        <div class="hm-player-name">{name}</div>
        <div class="hm-player-meta">{pos} · <strong>{age}</strong> (Born {birth}) · <strong>{height}</strong> · <strong>{nat}</strong></div>
        <div class="hm-player-stats-row">
            <div class="hm-stat-chip">📅 <strong>{gp}</strong> Games ({dnp} DNP)</div>
            <div class="hm-stat-chip">⏱️ <strong>{tot_min:.0f}</strong> Total Regulation Min</div>
            <div class="hm-stat-chip">⚡ <strong>{mpg:.1f}</strong> MPG</div>
            <div class="hm-stat-chip">📊 <strong>{min_share:.1f}%</strong> Team Minutes Share</div>
        </div>
    </div>
    """), unsafe_allow_html=True)

def render_kpi_card(
    label: str,
    value: str,
    percentile_text: str,
    stability_tier: str,
    volume_text: str,
    help_tooltip: Optional[str] = None
) -> str:
    """Returns HTML for an executive KPI card."""
    badge_html = render_badge(stability_tier)
    title_attr = f' title="{clean_html(help_tooltip)}"' if help_tooltip else ""
    info_icon = ' <span style="font-size:0.7rem; color:#94a3b8; cursor:help;">ℹ️</span>' if help_tooltip else ""
    html = f"""
    <div class="hm-kpi-card">
        <div>
            <div class="hm-kpi-label"{title_attr}>{label}{info_icon}</div>
            <div class="hm-kpi-value">{value}</div>
            <div class="hm-kpi-percentile">{percentile_text}</div>
            <div>{badge_html}</div>
        </div>
        <div class="hm-kpi-volume">{volume_text}</div>
    </div>
    """
    return clean_html(html)

def render_evidence_card(finding: Dict[str, Any]) -> str:
    """Renders a structured progressive disclosure evidence card."""
    category = finding.get("category", "Analysis")
    headline = finding.get("headline", "")
    observation = finding.get("observation", "")
    context = finding.get("context", "")
    volume_note = finding.get("volume_note", "")
    interpretation = finding.get("interpretation", "")
    stability_tier = finding.get("stability_tier", "EMERGING_SIGNAL")
    badge_html = render_badge(stability_tier)

    html = f"""
    <div class="hm-evidence-card">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.35rem;">
            <div class="hm-evidence-cat">{category}</div>
            <div>{badge_html}</div>
        </div>
        <div class="hm-evidence-headline">{headline}</div>
        <div class="hm-evidence-section">
            <div class="hm-evidence-section-title">1. Observed Production</div>
            <div class="hm-evidence-obs">{observation}</div>
        </div>
        <div class="hm-evidence-section">
            <div class="hm-evidence-section-title">2. League Benchmark Context</div>
            <div class="hm-evidence-ctx">{context}</div>
        </div>
        <div class="hm-evidence-interp">
            <strong>Interpretation:</strong> {interpretation}
        </div>
        <div class="hm-evidence-section">
            <div class="hm-evidence-section-title">3. Volume & Opportunity Diet</div>
            <div style="font-size: 0.8rem; color: #64748b;">{volume_note}</div>
        </div>
    </div>
    """
    return clean_html(html)

def render_film_card(finding: Dict[str, Any]) -> str:
    """Renders a tactical video review hypothesis."""
    cat = finding.get("category", "Tactical")
    q = finding.get("film_question", "")
    headline = finding.get("headline", "")
    obs = finding.get("observation", "")

    html = f"""
    <div class="hm-film-card">
        <div class="hm-film-title">📹 VIDEO HYPOTHESIS — NOT A STATISTICAL CLAIM · [{cat}]</div>
        <div class="hm-film-question">{q}</div>
        <div class="hm-film-anchor"><strong>Grounded in evidence:</strong> {headline} ({obs})</div>
    </div>
    """
    return clean_html(html)

def render_provenance_card(bench_meta: Dict[str, Any], freshness: Optional[Dict[str, Any]] = None) -> str:
    """Renders the official benchmark provenance metadata block."""
    season = str(bench_meta.get("season_id", "SEA_2025")).replace("SEA_", "")
    comp = str(bench_meta.get("competition_id", "CMP_JBBL")).replace("CMP_", "")
    pop_n = bench_meta.get("qualified_pop_size", 34)
    min_min = bench_meta.get("min_minutes", 100.0)
    g_type = bench_meta.get("game_type", "OFFICIAL")
    
    fresh_date = freshness.get("latest_game_date", "2026-03-15") if freshness else "Latest matchday"

    html = f"""
    <div class="hm-provenance-box">
        <strong>📌 Benchmark Provenance & Category Standard:</strong><br>
        • <strong>Comparison Universe:</strong> N = {pop_n} qualified {comp} players from Season {season} ({g_type} matches only)<br>
        • <strong>Qualification Threshold:</strong> Minimum {min_min:.0f} regulation minutes within the isolated season<br>
        • <strong>Temporal Isolation:</strong> Zero cross-season mixing. All percentiles computed via non-parametric empirical CDF<br>
        • <strong>Database Freshness:</strong> Synced through official matchday {fresh_date}
    </div>
    """
    return clean_html(html)

# Native Streamlit container display methods
def display_kpi_card(
    label: str,
    value: str,
    percentile_text: str,
    stability_tier: str,
    volume_text: str,
    help_tooltip: Optional[str] = None
):
    """Renders an executive KPI card inside a native bordered container."""
    tier_upper = str(stability_tier).upper()
    if "ESTABLISHED" in tier_upper:
        badge_label = "🟢 ESTABLISHED"
    elif "USABLE" in tier_upper:
        badge_label = "🔵 USABLE"
    elif "EMERGING" in tier_upper:
        badge_label = "🟡 EMERGING"
    else:
        badge_label = "🔴 LOW SAMPLE"

    with st.container(border=True):
        if help_tooltip:
            st.caption(f"**{label.upper()}**", help=help_tooltip)
        else:
            st.caption(f"**{label.upper()}**")
        st.markdown(f"<div style='font-size: 1.45rem; font-weight: 800; color: #0f172a; line-height: 1.1; margin-bottom: 0.25rem;'>{value}</div>", unsafe_allow_html=True)
        st.markdown(f"<div style='font-size: 0.82rem; font-weight: 700; color: #0284c7; margin-bottom: 0.25rem;'>{percentile_text} · <span style='font-size:0.75rem; color:#475569;'>{badge_label}</span></div>", unsafe_allow_html=True)
        st.caption(volume_text)

def display_evidence_card(finding: Dict[str, Any]):
    """Renders a structured progressive disclosure evidence card inside a native bordered container."""
    category = finding.get("category", "Analysis")
    headline = finding.get("headline", "")
    observation = finding.get("observation", "")
    context = finding.get("context", "")
    volume_note = finding.get("volume_note", "")
    interpretation = finding.get("interpretation", "")
    stability_tier = finding.get("stability_tier", "EMERGING_SIGNAL")
    
    tier_upper = str(stability_tier).upper()
    if "ESTABLISHED" in tier_upper:
        badge_label = "🟢 ESTABLISHED SIGNAL"
    elif "USABLE" in tier_upper:
        badge_label = "🔵 USABLE SIGNAL"
    elif "EMERGING" in tier_upper:
        badge_label = "🟡 EMERGING SIGNAL"
    else:
        badge_label = "🔴 LOW SAMPLE"

    with st.container(border=True):
        col_c, col_b = st.columns([2, 1])
        with col_c:
            st.caption(f"**{category.upper()}**")
        with col_b:
            st.markdown(f"<div style='text-align: right; font-size:0.75rem; font-weight:700; color:#334155;'>{badge_label}</div>", unsafe_allow_html=True)
            
        st.markdown(f"#### {headline}")
        
        st.markdown("**1. Observed Production**")
        st.write(observation)
        
        st.markdown("**2. League Benchmark Context**")
        st.write(context)
        
        st.info(f"**Interpretation:** {interpretation}")
        
        st.markdown("**3. Volume & Opportunity Diet**")
        st.caption(volume_note)

def display_film_card(finding: Dict[str, Any]):
    """Renders a tactical video review hypothesis in a native callout container."""
    cat = finding.get("category", "Tactical")
    q = finding.get("film_question", "")
    headline = finding.get("headline", "")
    obs = finding.get("observation", "")

    with st.container(border=True):
        st.warning(f"**📹 VIDEO HYPOTHESIS — NOT A STATISTICAL CLAIM · [{cat}]**\n\n**{q}**\n\n*Grounded in evidence:* `{headline}` ({obs})")

def display_provenance_card(bench_meta: Dict[str, Any], freshness: Optional[Dict[str, Any]] = None):
    """Renders official benchmark provenance metadata in a native container."""
    season = str(bench_meta.get("season_id", "SEA_2025")).replace("SEA_", "")
    comp = str(bench_meta.get("competition_id", "CMP_JBBL")).replace("CMP_", "")
    pop_n = bench_meta.get("qualified_pop_size", 34)
    min_min = bench_meta.get("min_minutes", 100.0)
    g_type = bench_meta.get("game_type", "OFFICIAL")
    fresh_date = freshness.get("latest_game_date", "2026-03-15") if freshness else "Latest matchday"

    with st.container(border=True):
        st.markdown(f"""
        **📌 Benchmark Provenance & Category Standard:**
        - **Comparison Universe:** N = {pop_n} qualified {comp} players from Season {season} ({g_type} matches only)
        - **Qualification Threshold:** Minimum {min_min:.0f} regulation minutes within the isolated season
        - **Temporal Isolation:** Zero cross-season mixing. All percentiles computed via non-parametric empirical CDF
        - **Database Freshness:** Synced through official matchday {fresh_date}
        """)
