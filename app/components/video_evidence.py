"""Reusable Video Evidence Display Components for Rheinland Falcons Platform.

Enforces the core architectural principle:
    "Video is evidence, referenced everywhere by ID."
Allows embedding video clip references inside:
- Player Dossiers (Hub 1)
- Team Tactical Analysis (Hub 2)
- Game Lab & Match Deep Dive (Hub 3)
- Academy Development Monitoring (Hub 6)
- Coach Notes & Development Objectives
"""

from typing import Any, Dict, List, Optional
import streamlit as st

from python.analytics.video_metadata import format_seconds_to_timestamp


def navigate_to_clip(
    evidence_id: str,
    match_id: str,
    video_id: str,
    start_time_s: float
):
    """Transitions navigation to Hub 7 with the player positioned at the exact clip timestamp."""
    st.session_state["pending_navigation_hub"] = "7. 📹 Video Analysis & Match Film"
    st.session_state["video_active_match_id"] = match_id
    st.session_state["video_active_video_id"] = video_id
    st.session_state["video_active_evidence_id"] = evidence_id
    st.session_state["video_seek_time"] = start_time_s
    st.rerun()


def render_video_evidence_card(
    evidence: Dict[str, Any],
    ds: Any,
    show_player: bool = True,
    key_prefix: str = "ev_card"
):
    """Renders a single atomic VideoEvidence card with metadata and instant play action."""
    eid = evidence.get("evidence_id", "")
    title = evidence.get("title", "Video Evidence Clip")
    start_s = evidence.get("start_time_s", 0.0)
    end_s = evidence.get("end_time_s", 0.0)
    dur = end_s - start_s
    start_fmt = format_seconds_to_timestamp(start_s)
    end_fmt = format_seconds_to_timestamp(end_s)
    cat = evidence.get("category", "Tactical")
    subcat = evidence.get("subcategory", "")
    cat_label = f"{cat.upper()} · {subcat}" if subcat else cat.upper()
    desc = evidence.get("description", "")
    src = evidence.get("source", "Coach")
    game_id = evidence.get("game_id", "")
    video_id = evidence.get("video_id", "")

    # Match label
    opp_name = evidence.get("away_team_name") if "Falcons" in evidence.get("home_team_name", "") else evidence.get("home_team_name", "Match")
    match_label = f"vs {opp_name}" if opp_name else f"Match {game_id}"

    # Category color accent
    cat_upper = cat.upper()
    if "DEF" in cat_upper:
        accent_color = "#dc2626"  # Red for defense
        bg_accent = "#fef2f2"
    elif "OFF" in cat_upper:
        accent_color = "#2563eb"  # Blue for offense
        bg_accent = "#eff6ff"
    elif "TRANS" in cat_upper:
        accent_color = "#16a34a"  # Green for transition
        bg_accent = "#f0fdf4"
    else:
        accent_color = "#d97706"  # Amber for general/dev
        bg_accent = "#fffbeb"

    # Player labels
    player_names = []
    if show_player and evidence.get("player_ids"):
        pmap = ds.get_player_map() if hasattr(ds, "get_player_map") else {}
        for pid in evidence.get("player_ids", []):
            pname = pmap.get(pid, pid)
            player_names.append(pname)
    player_str = f" · 👤 {', '.join(player_names)}" if player_names else ""

    col_info, col_action = st.columns([4, 1])

    with col_info:
        st.markdown(f"""
        <div style="background-color: {bg_accent}; border: 1px solid #e2e8f0; border-left: 4px solid {accent_color}; border-radius: 6px; padding: 10px 14px; margin-bottom: 8px;">
            <div style="display: flex; justify-content: space-between; align-items: baseline; flex-wrap: wrap;">
                <span style="font-size: 0.75rem; font-weight: 800; letter-spacing: 0.05em; color: {accent_color};">{cat_label}</span>
                <span style="font-size: 0.8rem; font-weight: 700; color: #475569;">⏱️ {start_fmt} ➔ {end_fmt} ({dur:.1f}s)</span>
            </div>
            <div style="font-size: 0.98rem; font-weight: 700; color: #0f172a; margin-top: 2px;">{title}</div>
            <div style="font-size: 0.8rem; color: #64748b; margin-top: 2px;">
                🏟️ <strong>{match_label}</strong>{player_str} · Source: <code>{src}</code>
            </div>
            {f'<div style="font-size: 0.85rem; color: #1e293b; margin-top: 4px; line-height: 1.35;">{desc}</div>' if desc else ''}
        </div>
        """, unsafe_allow_html=True)

    with col_action:
        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
        btn_key = f"{key_prefix}_play_{eid}_{start_s}"
        if st.button("▶ Play Clip", key=btn_key, use_container_width=True, help=f"Open video anchored at {start_fmt}"):
            navigate_to_clip(
                evidence_id=eid,
                match_id=game_id,
                video_id=video_id,
                start_time_s=start_s
            )


