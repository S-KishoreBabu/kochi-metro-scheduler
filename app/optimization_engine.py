# In app/optimization_engine.py
import pandas as pd
from datetime import timedelta

# --- THIS IS THE MISSING FUNCTION ---
def hard_constraint_filter(daily_status_df):
    """
    Filters trains based on hard constraints from the actual database columns.
    """
    # A train is eligible if it IS certified and DOES NOT have an open job card and IS clean.
    eligible_trains = daily_status_df[
        (daily_status_df['is_certified'] == True) &
        (daily_status_df['has_open_job_card'] == False) &
        (daily_status_df['is_clean'] == True)
    ]
    return eligible_trains['train_id'].tolist()


# In app/optimization_engine.py

def calculate_brand_score(contracts_df, daily_status_df, target_date):
    """
    Calculates a brand urgency score (0-100) based on specific contract types.
    """
    df = pd.merge(contracts_df, daily_status_df[['train_id', 'hours_accomplished_total']], on='train_id', how='left')
    
    # --- FIX: Do not fill missing hours yet ---
    # df['hours_accomplished_total'].fillna(0, inplace=True)

    df['contract_end_date'] = pd.to_datetime(df['contract_end_date'])
    target_datetime = pd.to_datetime(target_date)
    df['days_remaining'] = (df['contract_end_date'] - target_datetime).dt.days
    df['hours_remaining'] = df['total_hours_required'] - df['hours_accomplished_total']
    
    df['brand_score'] = 0.0

    # Rule 1: MINIMUM_DAILY and TIME_SPECIFIC are always 100% if active
    mask_must_run_types = df['branding_type'].isin(['MINIMUM_DAILY', 'TIME_SPECIFIC']) & (df['hours_remaining'] > 0)
    df.loc[mask_must_run_types, 'brand_score'] = 100.0

    # Rule 2: Handle CUMULATIVE contracts
    mask_cumulative = (df['branding_type'] == 'CUMULATIVE') & (df['hours_remaining'] > 0)
    
    df['urgency'] = 0.0
    days_mask = (df['days_remaining'] > 0) & mask_cumulative
    df.loc[days_mask, 'urgency'] = df['hours_remaining'] / df['days_remaining']

    mask_urgent_cumulative = mask_cumulative & ((df['days_remaining'] <= 0) | (df['urgency'] > 5))
    df.loc[mask_urgent_cumulative, 'brand_score'] = 100.0

    mask_variable_cumulative = mask_cumulative & (df['brand_score'] == 0.0)
    
    if not df.loc[mask_variable_cumulative].empty:
        df.loc[mask_variable_cumulative, 'brand_score'] = (df['urgency'] / 5.0) * 99
        df.loc[df['brand_score'] > 99, 'brand_score'] = 100

    return df[['train_id', 'brand_score']]


def score_and_rank_trains(eligible_trains_df, contracts_df, daily_status_df, target_date):
    """
    Scores and ranks eligible trains based on branding, mileage, and shunting cost.
    """
    if eligible_trains_df.empty:
        return pd.DataFrame()

    # --- FIX: Pass the complete daily_status_df, not a copy ---
    contracts_with_scores = calculate_brand_score(contracts_df, daily_status_df, target_date)
    
    df = pd.merge(eligible_trains_df, contracts_with_scores, on='train_id', how='left')
    
    # --- FIX: Fill missing brand_scores here, at the end ---
    df['brand_score'].fillna(0, inplace=True)

    df['brand_score_normalized'] = df['brand_score'] / 100.0

    max_mileage = df['mileage'].max()
    min_mileage = df['mileage'].min()
    if max_mileage == min_mileage:
        df['mileage_score'] = 1.0
    else:
        df['mileage_score'] = 1 - ((df['mileage'] - min_mileage) / (max_mileage - min_mileage))

    max_shunting = df['shunting_cost'].max()
    min_shunting = df['shunting_cost'].min()
    if max_shunting == min_shunting:
        df['shunting_score'] = 1.0
    else:
        df['shunting_score'] = 1 - ((df['shunting_cost'] - min_shunting) / (max_shunting - min_shunting))

    weights = {'brand': 0.5, 'mileage': 0.3, 'shunting': 0.2}
    df['suitability_score'] = (
        df['brand_score_normalized'] * weights['brand'] +
        df['mileage_score'] * weights['mileage'] +
        df['shunting_score'] * weights['shunting']
    )

    df['rank'] = df['suitability_score'].rank(method='dense', ascending=False).astype(int)
    final_df = df.sort_values(by='rank')
    
    return final_df[['train_id', 'rank', 'brand_score', 'mileage_score', 'shunting_score', 'suitability_score']]

def generate_explanation(row, weights):
    """Generates a human-readable explanation for a train's score."""
    # Note: explanation logic uses normalized scores (0-1)
    brand_contr = (row['brand_score'] / 100.0) * weights['brand']
    mileage_contr = row['mileage_score'] * weights['mileage']
    shunting_contr = row['shunting_score'] * weights['shunting']
    
    contributions = {
        'mandatory branding requirement': brand_contr,
        'low mileage': mileage_contr,
        'favorable depot position': shunting_contr
    }
    
    sorted_factors = sorted(contributions.items(), key=lambda item: item[1], reverse=True)
    
    primary_reason = sorted_factors[0][0]
    secondary_reason = sorted_factors[1][0]
    
    return f"Ranked highly due to its {primary_reason} and {secondary_reason}."