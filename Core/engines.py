import pandas as pd
from itertools import combinations

DOUBLE_SWAP_POOL_CAP = 40
FDR_LOOKAHEAD = 5
FDR_DECAY_WEIGHTS = [1.0, 0.8, 0.6, 0.4, 0.2]
DEFENSIVE_WINDOW = 4

ROI_WEIGHT_FORM = 0.50
ROI_WEIGHT_XSTATS = 0.30
ROI_WEIGHT_FDR = 0.20

def build_player_dataframe(data):
    teams_map = {t['id']: t['name'] for t in data['teams']}
    short_name_map = {t['id']: t['short_name'] for t in data['teams']}
    positions_map = {p['id']: p['singular_name_short'] for p in data['element_types']}

    df = pd.DataFrame(data['elements'])
    df['team_name'] = df['team'].map(teams_map)
    df['team_short'] = df['team'].map(short_name_map)
    df['position'] = df['element_type'].map(positions_map)
    df['now_cost'] = pd.to_numeric(df['now_cost'], errors='coerce') / 10

    numeric_cols = ['form', 'points_per_game', 'total_points', 'expected_goals', 'expected_assists', 'goals_scored', 'assists', 'minutes']
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    df['xg_delta'] = df['expected_goals'] - df['goals_scored']
    df['xa_delta'] = df['expected_assists'] - df['assists']
    return df, teams_map, short_name_map, positions_map

def build_fixture_matrix(fixtures_data, short_name_map, current_gw):
    upcoming = [f for f in fixtures_data if f.get('event') is not None and f['event'] >= current_gw and not f.get('finished', False)]
    upcoming.sort(key=lambda f: (f['event'], f.get('kickoff_time') or ""))

    team_fixtures = {tid: [] for tid in short_name_map.keys()}
    for fx in upcoming:
        home_id, away_id = fx['team_h'], fx['team_a']
        if home_id in team_fixtures and len(team_fixtures[home_id]) < FDR_LOOKAHEAD:
            team_fixtures[home_id].append({'opponent': short_name_map.get(away_id, '???'), 'venue': 'H', 'difficulty': fx.get('team_h_difficulty', 3)})
        if away_id in team_fixtures and len(team_fixtures[away_id]) < FDR_LOOKAHEAD:
            team_fixtures[away_id].append({'opponent': short_name_map.get(home_id, '???'), 'venue': 'A', 'difficulty': fx.get('team_a_difficulty', 3)})

    matrix_display, team_fixture_difficulties = {}, {}
    for tid, fixtures_list in team_fixtures.items():
        parts = [f"{f['opponent']} ({f['venue']}){f['difficulty']}" for f in fixtures_list]
        matrix_display[tid] = " | ".join(parts) if parts else "No fixtures scheduled"
        team_fixture_difficulties[tid] = [f['difficulty'] for f in fixtures_list]
    return matrix_display, team_fixture_difficulties

def compute_weighted_fdr_score(team_fixture_difficulties):
    scores = {}
    for tid, difficulties in team_fixture_difficulties.items():
        if not difficulties:
            scores[tid] = 50.0
            continue
        weights = FDR_DECAY_WEIGHTS[:len(difficulties)]
        weighted_sum = sum(d * w for d, w in zip(difficulties, weights))
        weight_total = sum(weights)
        weighted_avg_difficulty = weighted_sum / weight_total if weight_total > 0 else 3.0
        scores[tid] = max(0.0, min(100.0, (5.0 - weighted_avg_difficulty) / 4.0 * 100.0))
    return scores

