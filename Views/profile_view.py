import streamlit as st
from core.auth import update_user_profile

def render_profile_view():
    st.title("👤 User Profile & FPL Settings")
    st.markdown("Configure your account metrics. Changes made here persist globally across all optimization views.")
    
    user = st.session_state.user
    
    with st.form("profile_form"):
        st.subheader("FPL Integration Keys")
        manager_id = st.number_input("Official FPL Manager ID", min_value=1, value=user['manager_id'])
        league_id = st.number_input("Target Classic League ID", min_value=1, value=user['league_id'])
        bank_balance = st.number_input("In-Game Bank Balance (£m)", min_value=0.0, value=user['bank_balance'], step=0.1)
        
        if st.form_submit_button("Save Changes & Sync"):
            update_user_profile(user['username'], manager_id, league_id, bank_balance)
            st.session_state.user['manager_id'] = manager_id
            st.session_state.user['league_id'] = league_id
            st.session_state.user['bank_balance'] = bank_balance
            st.success("Configuration successfully updated in database record!")
