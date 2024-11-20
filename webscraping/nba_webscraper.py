from playwright.sync_api import sync_playwright
import pandas as pd
from datetime import date
from nba_api.stats.static import players

def fetch_nba_trends():
    try:
        # Launch headless browser using Playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)  # Ensure headless mode is enabled
            page = browser.new_page()

            # Navigate to the webpage
            url = 'https://linemate.io/nba/trends'
            page.goto(url)

            # Wait for dynamic content to load
            page.wait_for_selector('.trend-content-header')  # Wait for the player data section

            # Extract player data
            players = []
            player_items = page.query_selector_all('.trend-content-header')

            for item in player_items:
                try:
                    player_name = item.query_selector('.text-style-body-medium').inner_text().strip()
                    matchup = item.query_selector('.text-style-caption-uppercase-normal').inner_text().strip()
                    market = item.query_selector('.text-style-label-medium').inner_text().strip()
                    odds = item.query_selector('.text-style-label-semibold').inner_text().strip()
                    players.append([player_name, matchup, market, odds])
                except Exception as e:
                    print(f"Error extracting player data: {e}")
                    continue

            # Extract insight data
            insights = []
            insight_items = page.query_selector_all('.trend-content-insights')

            for item in insight_items:
                try:
                    insight = item.query_selector('.text-style-label-normal').inner_text().strip().replace("• ", "")
                    linemate_percentage = item.query_selector('.text-style-label-tabular-medium').inner_text().strip()
                    insights.append([insight, linemate_percentage])
                except Exception as e:
                    print(f"Error extracting insight data: {e}")
                    continue

            # Combine player and insight data into a DataFrame
            combined_data = []
            for player, insight in zip(players, insights):
                combined_row = player + insight  # Combine player data with insight data
                combined_data.append(combined_row)

            # Create DataFrame
            df = pd.DataFrame(combined_data, columns=['Player Name', 'Matchup', 'Market', 'Odds', 'Trend Context', 'Linemate Percentage'])

            # Debug: Print first 5 rows of the DataFrame to check the data
            print(f"Data preview (first 5 rows):\n{df.head()}")

            # Get current date
            current_date = date.today()

            # Save data to CSV
            output_path = f'../nba_saved_csv/nba_betting_data_{current_date.strftime("%m_%d_%Y")}.csv'
            df.to_csv(output_path, index=False)

            print(f'Data has been saved to {output_path}')
            browser.close()

    except Exception as e:
        print(f"Error: {e}")

def clean():
    # Get current date
    current_date = date.today()

    df = pd.read_csv(f'../nba_saved_csv/nba_betting_data_{current_date.strftime("%m_%d_%Y")}.csv')

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
    df["Opponent"] = df["Opponent"].str.replace("VS ", "").str.replace("@", "").str.strip()

    # Save the updated DataFrame back to the CSV file
    output_path = f'../nba_saved_csv/nba_betting_data_{current_date.strftime("%m_%d_%Y")}.csv'
    df.to_csv(output_path, index=False)

    print(f"Updated CSV saved to {output_path}")


# Run the function
if __name__ == "__main__":
    fetch_nba_trends()
    clean()
