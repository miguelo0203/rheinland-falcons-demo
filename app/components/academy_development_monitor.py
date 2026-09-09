"""Academy Development Monitoring (Hub 6) UI Component.

Provides youth academy directors and coaching staff with a strategic, evidence-first overview
of player trajectory and development across U16 (JBBL) and U19 (NBBL).

Core Features:
1. Academy Overview KPIs and category-isolated cohort breakdowns.
2. Primary Development Monitor Table (understandable without opening inspector).
3. Top Improving Players highlight cards.
4. Players Requiring Attention ("Needs Attention") constructive coaching cards.
5. U16 -> U19 Development Pipeline screening matrix (PASS / NOT MET / UNAVAILABLE).
6. Deep-Dive "Why?" Diagnostic Inspector with multi-window statistical comparison.
"""

from typing import Any, Dict, List, Optional
import streamlit as st
import pandas as pd
from app.services.data_service import DataService


def _navigate_to_player_dossier(canonical_name: str, player_squad: str = "U16", current_squad_scope: str = "U16"):
    """Transitions navigation to Hub 1 pre-selected to the athlete, preserving squad scope."""
    st.session_state["pending_navigation_hub"] = "1. 👤 Player Intelligence & Coach Dossier"
    st.session_state["pending_perspective"] = "🚀 Full Career Trajectory"
    st.session_state["nav_target_player"] = canonical_name

    # Preserve or update squad scope safely
    if current_squad_scope == "All Academy":
        st.session_state["pending_squad_scope"] = "All Academy"
    elif player_squad == "U19":
        st.session_state["pending_squad_scope"] = "U19 (NBBL)"
    else:
        st.session_state["pending_squad_scope"] = "U16 (JBBL)"

    st.rerun()


