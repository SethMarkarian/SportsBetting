import pandas as pd
from nba_api.stats.static import players
import datetime

# Load bets CSV and specify game date
input_date = input("Enter the game date (MM_DD_YYYY): ")
# game_date = datetime.strptime(input_date, "%m_%d_%Y")
df = pd.read_csv(f'../nba_saved_csv/nba_betting_data_{input_date}.csv')

# Extract player names (assuming column name is 'Player' - adjust as necessary)
player_initials = df['Player Name'].tolist()

# Get the list of NBA players
nba_players = players.get_players()

# Function to find full names from initial and last name format (e.g., 'J. Tatum')
def get_full_name(initial_last):
    try:
        initial, last_name = initial_last.split('. ')
        last_name = last_name.strip()
        matching_players = [p for p in nba_players if p['last_name'].lower() == last_name.lower() and p['first_name'].startswith(initial.upper())]
        if matching_players:
            return f"{matching_players[0]['first_name']} {matching_players[0]['last_name']}"
        else:
            return None
    except ValueError:
        return None  # Handle cases where the format isn't correct

# Replace player names in the DataFrame
df['Player Name'] = df['Player Name'].apply(lambda name: get_full_name(name) if get_full_name(name) else name)

# Remove rows where the "Market" column contains "Q"
df = df[~df['Market'].str.contains("Q", na=False)]

# Rename "Matchup" column to "Opponent"
df.rename(columns={"Matchup": "Opponent"}, inplace=True)

# Remove "vs." and "@" from the "Opponent" column
df["Opponent"] = df["Opponent"].str.replace("vs.", "").str.replace("@", "").str.strip()

# Save the updated DataFrame back to the CSV file
output_path = f'../nba_saved_csv/nba_betting_data_{input_date}.csv'
df.to_csv(output_path, index=False)

print(f"Updated CSV saved to {output_path}")
