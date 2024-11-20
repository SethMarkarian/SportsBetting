import requests
from bs4 import BeautifulSoup
import pandas as pd

def scrape_game_log_by_date(player_name, year, date):
    """
    Scrapes the game log data for a given basketball player and season from basketball-reference.com,
    and returns the game log for the specified date.

    Args:
        player_name (str): The player's full name, e.g., "LeBron James".
        year (int): The season year (e.g., 2025 for the 2024-25 season).
        date (str): The specific date in the format "MM_DD_YYYY" to filter the game logs.

    Returns:
        pd.DataFrame or None: A DataFrame containing the game log for the given date, or None if no game is found.
    """
    # Split the player's name into first and last name
    names = player_name.split()
    if len(names) != 2:
        raise ValueError("Player name must be in the format 'FirstName LastName'")
    
    first_name, last_name = names
    # Create the player's URL based on the naming convention
    url = f"https://www.basketball-reference.com/players/{last_name[0].lower()}/{last_name[:5].lower()}{first_name[:2].lower()}01/gamelog/{year}"

    try:
        # Make a request to the URL
        response = requests.get(url)
        response.raise_for_status()

        # Parse the HTML content
        soup = BeautifulSoup(response.content, "html.parser")

        # Locate the game log table
        table = soup.find("table", {"id": "pgl_basic"})

        if table:
            # Convert the table to a DataFrame
            df = pd.read_html(str(table))[0]

            # Check if the DataFrame has multi-level headers
            if isinstance(df.columns, pd.MultiIndex):
                # Remove the top level of multi-index headers
                df.columns = df.columns.droplevel(0)

            # Format the date for comparison
            formatted_date = pd.to_datetime(date, format="%m_%d_%Y").strftime("%Y-%m-%d")

            # Filter the DataFrame for the specific date
            filtered_game = df[df['Date'] == formatted_date]

            if not filtered_game.empty:
                return filtered_game
            else:
                print(f"No game found for {player_name} on {formatted_date}.")
                return None
        else:
            print("Game log table not found.")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

# Example usage
if __name__ == "__main__":
    player_name = "LeBron James"
    year = 2025
    date = "11_10_2024"  # Example date (March 12, 2025)
    game_log = scrape_game_log_by_date(player_name, year, date)
    
    if game_log is not None:
        print(game_log)