def render_academy_development_monitor(
    ds: DataService,
    squad_scope: str = "U16",
    season_id: str = "SEA_2025",
    as_of_date: Optional[str] = None
):
    """Renders the Academy Development Monitoring Hub 6."""
    st.markdown("## 📈 Academy Development Monitoring")
    st.caption(
        "Academy-wide developmental tracking across U16 (JBBL) and U19 (NBBL). "
        "Evaluates temporal multi-window trajectories across Efficiency, On-Court Impact, Production, and Role. "
        "Strictly enforces possession-volume gating and multi-dimensional confirmation."
    )

    # 1. Fetch batch data from DataService
    with st.spinner("Analyzing academy developmental trajectories..."):
        profiles = ds.get_academy_development_monitor(season_id=season_id, squad_scope=squad_scope, as_of_date=as_of_date)
        summary = ds.get_academy_development_summary(season_id=season_id, squad_scope=squad_scope, as_of_date=as_of_date)

    if not profiles:
        st.info(f"No academy roster records discovered for season **{season_id}** and squad scope **{squad_scope}**.")
        return

    # Epistemic / Provenance Banner
    u19_count = summary.get("u19_breakdown", {}).get("total", 0)
    u19_games = sum(1 for p in profiles if p.get("squad") == "U19" and p.get("baseline_window", {}).get("gp", 0) > 0)
    if squad_scope == "U19" or (squad_scope == "All Academy" and u19_count > 0 and u19_games == 0):
        st.info(
            f"ℹ️ **U19 / NBBL Roster Status:** {u19_count} athletes registered on official roster. "
            "Match boxscores and on-court stint ratings will activate dynamically upon ingestion of official NBBL game records."
        )

    # =========================================================================
    # SECTION 1: ACADEMY OVERVIEW (KPI CARDS)
    # =========================================================================
    st.markdown("### 📊 Academy Overview")

    kpi1, kpi2, kpi3, kpi4, kpi5, kpi6 = st.columns(6)
    with kpi1:
        st.metric("Total Athletes", summary.get("total_players", 0))
    with kpi2:
        st.metric("🟢 Improving", summary.get("improving_count", 0), help="Demonstrating confirmed multi-dimensional positive momentum.")
    with kpi3:
        st.metric("⚪ Stable", summary.get("stable_count", 0), help="Performing consistently within established baseline equilibrium.")
    with kpi4:
        st.metric("🟡 Stagnating", summary.get("stagnating_count", 0), help="Regular rotation (>=10 MPG, >=8 GP) with flat development across multiple windows.")
    with kpi5:
        st.metric("🔴 Needs Attention", summary.get("declining_count", 0), help="Meaningful downward divergence in efficiency, impact, or role.")
    with kpi6:
        st.metric("⚪ Insufficient Data", summary.get("insufficient_data_count", 0), help="Sample below minimum floor (< 4 matches or < 20 minutes).")

    # Cohort Breakdown if All Academy is active
    if squad_scope == "All Academy":
        u16_b = summary.get("u16_breakdown", {})
        u19_b = summary.get("u19_breakdown", {})
        with st.expander("📁 Cohort Breakdown (Strict Category Isolation)", expanded=False):
            c_col1, c_col2 = st.columns(2)
            with c_col1:
                st.markdown(
                    f"**U16 / JBBL Cohort ({u16_b.get('total', 0)} Athletes):**<br>"
                    f"• Improving: **{u16_b.get('improving', 0)}** · Stable: **{u16_b.get('stable', 0)}** · "
                    f"Stagnating: **{u16_b.get('stagnating', 0)}** · Declining: **{u16_b.get('declining', 0)}** · "
                    f"Insufficient Data: **{u16_b.get('insufficient_data', 0)}**",
                    unsafe_allow_html=True
                )
            with c_col2:
                st.markdown(
                    f"**U19 / NBBL Cohort ({u19_b.get('total', 0)} Athletes):**<br>"
                    f"• Improving: **{u19_b.get('improving', 0)}** · Stable: **{u19_b.get('stable', 0)}** · "
                    f"Stagnating: **{u19_b.get('stagnating', 0)}** · Declining: **{u19_b.get('declining', 0)}** · "
                    f"Insufficient Data: **{u19_b.get('insufficient_data', 0)}**",
                    unsafe_allow_html=True
                )
            st.caption("Peer comparison benchmarks and percentiles are isolated strictly by competition. Categories are never merged into a combined standard.")

    st.markdown("---")

    # =========================================================================
    # SECTION 2: PRIMARY DEVELOPMENT MONITOR TABLE
    # =========================================================================
    st.markdown("### 📋 Primary Development Monitor")
    st.caption("At-a-glance development status, multi-window deltas, and sample evidence. All rates recalculated from raw counts.")

    # Filter controls
    f_col1, f_col2, f_col3 = st.columns([2, 2, 2])
    with f_col1:
        status_options = ["All Statuses", "IMPROVING", "STABLE", "STAGNATING", "DECLINING", "INSUFFICIENT DATA"]
        sel_status = st.selectbox("Filter by Status", status_options, index=0, key="adm_status_filter")
    with f_col2:
        evidence_options = ["All Evidence Strengths", "STRONG EVIDENCE", "MODERATE EVIDENCE", "LIMITED EVIDENCE", "INSUFFICIENT EVIDENCE"]
        sel_evidence = st.selectbox("Filter by Evidence", evidence_options, index=0, key="adm_evidence_filter")
    with f_col3:
        search_query = st.text_input("Search Athlete Name", placeholder="e.g. Fall, Weber...", key="adm_search_name")

    with st.expander("ℹ️ Evidence Strength Guide (Data Confidence Levels)", expanded=False):
        st.markdown("""
        <div style="font-size: 0.85rem; line-height: 1.6; color: #334155;">
            • <strong>Strong Evidence:</strong> Enough games (≥8 GP) and data volume to support a reliable multi-signal development assessment.<br>
            • <strong>Moderate Evidence:</strong> Enough data (4–7 GP) to identify a useful trend, but some evidence or volume checks are limited.<br>
            • <strong>Limited Evidence:</strong> Early or incomplete sample. Treat the trend with caution.<br>
            • <strong>Insufficient Evidence:</strong> Not enough reliable data (&lt; 4 matches or &lt; 20 regulation minutes) to assess development.
        </div>
        """, unsafe_allow_html=True)

    # Filter profiles
    filtered_profiles = profiles
    if sel_status != "All Statuses":
        filtered_profiles = [p for p in filtered_profiles if p.get("status") == sel_status]
    if sel_evidence != "All Evidence Strengths":
        filtered_profiles = [p for p in filtered_profiles if p.get("evidence_strength") == sel_evidence]
    if search_query:
        q_lower = search_query.strip().lower()
        filtered_profiles = [p for p in filtered_profiles if q_lower in p.get("canonical_name", "").lower()]

    # Format table records
    table_rows = []
    for p in filtered_profiles:
        d = p.get("deltas", {})
        w_rec = p.get("recent_window", {})
        status_str = p.get("status_badge", p.get("status", ""))

        # TS% Delta formatting
        d_ts = d.get("delta_ts_pct")
        if d_ts is not None:
            ts_str = f"{d_ts:+0.1f} pp"
        else:
            ts_str = "—"

        # Net Rating Delta formatting with possession gating indicator
        d_net = d.get("delta_net_rtg")
        is_net_eligible = d.get("net_rtg_eligible_for_classification", False)
        rec_poss = d.get("net_rtg_recent_poss", 0.0)
        comp_poss = d.get("net_rtg_comp_poss", 0.0)

        if d_net is not None:
            if is_net_eligible:
                net_str = f"{d_net:+0.1f}"
            else:
                net_str = f"{d_net:+0.1f} (Low Vol: {rec_poss:.0f}p)"
        else:
            net_str = "—"

        # MPG Delta formatting
        d_mpg = d.get("delta_mpg", 0.0)
        mpg_str = f"{d_mpg:+0.1f}" if w_rec.get("gp", 0) > 0 else "—"

        # PPG Delta formatting
        d_ppg = d.get("delta_ppg", 0.0)
        ppg_str = f"{d_ppg:+0.1f}" if w_rec.get("gp", 0) > 0 else "—"

        # Evidence strength short code
        ev_strength = p.get("evidence_strength", "")
        ev_short = ev_strength.replace(" EVIDENCE", "")

        table_rows.append({
            "Athlete": p.get("canonical_name", ""),
            "Squad": p.get("squad", ""),
            "Status": status_str,
            "Evidence": ev_short,
            "TS% Δ": ts_str,
            "Net Rtg Δ": net_str,
            "MPG Δ": mpg_str,
            "PPG Δ": ppg_str,
            "Sample": p.get("sample_summary", ""),
            "player_id": p.get("player_id", "")
        })

    df_table = pd.DataFrame(table_rows)
    if not df_table.empty:
        event = st.dataframe(
            df_table[["Athlete", "Squad", "Status", "Evidence", "TS% Δ", "Net Rtg Δ", "MPG Δ", "PPG Δ", "Sample"]],
            use_container_width=True,
            hide_index=True,
            on_select="rerun",
            selection_mode="single-row",
            key="adm_table_view"
        )

        selected_tbl_name = None
        if event and hasattr(event, "selection") and event.selection.rows:
            sel_r_idx = event.selection.rows[0]
            if sel_r_idx < len(filtered_profiles):
                selected_tbl_name = filtered_profiles[sel_r_idx].get("canonical_name")

        c_act1, c_act2, _ = st.columns([2.5, 1.2, 2.3])
        with c_act1:
            p_names_list = [p.get("canonical_name", "") for p in filtered_profiles]
            default_tbl_idx = 0
            if selected_tbl_name and selected_tbl_name in p_names_list:
                default_tbl_idx = p_names_list.index(selected_tbl_name)
            chosen_tbl_player = st.selectbox(
                "Open Player Dossier from Table:",
                options=p_names_list,
                index=default_tbl_idx,
                key="adm_table_jump_select",
                help="Click a row above or select an athlete from this dropdown to open their Hub 1 development dossier."
            )
        with c_act2:
            st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
            if st.button("👤 Open Dossier", key="btn_adm_tbl_jump", type="primary", use_container_width=True):
                p_match = next((p for p in filtered_profiles if p.get("canonical_name") == chosen_tbl_player), None)
                p_sq = p_match.get("squad", "U16") if p_match else "U16"
                _navigate_to_player_dossier(chosen_tbl_player, player_squad=p_sq, current_squad_scope=squad_scope)
    else:
        st.info("No athletes match the selected filter criteria.")

    st.markdown("---")

    # =========================================================================
    # SECTION 3: TOP IMPROVING PLAYERS
    # =========================================================================
    improving_players = [p for p in profiles if p.get("status") == "IMPROVING"]
    st.markdown("### 🚀 Top Developing Athletes")
    st.caption("Athletes exhibiting confirmed positive developmental momentum across efficiency, role, or on-court impact.")

    if improving_players:
        cols = st.columns(min(3, len(improving_players)))
        for idx, p in enumerate(improving_players):
            col = cols[idx % len(cols)]
            with col:
                d = p.get("deltas", {})
                w_rec = p.get("recent_window", {})
                w_base = p.get("baseline_window", {})

                d_ts = d.get("delta_ts_pct")
                d_net = d.get("delta_net_rtg")
                net_elig = d.get("net_rtg_eligible_for_classification", False)

                ts_disp = f"{d_ts:+0.1f} pp" if d_ts is not None else "—"
                if d_net is not None:
                    net_disp = f"{d_net:+0.1f}" if net_elig else f"{d_net:+0.1f} (Low Vol)"
                else:
                    net_disp = "—"

                st.markdown(
                    f"""
                    <div style="background-color: #f8fafc; border: 1px solid #cbd5e1; border-left: 5px solid #22c55e; border-radius: 8px; padding: 14px; margin-bottom: 12px;">
                        <div style="font-weight: 700; font-size: 1.05rem; color: #0f172a;">{p.get('canonical_name')}</div>
                        <div style="font-size: 0.8rem; color: #64748b; margin-bottom: 8px;">{p.get('squad')} · {p.get('evidence_strength')}</div>
                        <div style="font-size: 0.85rem; line-height: 1.5; color: #1e293b;">
                            • <strong>TS% Δ:</strong> <span style="color: #15803d; font-weight: 600;">{ts_disp}</span> ({w_rec.get('ts_pct', 0.0)}% recent)<br>
                            • <strong>Net Rtg Δ:</strong> <span style="color: #15803d; font-weight: 600;">{net_disp}</span><br>
                            • <strong>Role Δ:</strong> {d.get('delta_mpg', 0.0):+0.1f} MPG ({w_rec.get('mpg', 0.0):.1f} MPG)<br>
                            • <strong>Scoring Δ:</strong> {d.get('delta_ppg', 0.0):+0.1f} PPG ({w_rec.get('ppg', 0.0):.1f} PPG)
                        </div>
                        <div style="font-size: 0.75rem; color: #64748b; margin-top: 8px; border-top: 1px dashed #e2e8f0; padding-top: 6px;">
                            Sample: {p.get('sample_summary')}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                if st.button("👤 Open Dossier", key=f"btn_nav_top_{p.get('player_id')}", use_container_width=True):
                    _navigate_to_player_dossier(p.get("canonical_name"), player_squad=p.get("squad", "U16"), current_squad_scope=squad_scope)
    else:
        st.info("No athletes currently meet the strict multi-dimensional threshold for IMPROVING in this squad scope.")

    st.markdown("---")

    # =========================================================================
    # SECTION 4: PLAYERS REQUIRING ATTENTION ("NEEDS ATTENTION")
    # =========================================================================
    attention_players = [
        p for p in profiles 
        if p.get("status") == "DECLINING" or p.get("status") == "STAGNATING" or len(p.get("attention_flags", [])) > 0
    ]
    # Exclude purely small sample players unless they have active games
    attention_players = [p for p in attention_players if p.get("baseline_window", {}).get("gp", 0) >= 4]

    st.markdown("### ⚠️ Athletes Requiring Development Attention")
    st.caption("Constructive coaching alerts highlighting efficiency drop-offs, rotation reductions, or turnover spikes.")

    if attention_players:
        att_cols = st.columns(min(3, len(attention_players)))
        for idx, p in enumerate(attention_players):
            col = att_cols[idx % len(att_cols)]
            with col:
                d = p.get("deltas", {})
                w_rec = p.get("recent_window", {})
                border_color = "#ef4444" if p.get("status") == "DECLINING" else ("#eab308" if p.get("status") == "STAGNATING" else "#94a3b8")

                flags_str = " · ".join([f.replace("_", " ") for f in p.get("attention_flags", [])]) if p.get("attention_flags") else "GENERAL MONITORING"

                d_ts = d.get("delta_ts_pct")
                ts_disp = f"{d_ts:+0.1f} pp" if d_ts is not None else "—"

                d_net = d.get("delta_net_rtg")
                net_elig = d.get("net_rtg_eligible_for_classification", False)
                if d_net is not None:
                    net_disp = f"{d_net:+0.1f}" if net_elig else f"{d_net:+0.1f} (Low Vol)"
                else:
                    net_disp = "—"

                st.markdown(
                    f"""
                    <div style="background-color: #f8fafc; border: 1px solid #cbd5e1; border-left: 5px solid {border_color}; border-radius: 8px; padding: 14px; margin-bottom: 12px;">
                        <div style="font-weight: 700; font-size: 1.05rem; color: #0f172a;">{p.get('canonical_name')}</div>
                        <div style="font-size: 0.8rem; color: #64748b; margin-bottom: 6px;">{p.get('squad')} · {p.get('status_badge')}</div>
                        <div style="font-size: 0.75rem; font-weight: 700; color: #b91c1c; margin-bottom: 8px;">FLAGS: {flags_str}</div>
                        <div style="font-size: 0.85rem; line-height: 1.5; color: #1e293b;">
                            • <strong>TS% Δ:</strong> {ts_disp} ({w_rec.get('ts_pct', 0.0)}% recent)<br>
                            • <strong>Net Rtg Δ:</strong> {net_disp}<br>
                            • <strong>Role Δ:</strong> {d.get('delta_mpg', 0.0):+0.1f} MPG ({w_rec.get('mpg', 0.0):.1f} MPG)<br>
                            • <strong>Turnover Δ:</strong> {d.get('delta_topg', 0.0):+0.1f} TOPG
                        </div>
                        <div style="font-size: 0.75rem; color: #64748b; margin-top: 8px; border-top: 1px dashed #e2e8f0; padding-top: 6px;">
                            Sample: {p.get('sample_summary')}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                if st.button("👤 Open Dossier", key=f"btn_nav_att_{p.get('player_id')}", use_container_width=True):
                    _navigate_to_player_dossier(p.get("canonical_name"), player_squad=p.get("squad", "U16"), current_squad_scope=squad_scope)
    else:
        st.success("No active rotation athletes currently exhibit declining trends or active development concern flags.")

    st.markdown("---")

    # =========================================================================
    # SECTION 5: U16 -> U19 DEVELOPMENT PIPELINE
    # =========================================================================
    if squad_scope in ("U16", "All Academy"):
        st.markdown("### 🌟 U16 ➔ U19 Development Screening Matrix")
        st.caption(
            "Multi-dimensional screening evaluating U16 candidates across Sample Stability, Trajectory, Efficiency, Role, and On-Court Impact. "
            "Rejects arbitrary black-box scores in favor of transparent criteria pass/fail evaluations."
        )

        st.warning(
            "⚠️ **Methodological Notice:** This is an objective analytical screening filter. "
            "It does not replace physical maturity assessment, tactical role fit, or coaching staff discretion."
        )

        pipeline_candidates = ds.get_u16_to_u19_pipeline_candidates(season_id=season_id, as_of_date=as_of_date)

        if pipeline_candidates:
            # Group into Candidates vs Others
            highlighted = [c for c in pipeline_candidates if c.get("qualification_status") != "NOT CURRENTLY INDICATED"]
            other_c = [c for c in pipeline_candidates if c.get("qualification_status") == "NOT CURRENTLY INDICATED"]

            if highlighted:
                p_cols = st.columns(min(2, len(highlighted)))
                for idx, c in enumerate(highlighted):
                    col = p_cols[idx % len(p_cols)]
                    with col:
                        badge = c.get("qualification_badge", "")
                        b_stats = c.get("baseline_stats", {})

                        # Color status helpers
                        def _st_color(s_val: str) -> str:
                            if s_val == "PASS":
                                return "color: #15803d; font-weight: 700;"
                            elif s_val == "NOT MET":
                                return "color: #b91c1c; font-weight: 700;"
                            else:
                                return "color: #64748b; font-weight: 600;"

                        st.markdown(
                            f"""
                            <div style="background-color: #f8fafc; border: 1px solid #cbd5e1; border-left: 5px solid #3b82f6; border-radius: 8px; padding: 14px; margin-bottom: 12px;">
                                <div style="display: flex; justify-content: space-between; align-items: baseline;">
                                    <span style="font-weight: 700; font-size: 1.1rem; color: #0f172a;">{c.get('canonical_name')}</span>
                                    <span style="font-size: 0.85rem; font-weight: 700;">{badge}</span>
                                </div>
                                <div style="font-size: 0.8rem; color: #64748b; margin-bottom: 10px;">Season Baseline: {b_stats.get('gp', 0)} GP · {b_stats.get('mpg', 0.0):.1f} MPG · {b_stats.get('ppg', 0.0):.1f} PPG · {b_stats.get('ts_pct', 0.0):.1f}% TS</div>
                                <table style="width: 100%; font-size: 0.82rem; border-collapse: collapse; margin-bottom: 8px;">
                                    <tr style="border-bottom: 1px solid #f1f5f9;">
                                        <td style="padding: 4px 0; font-weight: 600; width: 35%;">1. Sample Stability</td>
                                        <td style="{_st_color(c['sample_stability']['status'])}; width: 20%;">{c['sample_stability']['status']}</td>
                                        <td style="color: #64748b; font-size: 0.78rem;">{c['sample_stability']['detail']}</td>
                                    </tr>
                                    <tr style="border-bottom: 1px solid #f1f5f9;">
                                        <td style="padding: 4px 0; font-weight: 600;">2. Trajectory</td>
                                        <td style="{_st_color(c['trajectory']['status'])};">{c['trajectory']['status']}</td>
                                        <td style="color: #64748b; font-size: 0.78rem;">{c['trajectory']['detail']}</td>
                                    </tr>
                                    <tr style="border-bottom: 1px solid #f1f5f9;">
                                        <td style="padding: 4px 0; font-weight: 600;">3. Efficiency</td>
                                        <td style="{_st_color(c['efficiency']['status'])};">{c['efficiency']['status']}</td>
                                        <td style="color: #64748b; font-size: 0.78rem;">{c['efficiency']['detail']}</td>
                                    </tr>
                                    <tr style="border-bottom: 1px solid #f1f5f9;">
                                        <td style="padding: 4px 0; font-weight: 600;">4. Role Capacity</td>
                                        <td style="{_st_color(c['role_capacity']['status'])};">{c['role_capacity']['status']}</td>
                                        <td style="color: #64748b; font-size: 0.78rem;">{c['role_capacity']['detail']}</td>
                                    </tr>
                                    <tr>
                                        <td style="padding: 4px 0; font-weight: 600;">5. On-Court Impact</td>
                                        <td style="{_st_color(c['on_court_impact']['status'])};">{c['on_court_impact']['status']}</td>
                                        <td style="color: #64748b; font-size: 0.78rem;">{c['on_court_impact']['detail']}</td>
                                    </tr>
                                </table>
                                <div style="font-size: 0.78rem; color: #334155; font-style: italic; background-color: #f1f5f9; padding: 6px 8px; border-radius: 4px;">
                                    {c.get('summary_notes')}
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

            with st.expander("📄 View Full U16 Screening Matrix (All Athletes)", expanded=False):
                matrix_rows = []
                for c in pipeline_candidates:
                    matrix_rows.append({
                        "Athlete": c.get("canonical_name"),
                        "Status": c.get("qualification_status"),
                        "Sample Stability": c["sample_stability"]["status"],
                        "Trajectory": c["trajectory"]["status"],
                        "Efficiency (TS%)": c["efficiency"]["status"],
                        "Role (MPG)": c["role_capacity"]["status"],
                        "Impact (Net Rtg)": c["on_court_impact"]["status"],
                    })
                st.dataframe(pd.DataFrame(matrix_rows), use_container_width=True, hide_index=True)

        st.markdown("---")

    # =========================================================================
    # SECTION 6: DEEP-DIVE "WHY?" DIAGNOSTIC INSPECTOR
    # =========================================================================
    st.markdown("### 🔍 Deep-Dive \"Why?\" Diagnostic Inspector")
    st.caption("Inspect exact multi-window aggregations, possession-volume evidence, and natural-language coaching rationale.")

    player_names = [p.get("canonical_name", "") for p in profiles]
    selected_name = st.selectbox("Select Athlete to Inspect", player_names, index=0, key="adm_why_selector")

    sel_profile = next((p for p in profiles if p.get("canonical_name") == selected_name), None)

    if sel_profile:
        # Header Badge & Evidence Summary
        h_col1, h_col2, h_col3 = st.columns([2.5, 1.2, 1.3])
        with h_col1:
            st.markdown(f"#### {sel_profile.get('canonical_name')} ({sel_profile.get('squad')})")
            st.markdown(
                f"**Classification:** {sel_profile.get('status_badge')} · "
                f"**Evidence Quality:** `{sel_profile.get('evidence_strength')}` "
                f"<span title='Strong: ≥8 GP with all volume guards passing.\nModerate: 4–7 GP or partial volume guards.\nLimited/Insufficient: Below statistical floor.' style='cursor: help; color: #0284c7;'>ℹ️</span>",
                unsafe_allow_html=True
            )
        with h_col2:
            st.caption(f"Season: `{sel_profile.get('season_id')}`<br>Sample: `{sel_profile.get('sample_summary')}`", unsafe_allow_html=True)
        with h_col3:
            st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
            if st.button("👤 Open Player Dossier", key="btn_why_open_dossier", type="primary", use_container_width=True):
                _navigate_to_player_dossier(sel_profile.get("canonical_name"), player_squad=sel_profile.get("squad", "U16"), current_squad_scope=squad_scope)

        # Narrative Box
        st.markdown(
            f"""
            <div style="background-color: #f1f5f9; border-left: 4px solid #0284c7; padding: 12px; border-radius: 6px; margin: 10px 0; font-size: 0.9rem; color: #0f172a; line-height: 1.6;">
                {sel_profile.get('why_narrative')}
            </div>
            """,
            unsafe_allow_html=True
        )

        # Primary Signals & Attention Flags
        sig_col, flag_col = st.columns([2, 1])
        with sig_col:
            st.markdown("**Auditable Evidence Signals:**")
            for sig in sel_profile.get("primary_signals", []):
                st.markdown(f"- {sig}")
        with flag_col:
            st.markdown("**Attention Flags:**")
            flags = sel_profile.get("attention_flags", [])
            if flags:
                for f in flags:
                    st.markdown(f"`{f}`")
            else:
                st.markdown("`NO ACTIVE FLAGS`")

        # Multi-Window Side-by-Side Comparison Table
        st.markdown("##### 📊 Multi-Window Statistical Comparison")
        w_rec = sel_profile.get("recent_window", {})
        w_prev = sel_profile.get("previous_window")
        w_base = sel_profile.get("baseline_window", {})
        deltas = sel_profile.get("deltas", {})
        comp_type = deltas.get("comparison_type", "NONE")

        comp_label = "Previous Window (5 Games)" if comp_type == "PREVIOUS_WINDOW" else "Season Baseline"
        w_comp = w_prev if (comp_type == "PREVIOUS_WINDOW" and w_prev) else w_base

        def _fmt(val, is_pct=False, is_rating=False):
            if val is None:
                return "—"
            if is_pct:
                return f"{val:.1f}%"
            if is_rating:
                return f"{val:+0.1f}"
            if isinstance(val, float):
                return f"{val:.1f}"
            return str(val)

        d_table = [
            {"Metric": "Matches Evaluated", "Recent Window": f"{w_rec.get('gp', 0)}", comp_label: f"{w_comp.get('gp', 0)}", "Season Baseline": f"{w_base.get('gp', 0)}", "Delta": "—"},
            {"Metric": "Playing Time (MPG)", "Recent Window": _fmt(w_rec.get('mpg')), comp_label: _fmt(w_comp.get('mpg')), "Season Baseline": _fmt(w_base.get('mpg')), "Delta": f"{deltas.get('delta_mpg', 0.0):+0.1f} MPG"},
            {"Metric": "Total Minutes", "Recent Window": _fmt(w_rec.get('total_minutes')), comp_label: _fmt(w_comp.get('total_minutes')), "Season Baseline": _fmt(w_base.get('total_minutes')), "Delta": "—"},
            {"Metric": "Scoring (PPG)", "Recent Window": _fmt(w_rec.get('ppg')), comp_label: _fmt(w_comp.get('ppg')), "Season Baseline": _fmt(w_base.get('ppg')), "Delta": f"{deltas.get('delta_ppg', 0.0):+0.1f} PPG"},
            {"Metric": "Field Goal Attempts/G", "Recent Window": _fmt(w_rec.get('fga_per_game')), comp_label: _fmt(w_comp.get('fga_per_game')), "Season Baseline": _fmt(w_base.get('fga_per_game')), "Delta": f"{deltas.get('delta_fga_pg', 0.0):+0.1f}"},
            {"Metric": "True Shooting (TS%)", "Recent Window": _fmt(w_rec.get('ts_pct'), is_pct=True), comp_label: _fmt(w_comp.get('ts_pct'), is_pct=True), "Season Baseline": _fmt(w_base.get('ts_pct'), is_pct=True), "Delta": f"{deltas.get('delta_ts_pct', 0.0) or 0.0:+0.1f} pp" if deltas.get('delta_ts_pct') is not None else "—"},
            {"Metric": "Effective FG (eFG%)", "Recent Window": _fmt(w_rec.get('efg_pct'), is_pct=True), comp_label: _fmt(w_comp.get('efg_pct'), is_pct=True), "Season Baseline": _fmt(w_base.get('efg_pct'), is_pct=True), "Delta": f"{deltas.get('delta_efg_pct', 0.0) or 0.0:+0.1f} pp" if deltas.get('delta_efg_pct') is not None else "—"},
            {
                "Metric": "On-Court Net Rating",
                "Recent Window": _fmt(w_rec.get('net_rtg'), is_rating=True),
                comp_label: _fmt(w_comp.get('net_rtg'), is_rating=True),
                "Season Baseline": _fmt(w_base.get('net_rtg'), is_rating=True),
                "Delta": f"{deltas.get('delta_net_rtg', 0.0) or 0.0:+0.1f}" if deltas.get('delta_net_rtg') is not None else "—"
            },
            {
                "Metric": "Reconstructable Stint Possessions",
                "Recent Window": f"{w_rec.get('stint_poss', 0.0):.1f}",
                comp_label: f"{w_comp.get('stint_poss', 0.0):.1f}",
                "Season Baseline": f"{w_base.get('stint_poss', 0.0):.1f}",
                "Delta": "Eligible (>= 20 poss)" if deltas.get('net_rtg_eligible_for_classification') else "Ineligible (< 20 poss)"
            },
            {"Metric": "Rebounds (RPG)", "Recent Window": _fmt(w_rec.get('rpg')), comp_label: _fmt(w_comp.get('rpg')), "Season Baseline": _fmt(w_base.get('rpg')), "Delta": f"{deltas.get('delta_rpg', 0.0):+0.1f} RPG"},
            {"Metric": "Assists (APG)", "Recent Window": _fmt(w_rec.get('apg')), comp_label: _fmt(w_comp.get('apg')), "Season Baseline": _fmt(w_base.get('apg')), "Delta": f"{deltas.get('delta_apg', 0.0):+0.1f} APG"},
            {"Metric": "Turnovers (TOPG)", "Recent Window": _fmt(w_rec.get('topg')), comp_label: _fmt(w_comp.get('topg')), "Season Baseline": _fmt(w_base.get('topg')), "Delta": f"{deltas.get('delta_topg', 0.0):+0.1f} TOPG"},
            {"Metric": "Assist / Turnover Ratio", "Recent Window": _fmt(w_rec.get('ast_to_tov')), comp_label: _fmt(w_comp.get('ast_to_tov')), "Season Baseline": _fmt(w_base.get('ast_to_tov')), "Delta": "—"},
        ]

        st.dataframe(pd.DataFrame(d_table), use_container_width=True, hide_index=True)
        st.caption(
            "Note: All rate statistics are computed strictly from raw sum totals in the respective windows. "
            "TS% (True Shooting) measures shooting efficiency across 2PT, 3PT, and FTs. "
            "Net Rating measures on-court point differential per 100 possessions. "
            "Net Rating deltas are excluded from driving classifications when possession volume is below 20.0 reconstructable possessions."
        )
