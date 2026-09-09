"""Hub 7: Video Analysis & Match Film UI Component for Rheinland Falcons Intelligence.

Orchestrates:
1. Match Selection & Registration (Official, Practice, Friendly, Scrimmage).
2. Multi-format Video Upload with Technical Metadata Extraction & Readiness Assessment.
3. Video Player with Sub-second Scrubbing & Timestamp Anchors.
4. Manual Clip Creation MVP Workflow (Category, Subcategory, Player Tagging, Notes).
5. Match Video Evidence Library with Cross-Platform References.
"""

import logging
import os
import shutil
import uuid
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import streamlit as st
import pandas as pd

logger = logging.getLogger("falcons.video.hub")

from python.analytics.video_metadata import (
    extract_video_metadata,
    format_seconds_to_timestamp,
    parse_timestamp_to_seconds,
    validate_clip_range
)
from app.components.video_player import render_video_player
from app.components.video_evidence import render_match_evidence_library

PROJECT_ROOT = Path(__file__).resolve().parents[2]
VIDEO_STORAGE_DIR = PROJECT_ROOT / "data" / "video"
VIDEO_STORAGE_DIR.mkdir(parents=True, exist_ok=True)


def generate_sample_demo_video(target_path: Path, duration_s: int = 60) -> bool:
    """Generates a synthetic demo basketball film clip for immediate testing and verification."""
    try:
        import cv2
        import numpy as np

        width, height = 1280, 720
        fps = 25.0
        total_frames = int(fps * duration_s)

        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        out = cv2.VideoWriter(str(target_path), fourcc, fps, (width, height))

        for f_idx in range(total_frames):
            frame = np.zeros((height, width, 3), dtype=np.uint8)
            # Court floor tint
            frame[:] = (35, 45, 55)

            # Paint court lines
            cv2.rectangle(frame, (100, 80), (1180, 640), (180, 180, 180), 3)
            cv2.line(frame, (640, 80), (640, 640), (180, 180, 180), 2)
            cv2.circle(frame, (640, 360), 70, (180, 180, 180), 2)
            cv2.rectangle(frame, (100, 260), (280, 460), (180, 180, 180), 2)
            cv2.rectangle(frame, (1000, 260), (1180, 460), (180, 180, 180), 2)

            # Current playback time overlay
            cur_sec = f_idx / fps
            ts_text = format_seconds_to_timestamp(cur_sec)
            cv2.putText(frame, "RHEINLAND FALCONS U16 vs NECKAR WOLVES U16 (TACTICAL DEMO FILM)", (110, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (2, 132, 199), 2)
            cv2.putText(frame, f"GAME CLOCK: {ts_text}", (110, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
            cv2.putText(frame, "#4 Lukas Weber [Weak-Side Rotation Zone]", (110, 680), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (220, 220, 220), 2)

            out.write(frame)

        out.release()
        return True
    except Exception as e:
        print(f"[ERROR] Could not generate sample video: {e}")
        return False


def render_video_hub(
    ds: Any,
    squad_scope: str = "U16",
    selected_season: str = "SEA_DEMO_2025",
    pop_mode: str = "ALL_GAMES"
):
    """Renders the main Video Analysis & Match Film Hub."""
    st.subheader(f"📹 Video Analysis & Match Film — {squad_scope}")
    st.caption(
        "First-class Video Evidence Layer for Rheinland Falcons. "
        "Transform match recordings into reusable, temporally precise tactical evidence linked across athlete dossiers, coach notes, and development objectives."
    )

    # --------------------------------------------------------------------------
    # 1. MATCH SELECTION & REGISTRATION
    # --------------------------------------------------------------------------
    st.markdown("### 🏟️ Step 1: Select or Register Match")

    # Fetch available games
    df_reg = ds.get_game_registry(pop_mode, squad_scope=squad_scope)
    falcons_team_id = "TEM_DEMO_U19" if squad_scope == "U19" else "TEM_DEMO_U16"

    # Filter games involving FALCONS
    if not df_reg.empty:
        falcons_games = df_reg[
            (df_reg["home_team_id"] == falcons_team_id) | (df_reg["away_team_id"] == falcons_team_id)
        ].copy()
    else:
        falcons_games = pd.DataFrame()

    match_mode = st.radio(
        "Match Selection Mode:",
        ["📋 Select Existing Registered Match", "➕ Register New Match (e.g. Scrimmage / Neckar Wolves)"],
        horizontal=True,
        key="video_hub_match_mode"
    )

    active_game_id = None
    active_match_name = ""
    active_game_type = "OFFICIAL"

    if match_mode == "📋 Select Existing Registered Match":
        if falcons_games.empty:
            st.warning(f"No match records found for {squad_scope}. Use 'Register New Match' below.")
        else:
            game_options = []
            for _, r in falcons_games.iterrows():
                v_badge = "📹 Film Available" if r.get("video_available") else "No Video"
                g_type_label = f"[{r.get('game_type', 'OFFICIAL')}]"
                game_options.append(f"{r['game_date']} — vs {r['falcons_opponent_name']} {g_type_label} ({v_badge}) [{r['game_id']}]")

            # Check if active match is pre-selected via cross-hub navigation
            nav_gid = st.session_state.get("video_active_match_id")
            default_m_idx = 0
            if nav_gid:
                for idx, opt in enumerate(game_options):
                    if nav_gid in opt:
                        default_m_idx = idx
                        break

            sel_match_idx = st.selectbox("Choose Match to Review:", range(len(game_options)), index=default_m_idx, format_func=lambda i: game_options[i], key="video_hub_match_select")
            g_row = falcons_games.iloc[sel_match_idx]
            active_game_id = g_row["game_id"]
            active_match_name = f"{g_row['home_team_name']} vs {g_row['away_team_name']}"
            active_game_type = g_row.get("game_type", "OFFICIAL")

    else:
        # Match Registration Form
        with st.form("form_register_match"):
            st.markdown("##### Register Match Fixture")
            c_m1, c_m2, c_m3 = st.columns(3)
            with c_m1:
                home_club = st.selectbox("Home Team:", ["Rheinland Falcons", "Neckar Wolves", "Other / Opponent"], index=0)
            with c_m2:
                away_club = st.selectbox("Away Team:", ["Neckar Wolves", "Rheinland Falcons", "Other / Opponent"], index=0)
            with c_m3:
                m_date = st.date_input("Match Date:", value=date(2026, 3, 20))

            c_t1, c_t2, c_t3 = st.columns(3)
            with c_t1:
                g_type_sel = st.selectbox(
                    "Game Type (Population Isolation):",
                    ["PRACTICE", "FRIENDLY", "OFFICIAL", "SCRIMMAGE", "OTHER"],
                    index=0,
                    help="Official games link to competition statistics. Practice and friendly fixtures are strictly isolated from official benchmarks."
                )
            with c_t2:
                comp_sel = st.selectbox("Competition Scope:", ["JBBL U16 Friendly", "JBBL U16 Official", "Academy Scrimmage"], index=0)
            with c_t3:
                venue_txt = st.text_input("Venue / Court:", value="Falcons Dome")

            submitted_match = st.form_submit_button("Register Match Fixture")
            if submitted_match:
                # Resolve team IDs
                h_id = "TEM_DEMO_U16" if "Falcons" in home_club else "TEM_NECKAR_WOLVES_U16"
                a_id = "TEM_NECKAR_WOLVES_U16" if "Neckar Wolves" in away_club else "TEM_DEMO_U16"
                new_gid = f"GAM_{squad_scope}_{g_type_sel}_{m_date.strftime('%Y%m%d')}_{uuid.uuid4().hex[:4].upper()}"

                ds.register_match_if_not_exists(
                    game_id=new_gid,
                    home_team_id=h_id,
                    away_team_id=a_id,
                    game_date=str(m_date),
                    game_type=g_type_sel,
                    season_id=selected_season,
                    competition_id="CMP_DEMO_U16" if g_type_sel == "OFFICIAL" else "CMP_ACADEMY_PRAC",
                    venue=venue_txt
                )
                st.session_state["video_active_match_id"] = new_gid
                st.success(f"Registered fixture `{new_gid}` ({home_club} vs {away_club}).")
                st.rerun()

        # If a match was just registered
        active_game_id = st.session_state.get("video_active_match_id")
        active_match_name = f"Registered Match [{active_game_id}]" if active_game_id else ""

    if not active_game_id:
        st.info("Select or register a match fixture to proceed with video analysis.")
        return

    # Match Population Badge
    is_official = (active_game_type == "OFFICIAL")
    p_badge = "🏆 OFFICIAL COMPETITION MATCH" if is_official else f"🛠️ {active_game_type} MATCH (ISOLATED FROM OFFICIAL STATS)"
    st.caption(f"Active Match: **{active_game_id}** · `{p_badge}`")

    st.markdown("---")

    # --------------------------------------------------------------------------
    # 2. VIDEO INGESTION & TECHNICAL METADATA INSPECTION
    # --------------------------------------------------------------------------
    st.markdown("### 🎥 Step 2: Match Video & Technical Inspection")

    # Check existing videos for this match
    match_videos = ds.get_videos_for_game(active_game_id)
    selected_video_id = None
    active_video = None

    if match_videos:
        v_options = [f"{v.get('filename', 'Video')} ({v.get('container_format', 'MP4')} · {format_seconds_to_timestamp(v.get('duration_seconds', 0.0))}) [{v['video_id']}]" for v in match_videos]
        sel_v_idx = st.selectbox("Available Videos for this Match:", range(len(v_options)), format_func=lambda i: v_options[i], key="video_select_for_match")
        active_video = match_videos[sel_v_idx]
        selected_video_id = active_video["video_id"]
    else:
        st.info(f"No video uploaded yet for match **{active_game_id}**.")

    with st.expander("📤 Upload Video or Generate Sample Demo Film", expanded=(active_video is None)):
        st.markdown("##### Upload Match Video File")
        st.caption("Supported common formats: `.mp4`, `.mov`, `.mkv`, `.webm`, `.avi`. Technical metadata extracted deterministically.")

        up_cols = st.columns([2, 1])
        with up_cols[0]:
            uploaded_file = st.file_uploader("Select Video File:", type=["mp4", "mov", "mkv", "webm", "avi"], key="match_video_file_uploader")
        with up_cols[1]:
            st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
            if st.button("🎬 Generate Sample Demo Video (Instant Test)", use_container_width=True, help="Creates a 60s sample MP4 with court markings for immediate hands-on verification."):
                demo_filename = f"sample_{active_game_id}.mp4"
                demo_file_path = VIDEO_STORAGE_DIR / demo_filename
                logger.info("Generating sample demo video at: %s", demo_file_path)
                with st.spinner("Rendering sample basketball tactical video..."):
                    gen_ok = generate_sample_demo_video(demo_file_path, duration_s=60)
                if gen_ok:
                    meta = extract_video_metadata(demo_file_path)
                    new_vid_id = ds.register_video({
                        "video_id": f"VID_DEMO_{uuid.uuid4().hex[:6].upper()}",
                        "game_id": active_game_id,
                        "file_path": str(demo_file_path),
                        "filename": demo_filename,
                        "duration_seconds": meta["duration_seconds"],
                        "container_format": meta["container_format"],
                        "codec": meta["codec"],
                        "resolution_width": meta["resolution_width"],
                        "resolution_height": meta["resolution_height"],
                        "fps": meta["fps"],
                        "file_size_bytes": meta["file_size_bytes"],
                        "checksum_sha256": meta["checksum_sha256"],
                        "camera_angle": "Tactical High",
                        "analysis_focus": ["Defense", "Weak-side rotation", "Player development"],
                        "notes": "Generated sample demo video for UI verification",
                        "processing_status": meta["processing_status"],
                        "readiness_status": meta["readiness_status"],
                        "audio_present": meta["audio_present"],
                        "created_by": "Coach"
                    })
                    logger.info("Sample demo video registered: %s (id: %s)", demo_filename, new_vid_id)
                    st.session_state["video_active_video_id"] = new_vid_id
                    st.success(f"Sample demo video generated & registered: `{new_vid_id}`")
                    st.rerun()

        # Check for local video files already placed in data/video
        local_vids = [
            f for f in sorted(VIDEO_STORAGE_DIR.iterdir())
            if f.is_file() and f.suffix.lower() in [".mp4", ".mov", ".mkv", ".webm", ".avi"]
        ]
        if local_vids:
            st.markdown("---")
            st.markdown("##### 📁 Attach Existing Local Video File (`data/video/`)")
            st.caption("Directly attach video files placed on the local disk without browser upload buffer delays.")
            c_loc1, c_loc2 = st.columns([2, 1])
            with c_loc1:
                loc_names = [f.name for f in local_vids]
                sel_loc_file = st.selectbox("Select File from `data/video/`:", loc_names, key="select_local_video_file")
            with c_loc2:
                st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
                if st.button("🔗 Attach & Inspect Local File", use_container_width=True):
                    chosen_path = VIDEO_STORAGE_DIR / sel_loc_file
                    meta = extract_video_metadata(chosen_path)
                    if meta["is_valid"]:
                        new_vid_id = ds.register_video({
                            "video_id": f"VID_{uuid.uuid4().hex[:10].upper()}",
                            "game_id": active_game_id,
                            "file_path": str(chosen_path),
                            "filename": sel_loc_file,
                            "duration_seconds": meta["duration_seconds"],
                            "container_format": meta["container_format"],
                            "codec": meta["codec"],
                            "resolution_width": meta["resolution_width"],
                            "resolution_height": meta["resolution_height"],
                            "fps": meta["fps"],
                            "file_size_bytes": meta["file_size_bytes"],
                            "checksum_sha256": meta["checksum_sha256"],
                            "camera_angle": "Tactical High",
                            "analysis_focus": ["Defense", "Tactical review"],
                            "notes": f"Attached directly from local storage: {sel_loc_file}",
                            "processing_status": meta["processing_status"],
                            "readiness_status": meta["readiness_status"],
                            "audio_present": meta["audio_present"],
                            "created_by": "Coach"
                        })
                        logger.info("Attached local video file: %s as %s for game %s", sel_loc_file, new_vid_id, active_game_id)
                        st.session_state["video_active_video_id"] = new_vid_id
                        st.success(f"Attached `{sel_loc_file}` as `{new_vid_id}`!")
                        st.rerun()
                    else:
                        st.error(f"Failed to inspect local video file: {meta.get('error_message')}")

        # Metadata form inputs if user uploads
        if uploaded_file is not None:
            c_f1, c_f2 = st.columns(2)
            with c_f1:
                focus_opts = st.multiselect(
                    "Analysis Focus:",
                    ["Team tactics", "Offense", "Defense", "Transition", "Player development", "Individual player", "Opponent scouting", "Full game review"],
                    default=["Defense", "Player development"],
                    key="video_upload_focus"
                )
            with c_f2:
                notes_txt = st.text_input("Notes (Optional):", value="Match footage for tactical review", key="video_upload_notes")

            if st.button("💾 Process & Save Uploaded Video", use_container_width=True):
                save_filename = f"{active_game_id}_{uploaded_file.name}"
                dest_path = VIDEO_STORAGE_DIR / save_filename
                logger.info("Processing uploaded video: %s -> %s", uploaded_file.name, dest_path)
                with st.spinner("Saving video file and inspecting technical parameters..."):
                    with open(dest_path, "wb") as f_out:
                        shutil.copyfileobj(uploaded_file, f_out)

                    meta = extract_video_metadata(dest_path)

                if meta["is_valid"]:
                    new_vid_id = ds.register_video({
                        "video_id": f"VID_{uuid.uuid4().hex[:10].upper()}",
                        "game_id": active_game_id,
                        "file_path": str(dest_path),
                        "filename": uploaded_file.name,
                        "duration_seconds": meta["duration_seconds"],
                        "container_format": meta["container_format"],
                        "codec": meta["codec"],
                        "resolution_width": meta["resolution_width"],
                        "resolution_height": meta["resolution_height"],
                        "fps": meta["fps"],
                        "file_size_bytes": meta["file_size_bytes"],
                        "checksum_sha256": meta["checksum_sha256"],
                        "camera_angle": "Tactical Wide",
                        "analysis_focus": focus_opts,
                        "notes": notes_txt,
                        "processing_status": meta["processing_status"],
                        "readiness_status": meta["readiness_status"],
                        "audio_present": meta["audio_present"],
                        "created_by": "Coach"
                    })
                    logger.info("Video processed and registered: %s (id: %s)", uploaded_file.name, new_vid_id)
                    st.session_state["video_active_video_id"] = new_vid_id
                    st.success(f"Video uploaded & processed successfully! ID: `{new_vid_id}`")
                    st.rerun()
                else:
                    logger.warning("Uploaded video validation failed: %s", meta.get("error_message"))
                    st.error(f"Video processing failed: {meta.get('error_message')}")

    if not active_video:
        st.info("Upload a video or generate sample demo film above to activate playback and clipping.")
        return

    # Technical Metadata & Video Analysis Readiness Scorecard
    with st.expander("📊 Technical Video Metadata & Analysis Readiness Scorecard", expanded=False):
        readiness = classify_video_readiness_display(active_video)
        st.markdown(f"#### Video Analysis Readiness: {readiness.get('badge')}")
        st.write(f"**Diagnostic Summary:** {readiness.get('headline')}")

        meta_col1, meta_col2, meta_col3, meta_col4 = st.columns(4)
        meta_col1.metric("Resolution", f"{active_video.get('resolution_width')}×{active_video.get('resolution_height')}", active_video.get("container_format"))
        meta_col2.metric("Duration", format_seconds_to_timestamp(active_video.get("duration_seconds", 0.0)), f"{active_video.get('fps', 0):.1f} FPS")
        meta_col3.metric("File Size", f"{(active_video.get('file_size_bytes', 0) / (1024*1024)):.1f} MB", active_video.get("codec"))
        meta_col4.metric("Audio Channel", "✅ Present" if active_video.get("audio_present", True) else "⚠️ Absent", "Whistle Analysis")

        st.markdown("##### Verifiable Technical Validation Checklist")
        for crit in readiness.get("criteria", []):
            st.markdown(f"- {crit['detail']}")
        st.caption(f"SHA-256 Provenance Checksum: `{active_video.get('checksum_sha256', 'N/A')}`")

    st.markdown("---")

    # --------------------------------------------------------------------------
    # 3. REUSABLE VIDEO PLAYER
    # --------------------------------------------------------------------------
    st.markdown("### 🎬 Step 3: Match Video Player & Tactical Playback")

    active_ev_id = st.session_state.get("video_active_evidence_id")
    active_evidence = ds.get_video_evidence(active_ev_id) if active_ev_id else None
    seek_time = st.session_state.get("video_seek_time", 0.0)

    render_video_player(
        video_path=active_video["file_path"],
        duration_seconds=float(active_video.get("duration_seconds", 0.0)),
        seek_time_s=float(seek_time),
        active_evidence=active_evidence,
        key_prefix="hub7_player"
    )

    st.markdown("---")

    # --------------------------------------------------------------------------
    # 4. MANUAL CLIP CREATION MVP WORKFLOW
    # --------------------------------------------------------------------------
    st.markdown("### ✂️ Step 4: Manual Clip Creation (MVP Workflow)")
    st.caption("Capture tactical evidence with exact temporal boundaries. Ground observations directly in film.")

    # Roster players for tagging
    falcons_players = ds.get_falcons_player_list(season_id=selected_season, squad_scope=squad_scope)
    player_options = {}
    for p in falcons_players:
        jersey = p.get("jersey_number", "")
        j_str = f"#{jersey} " if jersey else ""
        player_options[f"{j_str}{p['canonical_name']} ({p['player_id']})"] = p["player_id"]

    # Pre-select player #7 if present
    default_player_keys = []
    for k in player_options.keys():
        if "#7" in k or "Jonas" in k:
            default_player_keys.append(k)

    with st.form("form_create_video_evidence"):
        c_ts1, c_ts2, c_ts3 = st.columns(3)
        with c_ts1:
            start_in = st.text_input("Start Timestamp (MM:SS or s):", value=format_seconds_to_timestamp(seek_time), key="clip_start_input")
        with c_ts2:
            end_in = st.text_input("End Timestamp (MM:SS or s):", value=format_seconds_to_timestamp(seek_time + 15.0), key="clip_end_input")
        with c_ts3:
            clip_title = st.text_input("Clip Title / Headline:", value="Weak-side defensive rotation", key="clip_title_input")

        c_c1, c_c2 = st.columns(2)
        with c_c1:
            cat_choice = st.selectbox(
                "Tactical Category:",
                ["Defense", "Offense", "Transition", "Player Development", "Rebounding", "Special Situation / ATO", "Turnover Analysis"],
                index=0,
                key="clip_category_input"
            )
        with c_c2:
            subcat_choice = st.text_input("Subcategory:", value="Weak-side rotation", key="clip_subcategory_input")

        c_p1, c_p2 = st.columns(2)
        with c_p1:
            tagged_players = st.multiselect(
                "Associated Player(s):",
                list(player_options.keys()),
                default=default_player_keys,
                key="clip_tagged_players"
            )
        with c_p2:
            tags_txt = st.text_input("Tags (comma-separated):", value="defense, weak-side, rotation, pnr", key="clip_tags_input")

        clip_desc = st.text_area(
            "Coaching Observation / Tactical Description:",
            value="Late rotation from weak side after ball swing. Needs early communication and recovery angle.",
            key="clip_desc_input"
        )

        c_s1, c_s2 = st.columns(2)
        with c_s1:
            source_choice = st.selectbox("Evidence Source:", ["Coach", "AI", "AI + Coach Review"], index=0, key="clip_source_input")
        with c_s2:
            created_by_txt = st.text_input("Created By:", value="Coach Keller / Staff", key="clip_created_by")

        save_clip_btn = st.form_submit_button("💾 Save Video Evidence Clip", use_container_width=True)

        if save_clip_btn:
            start_s = parse_timestamp_to_seconds(start_in)
            end_s = parse_timestamp_to_seconds(end_in)
            dur_total = float(active_video.get("duration_seconds", 0.0))

            is_valid, val_msg = validate_clip_range(start_s, end_s, dur_total)
            if not is_valid:
                st.error(f"Validation Error: {val_msg}")
            else:
                p_ids = [player_options[k] for k in tagged_players if k in player_options]
                tag_list = [t.strip() for t in tags_txt.split(",") if t.strip()]

                new_eid = ds.create_video_evidence({
                    "evidence_id": f"EVD_{uuid.uuid4().hex[:8].upper()}",
                    "video_id": selected_video_id,
                    "game_id": active_game_id,
                    "start_time_s": start_s,
                    "end_time_s": end_s,
                    "title": clip_title,
                    "category": cat_choice,
                    "subcategory": subcat_choice,
                    "tags": tag_list,
                    "description": clip_desc,
                    "player_ids": p_ids,
                    "team_id": falcons_team_id,
                    "source": source_choice,
                    "confidence": 1.0 if source_choice == "Coach" else 0.85,
                    "review_status": "CONFIRMED" if source_choice == "Coach" else "PENDING_REVIEW",
                    "created_by": created_by_txt
                })
                logger.info("Saved Video Evidence: %s ('%s', %.1fs -> %.1fs, video: %s)", new_eid, clip_title, start_s, end_s, selected_video_id)
                st.session_state["video_active_evidence_id"] = new_eid
                st.session_state["video_seek_time"] = start_s
                st.success(f"Saved Video Evidence `{new_eid}`: '{clip_title}' ({format_seconds_to_timestamp(start_s)} ➔ {format_seconds_to_timestamp(end_s)}).")
                st.rerun()

    st.markdown("---")

    # --------------------------------------------------------------------------
    # 5. MATCH VIDEO EVIDENCE LIBRARY
    # --------------------------------------------------------------------------
    render_match_evidence_library(
        game_id=active_game_id,
        ds=ds,
        active_evidence_id=active_ev_id,
        key_prefix="hub7_lib"
    )


def classify_video_readiness_display(video_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Helper to compute deterministic readiness scorecard for display."""
    from python.analytics.video_metadata import classify_video_readiness
    w = int(video_dict.get("resolution_width") or 1280)
    h = int(video_dict.get("resolution_height") or 720)
    fps = float(video_dict.get("fps") or 25.0)
    dur = float(video_dict.get("duration_seconds") or 60.0)
    container = video_dict.get("container_format") or "MP4"
    audio = bool(video_dict.get("audio_present", True))
    return classify_video_readiness(
        width=w,
        height=h,
        fps=fps,
        duration_s=dur,
        container_format=container,
        stream_readable=(w > 0 and h > 0 and dur > 0),
        audio_present=audio
    )
