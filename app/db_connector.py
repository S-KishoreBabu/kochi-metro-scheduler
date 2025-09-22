# In app/db_connector.py
import psycopg2
import pandas as pd
from datetime import date

# --- NEW: Reusable connection function ---
def connect_to_db():
    """Connects to the PostgreSQL database and returns the connection object."""
    conn = None
    try:
        conn = psycopg2.connect(
            host="localhost",
            database="kochi_metro_db",
            user="postgres",
            password="Kathmandu*30"
        )
        print("✅ Database connection successful!")
        return conn
    except (Exception, psycopg2.Error) as error:
        print(f"❌ Error while connecting to PostgreSQL: {error}")
        return None

def fetch_daily_data(target_date):
    """Fetches all necessary data for a given date."""
    # MODIFIED: Call the reusable function
    conn = connect_to_db()
    if not conn:
        return None, None
    try:
        contracts_query = "SELECT * FROM BrandingContracts;"
        status_query = "SELECT * FROM DailyFleetStatus WHERE status_date = %s;"

        print("\nFetching branding contracts...")
        contracts_df = pd.read_sql_query(contracts_query, conn)
        
        print(f"\nFetching fleet status for {target_date.strftime('%Y-%m-%d')}...")
        status_df = pd.read_sql_query(status_query, conn, params=(target_date,))

        return contracts_df, status_df
    except (Exception, psycopg2.Error) as error:
        print(f"Error during data fetch: {error}")
        return None, None
    finally:
        if conn:
            conn.close()
            print("\nPostgreSQL connection is closed.")

def fetch_depot_layout():
    """Fetches the current train layout from the depot."""
    # MODIFIED: Call the reusable function
    conn = connect_to_db()
    if not conn:
        return None
    try:
        print("Fetching depot layout...")
        query = "SELECT bay_number, position_in_bay, train_id FROM DepotLayout ORDER BY bay_number, position_in_bay;"
        depot_df = pd.read_sql_query(query, conn)
        return depot_df
    except (Exception, psycopg2.Error) as error:
        print(f"Error fetching depot layout: {error}")
        return None
    finally:
        if conn:
            conn.close()
            print("PostgreSQL connection for depot layout is closed.")


def save_schedule_recommendation(schedule_df, target_date):
    """Saves the ranked schedule to the history table."""
    conn = connect_to_db()
    if not conn:
        return
    try:
        cursor = conn.cursor()
        # Clear old records for the target date to prevent duplicates
        cursor.execute("DELETE FROM DailyScheduleRecommendation WHERE recommendation_date = %s;", (target_date,))
        
        # Save each ranked train
        for _, row in schedule_df.iterrows():
            if row['rank'] != '-': # Only save eligible, ranked trains
                cursor.execute(
                    """
                    INSERT INTO DailyScheduleRecommendation 
                    (recommendation_date, train_id, recommended_rank, suitability_score)
                    VALUES (%s, %s, %s, %s);
                    """,
                    (target_date, row['train_id'], row['rank'], row['suitability_score'])
                )
        conn.commit()
        print(f"✅ Successfully saved schedule for {target_date} to history.")
    except (Exception, psycopg2.Error) as error:
        print(f"❌ Error saving schedule to history: {error}")
    finally:
        if conn:
            conn.close()

def fetch_history_by_date(history_date):
    """Fetches the saved schedule recommendation for a specific date."""
    conn = connect_to_db()
    if not conn:
        return None
    try:
        query = """
            SELECT * FROM DailyScheduleRecommendation 
            WHERE recommendation_date = %s 
            ORDER BY recommended_rank;
        """
        history_df = pd.read_sql_query(query, conn, params=(history_date,))
        return history_df
    except (Exception, psycopg2.Error) as error:
        print(f"Error fetching history: {error}")
        return None
    finally:
        if conn:
            conn.close()