from basketball_reference_web_scraper import client
from basketball_reference_web_scraper.data import OutputType
import pandas as pd
import os
from datetime import datetime, timedelta

# Extended mapping to include all bet types
stat_map = {
    "3PTM": "made_three_point_field_goals",
    "Double Double": None,  # Calculated dynamically
    "STL+BLK": lambda row: row.get("steals", 0) + row.get("blocks", 0),
    "Blocks": "blocks",
    "Assists": "assists",
    "Turnovers": "turnovers",
    "Rebounds": "total_rebounds",  # Add total_rebounds to stat_map
    "Steals": "steals",
    "REB+AST": lambda row: row.get("total_rebounds", 0) + row.get("assists", 0),
    "P+A+R": lambda row: row.get("points", 0) + row.get("assists", 0) + row.get("total_rebounds", 0),
    "PTS+AST": lambda row: row.get("points", 0) + row.get("assists", 0),
    "PTS+REB": lambda row: row.get("points", 0) + row.get("total_rebounds", 0),
    "Points": "points",
}

def fetch_game_logs_for_date(date):
    """
    Fetch all game logs for a specific date.

    Args:
        date (str): The game date in "MM_DD_YYYY" format.

    Returns:
        pd.DataFrame: DataFrame containing all game logs for the date.
    """
    date_obj = pd.to_datetime(date, format="%m_%d_%Y")
    try:
        # Fetch all games for the date
        games = client.player_box_scores(
            day=date_obj.day, month=date_obj.month, year=date_obj.year
        )
        
        # Convert to DataFrame for easier handling
        game_logs_df = pd.DataFrame(games)
        
        # Calculate points and add to player data
        game_logs_df['points'] = (
            game_logs_df.get('made_field_goals', 0) * 2 +
            game_logs_df.get('made_three_point_field_goals', 0) * 3 +
            game_logs_df.get('made_free_throws', 0) * 1
        )
        
        # Ensure total_rebounds is available (it might be named differently, e.g., 'offensive_rebounds' + 'defensive_rebounds')
        game_logs_df['total_rebounds'] = game_logs_df.get('total_rebounds', 0)
        if 'offensive_rebounds' in game_logs_df.columns and 'defensive_rebounds' in game_logs_df.columns:
            game_logs_df['total_rebounds'] = game_logs_df['offensive_rebounds'] + game_logs_df['defensive_rebounds']
        
        pd.set_option('display.max_columns', None)  # Shows all columns
        pd.set_option('display.width', None)  # Allows wide output without wrapping

        return game_logs_df
    except Exception as e:
        print(f"Error fetching game logs: {e}")
        return pd.DataFrame()

def process_betting_csv(file_path, date):
    """
    Process the betting CSV file and evaluate bets.

    Args:
        file_path (str): Path to the betting CSV file.
        date (str): The game date in "MM_DD_YYYY" format.

    Returns:
        pd.DataFrame: Updated betting data.
        str: Path to the updated CSV file.
    """
    # Check if the file exists
    if not os.path.exists(file_path):
        print(f"No betting data file found for {date}. Exiting.")
        return None, None

    betting_data = pd.read_csv(file_path)
    game_logs_df = fetch_game_logs_for_date(date)

    if game_logs_df.empty:
        print("No game logs fetched. Exiting.")
        return None, None

    updated_data = evaluate_bets(betting_data, game_logs_df)

    updated_data.to_csv(file_path, index=False)
    return updated_data

if __name__ == "__main__":  
    # Load bets CSV
    # Automatically set the date to yesterday
    yesterday = datetime.now() - timedelta(days=1)
    input_date = yesterday.strftime("%m_%d_%Y")
    input_file = f'../nba_saved_csv/nba_betting_data_{input_date}.csv'

    updated_betting_data = process_betting_csv(input_file, input_date)
    if updated_betting_data is not None:
        print(f"Updated data saved to: {input_file}")
