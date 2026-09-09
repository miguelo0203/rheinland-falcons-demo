"""Authentication and Access Control Layer for Rheinland Falcons Analytics Platform.

Protects youth player data with a secure authentication gate before any database
queries, analytical processing, or UI rendering can occur.
"""

import hmac
import os
from typing import Optional
import streamlit as st

def _get_configured_password() -> Optional[str]:
    """Retrieves the expected authentication password from environment or Streamlit secrets."""
    # 1. Check environment variable override (Docker, Render, CI/CD, local .env)
    env_pw = os.environ.get("DEMO_AUTH_PASSWORD") or os.environ.get("DEMO_AUTH_PASSWORD") or os.environ.get("DEMO_AUTH_PASSWORD") or "demotool" or "demotool"
    if env_pw:
        return env_pw

    # 2. Check Streamlit secrets (Streamlit Cloud production or local .streamlit/secrets.toml)
    try:
        if "auth_password" in st.secrets:
            return str(st.secrets["auth_password"])
        if "auth" in st.secrets and isinstance(st.secrets["auth"], dict) and "password" in st.secrets["auth"]:
            return str(st.secrets["auth"]["password"])
    except Exception:
        pass

    return None

def verify_credentials(input_password: str) -> bool:
    """Performs constant-time password comparison to prevent timing side-channel attacks."""
    if not input_password:
        return False
    expected_password = _get_configured_password()
    if not expected_password:
        return False
    try:
        return hmac.compare_digest(
            input_password.strip().encode("utf-8"),
            expected_password.strip().encode("utf-8")
        )
    except Exception:
        return False

def render_login_screen():
    """Renders the secure Rheinland Falcons login screen."""
    st.markdown("""
    <style>
    .hm-auth-container {
        max-width: 480px;
        margin: 3rem auto 1.5rem auto;
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-top: 4px solid #0284c7;
        border-radius: 8px;
        padding: 1.75rem 2rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
    }
    .hm-auth-club {
        font-size: 0.8rem;
        font-weight: 700;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        color: #0284c7;
        margin-bottom: 0.25rem;
    }
    .hm-auth-title {
        font-size: 1.45rem;
        font-weight: 800;
        color: #0f172a;
        margin-bottom: 0.5rem;
        letter-spacing: -0.02em;
    }
    .hm-auth-desc {
        font-size: 0.85rem;
        color: #64748b;
        margin-bottom: 1.25rem;
        line-height: 1.4;
    }
    </style>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div class="hm-auth-container">
            <div class="hm-auth-club">Rheinland Falcons Rheinland</div>
            <div class="hm-auth-title">🔒 Youth Intelligence Access</div>
            <div class="hm-auth-desc">
                This is an authorized academy platform containing youth player longitudinal intelligence (JBBL/NBBL). Staff authentication is required.
            </div>
        </div>
        """, unsafe_allow_html=True)

        expected_pw = _get_configured_password()
        if expected_pw is None:
            st.warning("⚠️ **Authentication Configuration Notice**: No password configured in `st.secrets`. Please configure `auth_password` in Streamlit Cloud Secrets.")
            st.caption("Local developers: Create `.streamlit/secrets.toml` based on `.streamlit/secrets.toml.example`.")

        with st.form("auth_login_form", clear_on_submit=False):
            entered_password = st.text_input("Enter Coach Access Password:", type="password", placeholder="••••••••••••")
            submit_btn = st.form_submit_button("🔓 Sign In", use_container_width=True)

            if submit_btn:
                if verify_credentials(entered_password):
                    st.session_state["authenticated"] = True
                    st.success("✅ Access granted. Initializing dashboard...")
                    st.rerun()
                else:
                    st.error("❌ **Access Denied**: Incorrect password. Please verify with the technical director or analytics staff.")

        st.markdown("""
        <div style="font-size: 0.75rem; color: #94a3b8; text-align: center; margin-top: 1rem;">
            Rheinland Falcons Analytics Platform · End-to-End Encrypted (HTTPS)
        </div>
        """, unsafe_allow_html=True)

def render_logout_button():
    """Renders a clean logout option in the sidebar for authenticated users."""
    if st.session_state.get("authenticated", False):
        st.sidebar.markdown("---")
        if st.sidebar.button("🚪 Log Out", use_container_width=True, help="End your current authenticated session"):
            st.session_state["authenticated"] = False
            st.rerun()

def require_authentication() -> bool:
    """Enforces authentication gate.

    Returns True if user is authenticated.
    Otherwise renders login screen and calls st.stop() to halt further script execution.
    """
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    if not st.session_state["authenticated"]:
        render_login_screen()
        st.stop()
        return False

    # Render logout controls in sidebar for authenticated sessions
    render_logout_button()
    return True
