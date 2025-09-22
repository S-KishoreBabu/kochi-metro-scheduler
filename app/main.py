from flask import Flask, jsonify, render_template , request# <-- Add render_template
from datetime import date,datetime
from db_connector import (
    fetch_daily_data, 
    fetch_depot_layout, 
    save_schedule_recommendation, 
    fetch_history_by_date
)
from optimization_engine import hard_constraint_filter, score_and_rank_trains, generate_explanation, calculate_brand_score
import pandas as pd

# Initialize the Flask application
app = Flask(__name__)

@app.route('/')
def dashboard():
    """
    Renders the main dashboard page.
    """

    return render_template('index.html')


# In app/main.py

@app.route('/api/get_schedule', methods=['GET'])
def get_schedule():
    """
    API endpoint to get the daily train schedule recommendation for ALL trains.
    """
    try:
        target_date = date(2025, 9, 20)
        contracts, daily_status = fetch_daily_data(target_date)

        if daily_status is None or daily_status.empty:
            return jsonify({"error": f"No fleet status data found for {target_date}."}), 404

        # --- Logic ---
        eligible_ids = hard_constraint_filter(daily_status)
        daily_status['is_eligible'] = daily_status['train_id'].isin(eligible_ids)
        eligible_trains_df = daily_status[daily_status['is_eligible'] == True]
        
        final_ranking = score_and_rank_trains(eligible_trains_df, contracts, daily_status, target_date)
        
        if not final_ranking.empty:
            weights = {'brand': 0.5, 'mileage': 0.3, 'shunting': 0.2}
            final_ranking['explanation'] = final_ranking.apply(lambda row: generate_explanation(row, weights), axis=1)

        # Merge and prepare final data
        full_details = pd.merge(daily_status, contracts, on='train_id')
        schedule_data_df = pd.merge(full_details, final_ranking, on='train_id', how='left')

        # Sort the DataFrame by the 'rank' column
        schedule_data_df['rank_sort'] = pd.to_numeric(schedule_data_df['rank'], errors='coerce').fillna(999)
        schedule_data_df.sort_values('rank_sort', inplace=True)
        schedule_data_df.drop(columns='rank_sort', inplace=True)

        # FINAL STEP: Replace all remaining NaNs with JSON-safe values
        fill_values = {
            'rank': '-', 'suitability_score': -1, 'brand_score': -1,
            'mileage_score': -1, 'shunting_score': -1,
            'explanation': 'Train is ineligible for service today.'
        }
        schedule_data_df.fillna(value=fill_values, inplace=True)
        save_schedule_recommendation(schedule_data_df, target_date)
        schedule_data = schedule_data_df.to_dict('records')
        return jsonify(schedule_data)

    except Exception as e:
        print(f"An error occurred in get_schedule endpoint: {e}")
        return jsonify({"error": "An internal server error occurred."}), 500
    
@app.route('/api/get_history', methods=['GET'])
def get_history():
    """API endpoint to get saved schedule history for a specific date."""
    # Get the date from the query parameter (e.g., ?date=2025-09-20)
    date_str = request.args.get('date')
    if not date_str:
        return jsonify({"error": "A 'date' parameter is required."}), 400
    
    try:
        history_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        history_df = fetch_history_by_date(history_date)
        
        if history_df is None or history_df.empty:
            return jsonify({"message": f"No history found for {date_str}."}), 404
            
        return jsonify(history_df.to_dict('records'))

    except ValueError:
        return jsonify({"error": "Invalid date format. Please use YYYY-MM-DD."}), 400
    except Exception as e:
        print(f"An error occurred in get_history endpoint: {e}")
        return jsonify({"error": "An internal server error occurred."}), 500


@app.route('/api/get_depot_layout', methods=['GET'])
def get_depot_layout():
    try:
        # Use a date for which you have data
        target_date = date(2025, 9, 20) 
        contracts, daily_status = fetch_daily_data(target_date)
        depot_layout_df = fetch_depot_layout()

        # --- THIS IS THE FIX: Check if the dataframe is empty ---
        if daily_status is None or daily_status.empty or depot_layout_df is None:
            return jsonify({"error": f"No data found for {target_date}."}), 404
        
        # --- The rest of the logic remains the same ---
        eligible_ids = hard_constraint_filter(daily_status)
        daily_status['is_eligible'] = daily_status['train_id'].isin(eligible_ids)

        contracts_with_scores = calculate_brand_score(contracts.copy(), daily_status.copy(), target_date)
        
        daily_status = pd.merge(daily_status, contracts_with_scores, on='train_id', how='left')
        daily_status['brand_score'].fillna(0, inplace=True)
        merged_df = pd.merge(depot_layout_df, daily_status, on='train_id')
        
        layout_data = merged_df.to_dict('records')
        return jsonify(layout_data)
        
    except Exception as e:
        print(f"An error occurred in depot layout endpoint: {e}")
        return jsonify({"error": "An internal server error occurred."}), 500
    

if __name__ == '__main__':
    # Running on 0.0.0.0 makes the server accessible from your network
    # Debug=True will auto-reload the server when you make changes
    app.run(host='0.0.0.0', port=5000, debug=True)