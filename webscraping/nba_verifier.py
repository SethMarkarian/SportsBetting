import pandas as pd
import requests
from datetime import datetime
from nba_api.stats.endpoints import ScoreboardV2, BoxScoreTraditionalV2
import time

def get_games_and_players_data(date: str):
    # Convert date from MM_DD_YYYY format to required YYYY-MM-DD
    date_obj = datetime.strptime(date, "%m_%d_%Y")
    date_str = date_obj.strftime("%Y-%m-%d")
    
    # Get games for the specified date
    scoreboard = ScoreboardV2(game_date=date_str)
    games = scoreboard.get_data_frames()[0]  # Dataframe containing game details
    
    # Prepare an empty list to collect player stats data
    all_player_stats = []
    
    # Loop through each game to get player stats
    for game_id in games['GAME_ID']:
        # Retrieve player stats for the game
        box_score = BoxScoreTraditionalV2(game_id=game_id)
        player_stats = box_score.get_data_frames()[0]  # Dataframe containing player stats
        
        # Append to the list of all player stats
        all_player_stats.append(player_stats)
        
        # Rate limit handling (avoid hitting API limits)
        time.sleep(1)  # You may adjust the sleep duration if needed

    # Concatenate all player stats into a single dataframe
    all_player_stats_df = pd.concat(all_player_stats, ignore_index=True)
    
    # Optional: Add game details to player stats for additional context
    all_player_stats_df = all_player_stats_df.merge(games[['GAME_ID', 'HOME_TEAM_ID', 'VISITOR_TEAM_ID']],
                                                    on='GAME_ID', how='left')
    
    return games, all_player_stats_df

def evaluate_over_under(bet, game_data):
    """
    Evaluate an over/under bet based on the final score.
    """
    total_score = game_data['PTS_home'] + game_data['PTS_away']
    if bet['Bet Type'] == 'over':
        hit = total_score > bet['Bet Value']
    elif bet['Bet Type'] == 'under':
        hit = total_score < bet['Bet Value']
    else:
        hit = None
    return hit, total_score

def evaluate_spread(bet, game_data):
    """
    Evaluate a spread bet based on the final score and spread.
    """
    point_diff = game_data['PTS_home'] - game_data['PTS_away']
    if bet['Team'] == game_data['HOME_TEAM']:
        hit = point_diff > bet['Bet Value']
    else:
        hit = -point_diff > bet['Bet Value']
    return hit, point_diff

def evaluate_moneyline(bet, game_data):
    """
    Evaluate a moneyline bet based on the winning team.
    """
    winning_team = game_data['HOME_TEAM'] if game_data['PTS_home'] > game_data['PTS_away'] else game_data['AWAY_TEAM']
    hit = winning_team == bet['Team']
    return hit, winning_team

def analyze_bets(games_df, bets_df):
    """
    Analyze each bet in bets_df using data from games_df.
    """
    # Create lists to store results
    bet_results = []
    actual_data = []

    print(bets_df.columns)
    
    for _, bet in bets_df.iterrows():
        # Find the relevant game in games_df
        game_data = games_df[
            (games_df['HOME_TEAM_ID'] == bet['Home Team ID']) &
            (games_df['VISITOR_TEAM_ID'] == bet['Away Team ID'])
        ]
        if game_data.empty:
            bet_results.append(None)
            actual_data.append(None)
            continue
        
        # Only take the first matching row if duplicates exist
        game_data = game_data.iloc[0]
        
        # Determine bet type and evaluate it
        if bet['Bet Type'] in ['over', 'under']:
            hit, actual = evaluate_over_under(bet, game_data)
        elif bet['Bet Type'] == 'spread':
            hit, actual = evaluate_spread(bet, game_data)
        elif bet['Bet Type'] == 'moneyline':
            hit, actual = evaluate_moneyline(bet, game_data)
        else:
            hit, actual = None, None
        
        # Append results
        bet_results.append(hit)
        actual_data.append(actual)
    
    # Add results to bets_df
    bets_df['Bet Hit'] = bet_results
    bets_df['Actual Result'] = actual_data
    
    return bets_df

# Load bets CSV and specify game date
input_date = input("Enter the game date (MM_DD_YYYY): ")
game_date = datetime.strptime(input_date, "%m_%d_%Y")
bets_df = pd.read_csv(f'../nba_saved_csv/nba_betting_data_{input_date}.csv')

# Fetch game stats for the input date
print("Retrieving game and player data from NBA API...")
games_df, player_stats_df = get_games_and_players_data(input_date)
print("Successfully retrieved game and player data")

# Save DataFrame to CSV
# games_df.to_csv('games_df.csv', index=False)
# player_stats_df.to_csv('games_df.csv', index=False)

# Analyze the bets and add hit results
print("Analyzing bets...")
analyzed_bets_df = analyze_bets(games_df, bets_df)

# Display results
print(analyzed_bets_df.head())

# # Save the updated CSV
# output_path = f'../nba_saved_csv/verified_nba_data_{input_date}.csv'
# updated_df.to_csv(output_path, index=False)
# print(f"Updated CSV saved to {output_path}")