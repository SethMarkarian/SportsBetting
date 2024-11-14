import pandas as pd
from datetime import datetime
from nba_api.stats.endpoints import boxscoretraditionalv2, scoreboardv2
import os

def get_game_id_for_date(opponent_team, date):
    """Retrieves the game ID for a specified date and opponent team using nba_api."""
    scoreboard = scoreboardv2.ScoreboardV2(game_date=date, timeout=60)
    games = scoreboard.game_header.get_data_frame()

    for _, game in games.iterrows():
        if opponent_team in (game['HOME_TEAM_ID'], game['VISITOR_TEAM_ID']):
            return game['GAME_ID']
    return None

def parse_bet_condition(bet_condition):
    """Parses a bet condition to determine stat type, limit, and comparison (Over/Under)."""
    components = bet_condition.split()
    stat_type = components[-2]  # e.g., 'Rebounds', 'Points', 'Assists'
    comparison = components[0]  # 'Over' or 'Under'
    limit = float(components[1])  # e.g., '0.5'
    
    # Determine the specific period if present (e.g., '1Q', 'Full Game')
    period = 'Full Game'
    if '1Q' in bet_condition:
        period = '1Q'
    elif '2Q' in bet_condition:
        period = '2Q'
    elif '3Q' in bet_condition:
        period = '3Q'
    elif '4Q' in bet_condition:
        period = '4Q'
    
    return stat_type, comparison, limit, period

def get_player_stats(game_id, player_name, bet_condition):
    """Retrieves a player's stats for a given game and verifies if the bet condition was met."""
    boxscore = boxscoretraditionalv2.BoxScoreTraditionalV2(game_id=game_id)
    player_stats = boxscore.player_stats.get_data_frame()
    
    player_row = player_stats[player_stats['PLAYER_NAME'].str.contains(player_name, case=False)]
    if not player_row.empty:
        player_data = player_row.iloc[0]  # Get the first matching row
        
        # Parse the bet condition to determine what to check
        stat_type, comparison, limit, period = parse_bet_condition(bet_condition)
        
        # Map stat types to columns in the DataFrame
        stat_mapping = {
            'Points': 'PTS',
            'Rebounds': 'REB',
            'Assists': 'AST',
            'Steals': 'STL',
            'Blocks': 'BLK',
            'Turnovers': 'TO'
        }
        
        # Extract the relevant stat
        if stat_type in stat_mapping:
            stat_value = player_data[stat_mapping[stat_type]]
            
            # Perform comparison for full game stats (modify if quarter data is available)
            if period == 'Full Game':  
                if comparison == 'Under':
                    return stat_value < limit
                elif comparison == 'Over':
                    return stat_value > limit
    
    return None

# User input date (in format MM_DD_YYYY)
input_date = input("Enter the date (MM_DD_YYYY): ")

# Format the date to YYYY-MM-DD for NBA API
formatted_date = datetime.strptime(input_date, '%m_%d_%Y').strftime('%Y-%m-%d')

# Load the specific CSV file for the given date
csv_file_path = f'../nba_saved_csv/nba_betting_data_{input_date}.csv'
if not os.path.exists(csv_file_path):
    print(f"CSV file for the date {input_date} does not exist.")
    exit()

betting_data = pd.read_csv(csv_file_path)

# Add a column for bet result
betting_data['Bet Hit'] = False

# Process each bet in the DataFrame
for index, row in betting_data.iterrows():
    player_name = row['Player Name']
    opponent_team = row['Matchup'].split(' ')[1]
    bet_condition = row['Market']
    
    # Get game ID for the specific date and opponent
    game_id = get_game_id_for_date(opponent_team, formatted_date)
    if game_id:
        result = get_player_stats(game_id, player_name, bet_condition)
        if result is not None:
            betting_data.at[index, 'Bet Hit'] = result

# Save the updated DataFrame to a new CSV file
output_path = f'../nba_saved_csv/nba_betting_data_verified_{input_date}.csv'
betting_data.to_csv(output_path, index=False)
print(f"Updated CSV saved to {output_path}")
