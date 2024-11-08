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
items = driver.find_elements(By.CLASS_NAME, 'trend-content-header-info')
players = []
for item in items:
    player_name = item.find_element(By.CLASS_NAME, 'text-style-body-medium').text
    matchup = item.find_element(By.CLASS_NAME, 'text-style-caption-uppercase-normal').text
    market = item.find_element(By.CLASS_NAME, 'text-style-label-medium').text
    odds = item.find_element(By.CLASS_NAME, 'text-style-label-semibold').text
    players.append([player_name, matchup, market, odds])

# Get current date
current_date = date.today()

# Save data to CSV
with open(f'../nba_saved_csv/nfl_betting_data_{current_date.strftime("%m_%d_%Y")}.csv', 'w', newline='', encoding='utf-8') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(['Player Name', 'Matchup', 'Market', 'Odds'])
    writer.writerows(players)

print('Data has been saved to ../nba_saved_csv/nba_betting_data.csv')

driver.quit()
