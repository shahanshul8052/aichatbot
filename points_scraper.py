import requests
from bs4 import BeautifulSoup
import pandas as pd
import datetime

def get_current_gameweek():
    """
    Determine the current gameweek dynamically from the website.
    """
    # Fetch the webpage
    url = "https://fplform.com/fpl-predicted-points"
    response = requests.get(url)
    if response.status_code != 200:
        print("Failed to fetch data from FPL Form. Defaulting to Gameweek 1.")
        return 1

    # Parse the webpage content
    soup = BeautifulSoup(response.text, "html.parser")

    # Extract headers
    headers = [th.text.strip() for th in soup.find_all("th")]
    print("Detected headers:", headers)

    # Look for the first header containing "PPGW"
    for header in headers:
        if "PPGW" in header:
            try:
                # Extract the gameweek number from the header text (e.g., "PPGW21" -> 21)
                current_gw = int("".join(filter(str.isdigit, header)))
                print(f"Current Gameweek detected: {current_gw}")
                return current_gw
            except (IndexError, ValueError):
                print("Error parsing current gameweek from header. Defaulting to Gameweek 1.")
                return 1

    print("Gameweek header not found. Defaulting to Gameweek 1.")
    return 1




def scrape_predicted_points():
    """
    Scrape predicted points for players for the next 6 gameweeks.
    """
    print("Starting to scrape predicted points...")

    url = "https://fplform.com/fpl-predicted-points"
    response = requests.get(url)
    if response.status_code != 200:
        print("Failed to fetch data from FPL Form.")
        return None

    # Parse the webpage content
    soup = BeautifulSoup(response.text, "html.parser")
    table = soup.find("table")
    if not table:
        print("No table found on the webpage.")
        return None

    print("Table found. Extracting headers and rows...")
    headers = [th.text.strip() for th in table.find_all("th")]
    rows = []

    for row in table.find_all("tr")[1:]:
        cols = [col.text.strip() for col in row.find_all("td")]
        while len(cols) < len(headers):
            cols.append("")  # Fill missing columns with empty strings
        rows.append(cols)

    # Convert the table data into a DataFrame
    print("Converting table data into a DataFrame...")
    df = pd.DataFrame(rows, columns=headers)

    # Locate the column with "Prob. of Appearing"
    prob_col_index = headers.index("Prob. ofAppear-ingProbability that the player will play at all in the next match")
    gw_offsets = [1, 3, 6, 9, 12, 15]  # Gameweek column offsets

    # Get the current gameweek
    current_gameweek = get_current_gameweek()
    print(f"Current Gameweek: {current_gameweek}")

    # Extract player name, team, position, and predicted points for the next 6 gameweeks
    predicted_points_data = []
    for _, row in df.iterrows():
        player_name = row["Player"]
        player_team = row["Team"]
        player_position = row["PosPosition"]
        for i, gw_offset in enumerate(gw_offsets):  # Iterate through GW offsets
            gw_col = prob_col_index + gw_offset
            gw_number = current_gameweek + i  # Dynamic gameweek calculation
            if gw_col < len(row):
                predicted_points = row.iloc[gw_col]
                if predicted_points:  # Avoid empty or invalid data
                    predicted_points_data.append({
                        "Player": player_name,
                        "Team": player_team,
                        "Position": player_position,
                        "GW": gw_number,
                        "Predicted Points": float(predicted_points) if predicted_points.replace('.', '', 1).isdigit() else 0.0
                    })

    # Convert to a final DataFrame
    final_df = pd.DataFrame(predicted_points_data)

    # Save the final data to a CSV
    final_df.to_csv("predicted_points.csv", index=False)
    print("Predicted points data saved successfully!")



if __name__ == "__main__":
    scrape_predicted_points()


