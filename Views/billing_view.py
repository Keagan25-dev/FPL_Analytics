import streamlit as st
from core.auth import update_user_tier

def render_billing_view():
    st.title("💳 Subscriptions & Commercial Billing")
    user = st.session_state.user
    
    st.metric(label="Your Active License Tier", value=f"👑 {user['tier'].upper()} MEMBER")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Free Basic Account")
        st.markdown("- Squad Viewer View\n- Proximity FDR Timelines\n- Limited 1-for-1 transfers")
        if user['tier'] == 'Free':
            st.button("Active Tier", disabled=True, key="free_active")
        else:
            if st.button("Downgrade to Free", key="demote"):
                update_user_tier(user['username'], 'Free')
                st.session_state.user['tier'] = 'Free'
                st.rerun()
                
    with col2:
        st.subheader("🔥 Premium Pro Analytics")
        st.markdown("- Complete Buy / Sell Signal Engines\n- Dynamic xG/xA Performance Deltas\n- High-Performance Double-Swap Optimization Matrix Engine")
        if user['tier'] == 'Premium':
            st.button("Active Pro Tier", disabled=True, key="premium_active")
        else:
            if st.button("Simulate Checkout (£4.99/mo)", type="primary", key="upgrade"):
                update_user_tier(user['username'], 'Premium')
                st.session_state.user['tier'] = 'Premium'
                st.success("Payment Authorized! Account upgraded to Premium Pro.")
                st.rerun()