def render_video_evidence_list(
    evidence_ids: List[str],
    ds: Any,
    title: Optional[str] = None,
    empty_message: str = "No video evidence attached.",
    key_prefix: str = "ev_list"
):
    """Renders a collection of VideoEvidence entities resolved by their surrogate IDs."""
    if title:
        st.markdown(f"#### {title}")

    if not evidence_ids:
        st.caption(empty_message)
        return

    # Batch retrieve evidence from repository
    evidence_list = ds.get_video_evidence_by_ids(evidence_ids)
    if not evidence_list:
        st.caption(empty_message)
        return

    for idx, ev in enumerate(evidence_list):
        render_video_evidence_card(
            evidence=ev,
            ds=ds,
            show_player=True,
            key_prefix=f"{key_prefix}_{idx}"
        )


def render_match_evidence_library(
    game_id: str,
    ds: Any,
    active_evidence_id: Optional[str] = None,
    key_prefix: str = "match_lib"
):
    """Renders the complete Video Evidence Library for a specific match with search, filter, play, and delete."""
    st.markdown("### 📚 Match Video Evidence Library")
    st.caption("Structured catalog of all tagged tactical moments and player observations for this match.")

    clips = ds.get_video_evidence_for_game(game_id)
    if not clips:
        st.info("No video evidence clips created yet for this match. Use the player controls above to mark and save clips.")
        return

    # Filter controls
    f_c1, f_c2, f_c3 = st.columns(3)
    with f_c1:
        categories = sorted(list(set(c.get("category", "General") for c in clips)))
        sel_cat = st.selectbox("Filter by Category:", ["All Categories"] + categories, key=f"{key_prefix}_cat_filter")
    with f_c2:
        sources = sorted(list(set(c.get("source", "Coach") for c in clips)))
        sel_src = st.selectbox("Filter by Source:", ["All Sources"] + sources, key=f"{key_prefix}_src_filter")
    with f_c3:
        search_query = st.text_input("Search Observation / Title:", "", key=f"{key_prefix}_search")

    filtered = clips
    if sel_cat != "All Categories":
        filtered = [c for c in filtered if c.get("category") == sel_cat]
    if sel_src != "All Sources":
        filtered = [c for c in filtered if c.get("source") == sel_src]
    if search_query:
        q = search_query.lower()
        filtered = [c for c in filtered if q in (c.get("title", "") + c.get("description", "") + c.get("subcategory", "")).lower()]

    st.markdown(f"**Found {len(filtered)} clip(s):**")

    pmap = ds.get_player_map() if hasattr(ds, "get_player_map") else {}

    for idx, clip in enumerate(filtered):
        eid = clip["evidence_id"]
        start_fmt = format_seconds_to_timestamp(clip["start_time_s"])
        end_fmt = format_seconds_to_timestamp(clip["end_time_s"])
        dur = clip["end_time_s"] - clip["start_time_s"]
        is_active = (active_evidence_id == eid)

        # Build player string
        p_names = [pmap.get(pid, pid) for pid in clip.get("player_ids", [])]
        p_str = ", ".join(p_names) if p_names else "Team / Unassigned"

        col_main, col_btn_play, col_btn_del = st.columns([5, 1, 1])

        with col_main:
            active_border = "border: 2px solid #0284c7; background-color: #f0f9ff;" if is_active else "border: 1px solid #e2e8f0; background-color: #ffffff;"
            st.markdown(f"""
            <div style="{active_border} border-radius: 6px; padding: 8px 12px; margin-bottom: 6px;">
                <div style="display: flex; justify-content: space-between; align-items: baseline;">
                    <span style="font-weight: 700; font-size: 0.95rem; color: #0f172a;">{clip['title']}</span>
                    <span style="font-size: 0.8rem; font-weight: 700; color: #0284c7;">⏱️ {start_fmt} – {end_fmt} ({dur:.1f}s)</span>
                </div>
                <div style="font-size: 0.8rem; color: #64748b; margin-top: 2px;">
                    <strong>{clip.get('category')}</strong> {f"➔ {clip.get('subcategory')}" if clip.get('subcategory') else ''} · 👤 <strong>{p_str}</strong> · Source: <code>{clip.get('source')}</code>
                </div>
                {f'<div style="font-size: 0.83rem; color: #334155; margin-top: 4px;">{clip.get("description")}</div>' if clip.get("description") else ''}
            </div>
            """, unsafe_allow_html=True)

        with col_btn_play:
            st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
            if st.button("▶ Play", key=f"{key_prefix}_lib_play_{eid}", use_container_width=True):
                st.session_state["video_active_evidence_id"] = eid
                st.session_state["video_seek_time"] = clip["start_time_s"]
                st.rerun()

        with col_btn_del:
            st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
            if st.button("🗑️ Del", key=f"{key_prefix}_lib_del_{eid}", use_container_width=True, help="Delete this clip"):
                ds.delete_video_evidence(eid)
                if st.session_state.get("video_active_evidence_id") == eid:
                    st.session_state.pop("video_active_evidence_id", None)
                st.success(f"Deleted clip {clip['title']}")
                st.rerun()