def compute_team_defensive_metrics(fixtures_data, current_gw):
    lower_bound = max(1, current_gw - DEFENSIVE_WINDOW)
    completed = [f for f in fixtures_data if f.get('finished') and f.get('event') is not None and lower_bound <= f['event'] < current_gw]

    conceded_totals, matches_counted = {}, {}
    for fx in completed:
        h_id, a_id = fx['team_h'], fx['team_a']
        h_score = fx.get('team_h_score', 0) or 0
        a_score = fx.get('team_a_score', 0) or 0
        conceded_totals[h_id] = conceded_totals.get(h_id, 0) + a_score
        matches_counted[h_id] = matches_counted.get(h_id, 0) + 1
        conceded_totals[a_id] = conceded_totals.get(a_id, 0) + h_score
        matches_counted[a_id] = matches_counted.get(a_id, 0) + 1
    return {tid: conceded_totals[tid] / matches_counted[tid] for tid in conceded_totals if matches_counted[tid]}

def _min_max_normalize(series):
    if series.max() - series.min() == 0:
        return pd.Series(0.5, index=series.index)
    return (series - series.min()) / (series.max() - series.min())

def compute_roi_scores(df, weighted_fdr_by_team):
    df = df.copy()
    df['fdr_goodness'] = df['team'].map(weighted_fdr_by_team).fillna(50.0)
    form_ppg_component = (_min_max_normalize(df['form']) * 0.5 + _min_max_normalize(df['points_per_game']) * 0.5)
    xstats_component = (_min_max_normalize(df['xg_delta']) * 0.5 + _min_max_normalize(df['xa_delta']) * 0.5)
    df['expected_roi_score'] = (form_ppg_component * ROI_WEIGHT_FORM + xstats_component * ROI_WEIGHT_XSTATS + (df['fdr_goodness'] / 100.0) * ROI_WEIGHT_FDR) * 100.0
    return df

def find_upgrade_candidates(df, dropped_position, dropped_cost, squad_ids, top_n=5):
    return df[(df['position'] == dropped_position) & (df['now_cost'] <= dropped_cost) & (df['status'] == 'a') & (~df['id'].isin(squad_ids))].sort_values(by='expected_roi_score', ascending=False).head(top_n)

def find_double_swap_combinations(df, sell_player_1, sell_player_2, bank_balance, squad_ids, top_n=5):
    pos1, pos2 = sell_player_1['position'], sell_player_2['position']
    total_budget = sell_player_1['now_cost'] + sell_player_2['now_cost'] + bank_balance
    excluded_ids = set(squad_ids)

    pool1 = df[(df['position'] == pos1) & (df['status'] == 'a') & (~df['id'].isin(excluded_ids))].sort_values(by='expected_roi_score', ascending=False).head(DOUBLE_SWAP_POOL_CAP)
    pool2 = df[(df['position'] == pos2) & (df['status'] == 'a') & (~df['id'].isin(excluded_ids))].sort_values(by='expected_roi_score', ascending=False).head(DOUBLE_SWAP_POOL_CAP)

    results = []
    if pos1 == pos2:
        for (_, row_a), (_, row_b) in combinations(pool1.iterrows(), 2):
            if row_a['now_cost'] + row_b['now_cost'] <= total_budget:
                results.append({'player_in_1': row_a['web_name'], 'cost_1': row_a['now_cost'], 'player_in_2': row_b['web_name'], 'cost_2': row_b['now_cost'], 'combined_cost': row_a['now_cost'] + row_b['now_cost'], 'combined_roi': row_a['expected_roi_score'] + row_b['expected_roi_score']})
    else:
        for _, row_a in pool1.iterrows():
            for _, row_b in pool2.iterrows():
                if row_a['now_cost'] + row_b['now_cost'] <= total_budget:
                    results.append({'player_in_1': row_a['web_name'], 'cost_1': row_a['now_cost'], 'player_in_2': row_b['web_name'], 'cost_2': row_b['now_cost'], 'combined_cost': row_a['now_cost'] + row_b['now_cost'], 'combined_roi': row_a['expected_roi_score'] + row_b['expected_roi_score']})
    
    return pd.DataFrame(results).sort_values(by='combined_roi', ascending=False).head(top_n).reset_index(drop=True)
