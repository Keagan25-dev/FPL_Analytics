import streamlit as st
from core.auth import register_user, authenticate_user

def render_login_view():
    st.title("⚽ Premium FPL Analytics Portal")
    
    auth_action = st.radio("Access Portal Mode", ["Sign In", "Create Premium Account"], horizontal=True)
    
    username = st.text_input("Username / Email Address")
    password = st.text_input("Security Password", type="password")
    
    if auth_action == "Sign In":
        if st.button("Unlock Dashboard", type="primary"):
            user_session = authenticate_user(username, password)
            if user_session:
                st.session_state.user = user_session
                st.success("Identity verified successfully! Routing to workbench...")
                st.rerun()
            else:
                st.error("Invalid credentials provided.")
    else:
        st.caption("New registrations instantly grant standard Free-tier dashboard tokens.")
        if st.button("Register Identity"):
            if username and password:
                if register_user(username, password):
                    st.success("Account constructed successfully! Select 'Sign In' to enter.")
                else:
                    st.error("Username is already allocated inside registry system.")
            else:
                st.error("Fields cannot evaluate empty.")
