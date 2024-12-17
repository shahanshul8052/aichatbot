from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import pandas as pd
import time

# Path to ChromeDriver
DRIVER_PATH = r"D:\Anshul\ML Projects\aichatbot\chromedriver-win64\chromedriver-win64\chromedriver.exe"

def fetch_player_stats():
    # Set up headless Chrome
    options = Options()
    options.headless = True
    service = Service(DRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=options)

    try:
        # Open the FPL statistics page
        url = "https://fantasy.premierleague.com/statistics"
        driver.get(url)
        time.sleep(5)  # Wait for JavaScript to load

        # Extract the table rows
        table_rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")

        players = []
        for row in table_rows:
            cols = row.find_elements(By.TAG_NAME, "td")

            if len(cols) >= 5:  # Ensure there are at least 5 columns
                # Extract player info (split player name, team, and position)
                player_details = cols[1].text.strip().split("\n")
                player_name = player_details[0]  # Extract player name
                team_position = " ".join(player_details[1:])  # Combine team and position

                # Clean and extract other stats
                cost = float(cols[2].text.strip())  # Cost
                selected_percentage = float(cols[3].text.strip().replace("%", ""))  # Remove % and convert to float
                form = float(cols[4].text.strip())  # Form
                points = int(cols[5].text.strip())  # Points

                # Append to list
                players.append({
                    "Player": player_name,
                    "Team/Position": team_position,
                    "Cost (£)": cost,
                    "Selected (%)": selected_percentage,
                    "Form": form,
                    "Points": points,
                })




        # Convert to DataFrame and save
        df = pd.DataFrame(players)
        df.to_csv("fpl_player_stats.csv", index=False)
        print("Player stats saved to fpl_player_stats.csv")

    finally:
        driver.quit()

if __name__ == "__main__":
    fetch_player_stats()
