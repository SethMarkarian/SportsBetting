from basketball_reference_web_scraper import client
from basketball_reference_web_scraper.data import OutputType
import os


# Output all player box scores for January 1st, 2017 in JSON format to 1_1_2017_box_scores.csv
client.player_box_scores(day=7, month=11, year=2024, output_type=OutputType.CSV, output_file_path="1_1_2017_box_scores.csv")