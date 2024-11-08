from selenium import webdriver
from selenium.webdriver.common.by import By
import time
import csv
from datetime import date

# Set up the WebDriver
driver = webdriver.Chrome()  # Ensure ChromeDriver is installed and in PATH
driver.get('https://linemate.io/nba/trends')

# Wait for the page to load JavaScript content
time.sleep(5)  # Adjust based on your internet speed

# Extract the player data
items = driver.find_elements(By.CLASS_NAME, 'trend-content-header')
players = []
for item in items:
    try:
        player_name = item.find_element(By.CLASS_NAME, 'text-style-body-medium').text
        matchup = item.find_element(By.CLASS_NAME, 'text-style-caption-uppercase-normal').text
        market = item.find_element(By.CLASS_NAME, 'text-style-label-medium').text
        odds = item.find_element(By.CLASS_NAME, 'text-style-label-semibold').text

        players.append([player_name, matchup, market, odds])
    except Exception as e:
        print(f"Error extracting data from an item: {e}")
        continue

# Extract the insight data
items = driver.find_elements(By.CLASS_NAME, 'trend-content-insights')
insights = []

for item in items:
    try:
        insight = item.find_element(By.CLASS_NAME, 'text-style-label-normal').text.replace("• ", "")
        linemate_percentage = item.find_element(By.CLASS_NAME, 'text-style-label-tabular-medium').text

        insights.append([insight, linemate_percentage])
    except Exception as e:
        print(f"Error extracting data from an item: {e}")
        continue

# Get current date
current_date = date.today()

# Combine player data with linemate insights
combined_player_insight_data = [players + insights for players, insights in zip(players, insights)]


# Save data to CSV with trend context
with open(f'../nba_saved_csv/nba_betting_data_{current_date.strftime("%m_%d_%Y")}.csv', 'w', newline='', encoding='utf-8') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(['Player Name', 'Matchup', 'Market', 'Odds', 'Trend Context', 'Linemate Percentage'])
    writer.writerows(combined_player_insight_data)

print(f'Data has been saved to ../nba_saved_csv/nba_betting_data_{current_date.strftime("%m_%d_%Y")}.csv')

driver.quit()
