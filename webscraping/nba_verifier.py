from basketball_reference_web_scraper import client
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
    "Rebounds": "total_rebounds",
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
        games = client.player_box_scores(day=date_obj.day, month=date_obj.month, year=date_obj.year)
        game_logs_df = pd.DataFrame(games)

        # Calculate points and total rebounds
        game_logs_df['points'] = (
            game_logs_df.get('made_field_goals', 0) * 2 +
            game_logs_df.get('made_three_point_field_goals', 0) * 3 +
            game_logs_df.get('made_free_throws', 0) * 1
        )
        if 'offensive_rebounds' in game_logs_df.columns and 'defensive_rebounds' in game_logs_df.columns:
            game_logs_df['total_rebounds'] = game_logs_df['offensive_rebounds'] + game_logs_df['defensive_rebounds']
        else:
            game_logs_df['total_rebounds'] = game_logs_df.get('total_rebounds', 0)

        return game_logs_df
    except Exception as e:
        print(f"Error fetching game logs: {e}")
        return pd.DataFrame()

def calculate_double_double(player_stats):
    """
    Determine if a player achieved a double-double.

    Args:
        player_stats (dict): The player's stats.

    Returns:
        bool: True if the player achieved a double-double, False otherwise.
    """
    double_double_categories = ["points", "total_rebounds", "assists", "blocks", "steals"]
    qualifying_stats = sum(1 for stat in double_double_categories if player_stats.get(stat, 0) >= 10)
    return qualifying_stats >= 2

def extract_stat_name(market):
    """
    Extract the statistic type from the market column.

    Args:
        market (str): The market description (e.g., "Points Over 30.5").

    Returns:
        str or None: The key corresponding to the statistic in `stat_map` or None if not found.
    """
    for key in stat_map.keys():
        if key in market:
            return key
    return None

def check_bet_hit(row, player_stats):
    """
    Check if a bet hit and calculate the actual value.

    Args:
        row (pd.Series): Bet details.
        player_stats (dict): Player stats.

    Returns:
        Tuple[bool, float]: Whether the bet hit and the actual stat value.
    """
    market = row["Market"]
    stat_name = extract_stat_name(market)
    if not stat_name or stat_name not in stat_map:
        return False, 0  # Default for missing or unmatched stat

    try:
        threshold = float(market.split()[1])  # Extract threshold (e.g., 0.5, 1.5)
        over_under = market.split()[0]  # Extract "Over" or "Under"

        # Calculate the actual value
        if stat_name == "Double Double":
            actual_value = 1 if calculate_double_double(player_stats) else 0
        elif callable(stat_map[stat_name]):
            actual_value = stat_map[stat_name](player_stats)
        else:
            actual_value = player_stats.get(stat_map[stat_name], 0)

        actual_value = float(actual_value)  # Ensure numeric value

        # Determine if the bet hit
        bet_hit = (actual_value > threshold if over_under == "Over" else actual_value < threshold)
    except Exception as e:
        print(f"Error processing {row['Player Name']} for market {market}: {e}")
        return False, 0  # Default in case of errors

    return bet_hit, actual_value

def evaluate_bets(betting_data, game_logs_df):
    """
    Evaluate bets against fetched game logs.

    Args:
        betting_data (pd.DataFrame): The original betting data.
        game_logs_df (pd.DataFrame): DataFrame containing all game logs for the date.

    Returns:
        pd.DataFrame: Updated betting data with results.
    """
    results = []
    for _, row in betting_data.iterrows():
        player_stats = game_logs_df[game_logs_df["name"] == row["Player Name"]]
        if not player_stats.empty:
            player_stats = player_stats.iloc[0].to_dict()
            bet_hit, actual_value = check_bet_hit(row, player_stats)
        else:
            bet_hit, actual_value = None, None  # Indicate no data
        
        # Append results
        results.append((bet_hit, actual_value))

    # Add results to the DataFrame
    betting_data["Bet Hit"] = [result[0] for result in results]
    betting_data["Actual Value"] = [result[1] for result in results]

    # Drop columns that are entirely empty (all None or NaN)
    for column in ["Bet Hit", "Actual Value"]:
        if betting_data[column].isna().all():
            print(f"Removing empty column: {column}")
            betting_data.drop(columns=[column], inplace=True)

    return betting_data

def remove_empty_bet_hit_rows(dataframe):
    """
    Remove rows where the 'Bet Hit' column is empty (NaN or None).
    
    Args:
        dataframe (pd.DataFrame): The input DataFrame.

    Returns:
        pd.DataFrame: The cleaned DataFrame with non-empty 'Bet Hit' rows.
    """
    # Drop rows where 'Bet Hit' is NaN or None
    cleaned_dataframe = dataframe.dropna(subset=["Bet Hit"])
    return cleaned_dataframe

def process_betting_csv(file_path, date):
    """
    Process the betting CSV file and evaluate bets.

    Args:
        file_path (str): Path to the betting CSV file.
        date (str): The game date in "MM_DD_YYYY" format.

    Returns:
        pd.DataFrame: Updated betting data.
    """
    if not os.path.exists(file_path):
        print(f"No betting data file found for {date}. Exiting.")
        return None

    betting_data = pd.read_csv(file_path)
    game_logs_df = fetch_game_logs_for_date(date)

    if game_logs_df.empty:
        print("No game logs fetched. Exiting.")
        return None

    updated_data = evaluate_bets(betting_data, game_logs_df)

    # Remove rows with empty 'Bet Hit' values
    updated_data = remove_empty_bet_hit_rows(updated_data)

    # Save the cleaned and updated data
    updated_data.to_csv(file_path, index=False)
    return updated_data


if __name__ == "__main__":
    yesterday = datetime.now() - timedelta(days=1)
    input_date = yesterday.strftime("%m_%d_%Y")
    input_file = f'../nba_saved_csv/nba_betting_data_{input_date}.csv'

    updated_betting_data = process_betting_csv(input_file, input_date)
    if updated_betting_data is not None:
        print(f"Updated data saved to: {input_file}")
