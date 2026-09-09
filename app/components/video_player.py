"""Reusable Video Player Component for Rheinland Falcons Basketball Platform.

Provides high-performance video streaming with:
- Sub-second temporal positioning and clip start anchoring
- Active clip context display (title, category, players, duration)
- Quick scrub controls (jump to start, jump to end, -5s, -1s, +1s, +5s)
- Visual timeline position indicator
- Fullscreen and speed adjustment via native browser controls
"""

from pathlib import Path
from typing import Any, Dict, Optional
import streamlit as st

from python.analytics.video_metadata import format_seconds_to_timestamp, parse_timestamp_to_seconds


def render_video_player(
    video_path: str,
    duration_seconds: float = 0.0,
    seek_time_s: float = 0.0,
    active_evidence: Optional[Dict[str, Any]] = None,
    key_prefix: str = "vid_player"
):
    """Renders the video player anchored to seek_time_s with tactical clip review controls."""
    p = Path(video_path)
    if not p.exists():
        st.error(f"Video file not found on disk: `{video_path}`. Verify storage location.")
        return

    # 1. Active Clip Banner (if focused on a specific piece of evidence)
    if active_evidence:
        start_fmt = format_seconds_to_timestamp(active_evidence.get("start_time_s", 0.0))
        end_fmt = format_seconds_to_timestamp(active_evidence.get("end_time_s", 0.0))
        dur_clip = active_evidence.get("end_time_s", 0.0) - active_evidence.get("start_time_s", 0.0)
        cat = active_evidence.get("category", "Tactical")
        subcat = active_evidence.get("subcategory", "")
        cat_disp = f"{cat} ➔ {subcat}" if subcat else cat
        title = active_evidence.get("title", "Active Clip")
        src = active_evidence.get("source", "Coach")
        conf = active_evidence.get("confidence")
        conf_badge = f" · Confidence: **{conf:.2f}**" if conf is not None else ""

        st.markdown(f"""
        <div style="background: #eff6ff; border: 1px solid #bfdbfe; border-left: 5px solid #0284c7; border-radius: 6px; padding: 10px 14px; margin-bottom: 12px;">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
                <div>
                    <span style="font-size: 0.75rem; font-weight: 800; text-transform: uppercase; color: #0369a1; letter-spacing: 0.05em;">🎬 ACTIVE VIDEO EVIDENCE · [{cat_disp}]</span>
                    <h4 style="margin: 2px 0 4px 0; color: #0f172a;">{title}</h4>
                </div>
                <div style="background: #ffffff; border: 1px solid #cbd5e1; border-radius: 4px; padding: 4px 10px; font-weight: 700; color: #0f172a; font-size: 0.85rem;">
                    ⏱️ {start_fmt} ➔ {end_fmt} ({dur_clip:.1f}s)
                </div>
            </div>
            <div style="font-size: 0.82rem; color: #334155; margin-top: 4px;">
                <strong>Source:</strong> {src}{conf_badge}
            </div>
            {f'<div style="font-size: 0.84rem; color: #1e293b; margin-top: 6px; font-style: italic;">Observation: {active_evidence.get("description")}</div>' if active_evidence.get("description") else ''}
        </div>
        """, unsafe_allow_html=True)

    # 2. Main Native Video Player
    # Streamlit passes start_time as integer seconds to browser media stream
    target_start_int = max(0, int(seek_time_s))
    st.video(str(p), start_time=target_start_int)

    # 3. Temporal Position & Scrubbing Toolbar
    cur_fmt = format_seconds_to_timestamp(seek_time_s)
    tot_fmt = format_seconds_to_timestamp(duration_seconds)

    col_info, col_controls = st.columns([1, 2])
    with col_info:
        st.markdown(f"""
        <div style="font-size: 0.85rem; color: #475569; padding-top: 6px;">
            📍 <strong>Player Anchor:</strong> <code>{cur_fmt}</code> / <code>{tot_fmt}</code>
        </div>
        """, unsafe_allow_html=True)

    with col_controls:
        # Quick Scrub Action Buttons
        b_cols = st.columns(6)
        
        # Jump to start of clip
        if active_evidence:
            start_val = active_evidence.get("start_time_s", 0.0)
            end_val = active_evidence.get("end_time_s", 0.0)
            with b_cols[0]:
                if st.button("⏮ Start", key=f"{key_prefix}_jump_start", help=f"Jump to clip start ({format_seconds_to_timestamp(start_val)})"):
                    st.session_state["video_seek_time"] = start_val
                    st.rerun()
            with b_cols[1]:
                if st.button("⏭ End", key=f"{key_prefix}_jump_end", help=f"Jump to clip end ({format_seconds_to_timestamp(end_val)})"):
                    st.session_state["video_seek_time"] = end_val
                    st.rerun()
        else:
            with b_cols[0]:
                if st.button("⏮ 00:00", key=f"{key_prefix}_jump_zero", help="Jump to start of video"):
                    st.session_state["video_seek_time"] = 0.0
                    st.rerun()
            with b_cols[1]:
                pass

        with b_cols[2]:
            if st.button("⏪ -5s", key=f"{key_prefix}_scrub_back_5", help="Seek 5 seconds backward"):
                st.session_state["video_seek_time"] = max(0.0, seek_time_s - 5.0)
                st.rerun()
        with b_cols[3]:
            if st.button("◀ -1s", key=f"{key_prefix}_scrub_back_1", help="Seek 1 second backward"):
                st.session_state["video_seek_time"] = max(0.0, seek_time_s - 1.0)
                st.rerun()
        with b_cols[4]:
            if st.button("▶ +1s", key=f"{key_prefix}_scrub_fwd_1", help="Seek 1 second forward"):
                st.session_state["video_seek_time"] = min(duration_seconds, seek_time_s + 1.0) if duration_seconds > 0 else seek_time_s + 1.0
                st.rerun()
        with b_cols[5]:
            if st.button("⏩ +5s", key=f"{key_prefix}_scrub_fwd_5", help="Seek 5 seconds forward"):
                st.session_state["video_seek_time"] = min(duration_seconds, seek_time_s + 5.0) if duration_seconds > 0 else seek_time_s + 5.0
                st.rerun()

    # 4. Interactive Direct Jump Input
    with st.expander("⏩ Jump to Exact Timestamp", expanded=False):
        c_in, c_btn = st.columns([3, 1])
        with c_in:
            jump_ts = st.text_input("Enter Timestamp (MM:SS or seconds):", value=cur_fmt, key=f"{key_prefix}_manual_jump_input")
        with c_btn:
            st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
            if st.button("Jump", key=f"{key_prefix}_manual_jump_btn", use_container_width=True):
                parsed = parse_timestamp_to_seconds(jump_ts)
                st.session_state["video_seek_time"] = parsed
                st.rerun()
