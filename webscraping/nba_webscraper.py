from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time
import csv
from datetime import date

# Set up Chrome options for headless mode and CI/CD compatibility
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--remote-debugging-port=9222")
chrome_options.add_argument("--disable-gpu")
chrome_options.binary_location = '/usr/bin/google-chrome'

# Set up ChromeDriver path
chrome_driver_path = '/usr/local/bin/chromedriver'
service = Service(chrome_driver_path)

# Initialize the WebDriver
driver = webdriver.Chrome(service=service, options=chrome_options)

# Navigate to the web page
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
output_path = f'../nba_saved_csv/nba_betting_data_{current_date.strftime("%m_%d_%Y")}.csv'
with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(['Player Name', 'Matchup', 'Market', 'Odds', 'Trend Context', 'Linemate Percentage'])
    writer.writerows(combined_player_insight_data)

print(f'Data has been saved to {output_path}')

# Close the driver
driver.quit()
