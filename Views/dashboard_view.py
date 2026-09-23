import streamlit as st
import pandas as pd
from core.pipeline import fetch_bootstrap_data, fetch_fixtures_data, fetch_manager_team
from core.engines import (
    build_player_dataframe, build_fixture_matrix, compute_weighted_fdr_score,
    compute_team_defensive_metrics, compute_roi_scores, find_upgrade_candidates, find_double_swap_combinations
)

def render_dashboard_view():
    user = st.session_state.user
    bootstrap_data = fetch_bootstrap_data()
    fixtures_data = fetch_fixtures_data()

    if not bootstrap_data:
        st.error("Connection failed to FPL Database API endpoints.")
        return

    current_gw = next((gw['id'] for gw in bootstrap_data['events'] if gw['is_current']), 1)
    df_players, teams_map, short_name_map, positions_map = build_player_dataframe(bootstrap_data)
    
    fixture_matrix_display, team_fixture_difficulties = build_fixture_matrix(fixtures_data, short_name_map, current_gw)
    weighted_fdr_by_team = compute_weighted_fdr_score(team_fixture_difficulties)
    defensive_concession = compute_team_defensive_metrics(fixtures_data, current_gw)
    df_players = compute_roi_scores(df_players, weighted_fdr_by_team)

    team_data = fetch_manager_team(user['manager_id'], current_gw)
    squad_ids = [pick['element'] for pick in team_data['picks']] if team_data else []

    # Premium Gated Banner Element
    if user['tier'] == 'Free':
        st.info("💡 **Upgrade to Pro:** Unlock advanced Buy/Sell Engines and Double-Swap combinatorial algorithmic solvers right now from the Billing hub.")

    # Executive Summary Metric Bar
    st.subheader("📊 Executive Overview")
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("Target Week", f"Gameweek {current_gw}")
    kpi2.metric("Manager ID Active", user['manager_id'])
    kpi3.metric("Bank Balance Saved", f"£{user['bank_balance']}m")
    kpi4.metric("License Tier", user['tier'].upper())

    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 Live Squad Layout", 
        "📈 Pro Quantitative Engines", 
        "🗓️ FDR Proximity Matrix", 
        "🔄 2-for-2 Advanced Solver"
    ])

    with tab1:
        st.subheader("Your Current Live Lineup")
        if team_data:
            my_squad = df_players[df_players['id'].isin(squad_ids)].copy()
            status_labels = {'i': 'Injured', 's': 'Suspended', 'd': 'Doubtful', 'a': 'Available'}
            my_squad['status_label'] = my_squad['status'].map(status_labels).fillna('Available')
            
            display_squad = my_squad[['web_name', 'position', 'team_name', 'now_cost', 'total_points', 'form', 'status_label', 'expected_roi_score']].copy()
            display_squad.columns = ['Player', 'Pos', 'Club', 'Cost', 'Pts', 'Form', 'Status', 'ROI Score']
            st.dataframe(display_squad.reset_index(drop=True), use_container_width=True, hide_index=True)

            st.markdown("---")
            st.subheader("🔁 1-for-1 Optimizer")
            player_label_map = {row['id']: f"{row['web_name']} ({row['position']}, £{row['now_cost']}m)" for _, row in my_squad.iterrows()}
            selected_drop_id = st.selectbox("Select player to drop:", options=list(player_label_map.keys()), format_func=lambda x: player_label_map[x])
            
            if selected_drop_id:
                dropped_row = my_squad[my_squad['id'] == selected_drop_id].iloc[0]
                candidates = find_upgrade_candidates(df_players, dropped_row['position'], dropped_row['now_cost'], squad_ids)
                st.dataframe(candidates[['web_name', 'team_short', 'now_cost', 'form', 'expected_roi_score']], use_container_width=True, hide_index=True)
        else:
            st.warning("Squad records empty. Update keys in Profile.")

    with tab2:
        if user['tier'] != 'Premium':
            st.error("🔒 **Premium Gated Feature:** The Unified ROI and xG/xA Delta Engine requires a Premium membership.")
        else:
            st.subheader("📈 Quantitative Buy / Sell Engine")
            col1, col2 = st.columns(2)
            with col1:
                st.success("🔥 Top BUY Targets (Highest ROI)")
                buy_targets = df_players[(df_players['status'] == 'a') & (df_players['minutes'] > 90)].sort_values(by='expected_roi_score', ascending=False).head(10)
                st.dataframe(buy_targets[['web_name', 'position', 'team_name', 'now_cost', 'form', 'expected_roi_score']], use_container_width=True, hide_index=True)
            with col2:
                st.error("⚠️ Top Regression Risks (High xG Overperformers)")
                sells = df_players[df_players['minutes'] >= 180].sort_values(by='xg_delta', ascending=True).head(10)
                st.dataframe(sells[['web_name', 'position', 'team_name', 'goals_scored', 'expected_goals']], use_container_width=True, hide_index=True)

    with tab3:
        st.subheader("🗓️ Advanced FDR Timeline Matrix")
        fdr_rows = [{'Team': teams_map.get(tid, '???'), 'Next Fixtures': d_str, 'Weighted FDR Score': round(weighted_fdr_by_team.get(tid, 50.0), 1)} for tid, d_str in fixture_matrix_display.items()]
        st.dataframe(pd.DataFrame(fdr_rows).sort_values(by='Weighted FDR Score', ascending=False), use_container_width=True, hide_index=True)

    with tab4:
        if user['tier'] != 'Premium':
            st.error("🔒 **Premium Gated Feature:** The Double Transfer Combinatorial Matrix Solver requires a Premium membership.")
        else:
            st.subheader("🔄 Double Transfer (2-for-2) Optimizer")
            if team_data:
                player_label_map_2 = {row['id']: f"{row['web_name']} ({row['position']}, £{row['now_cost']}m)" for _, row in df_players[df_players['id'].isin(squad_ids)].iterrows()}
                sell_ids = st.multiselect("Select exactly two players to drop:", options=list(player_label_map_2.keys()), format_func=lambda x: player_label_map_2[x], max_selections=2)
                
                if len(sell_ids) == 2:
                    sell_row_1 = df_players[df_players['id'] == sell_ids[0]].iloc[0]
                    sell_row_2 = df_players[df_players['id'] == sell_ids[1]].iloc[0]
                    combo_results = find_double_swap_combinations(df_players, sell_row_1, sell_row_2, user['bank_balance'], squad_ids)
                    st.dataframe(combo_results, use_container_width=True, hide_index=True)
