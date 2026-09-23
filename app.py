import streamlit as st
from core.auth import init_db
from views.login_view import render_login_view
from views.dashboard_view import render_dashboard_view
from views.profile_view import render_profile_view
from views.billing_view import render_billing_view

# Configure browser tab layouts
st.set_page_config(page_title="FPL Analytics SaaS Engine", layout="wide", page_icon="⚽")

# Core state and schema bootstrap initialization logic
init_db()

if "user" not in st.session_state:
    st.session_state.user = None

# Security Routing Mechanism
if st.session_state.user is None:
    render_login_view()
else:
    # Build professional navigation panel inside Sidebar wrapper space
    st.sidebar.title(f"Welcome, {st.session_state.user['username']}")
    st.sidebar.markdown(f"**Tier status:** `{st.session_state.user['tier'].upper()}`")
    
    workspace = st.sidebar.radio(
        "Navigation Hub",
        ["📈 Analytics Dashboard", "👤 Account Profile Settings", "💳 Commercial Billing Centre"]
    )
    
    st.sidebar.markdown("---")
    if st.sidebar.button("Secure Session Exit", type="secondary"):
        st.session_state.user = None
        st.rerun()
        
    # Active Workspace Routing Hub
    if workspace == "📈 Analytics Dashboard":
        render_dashboard_view()
    elif workspace == "👤 Account Profile Settings":
        render_profile_view()
    elif workspace == "💳 Commercial Billing Centre":
        render_billing_view()
