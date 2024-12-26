import pandas as pd
import requests

FPL_API_BASE_URL = "https://fantasy.premierleague.com/api"

def fetch_data():
    # Fetch data from API
    players_response = requests.get(f"{FPL_API_BASE_URL}/bootstrap-static/")
    fixtures_response = requests.get(f"{FPL_API_BASE_URL}/fixtures/")

    players_data = players_response.json()
    fixtures_data = fixtures_response.json()

    players_df = pd.DataFrame(players_data["elements"])
    teams_df = pd.DataFrame(players_data["teams"])
    fixtures_df = pd.DataFrame(fixtures_data)

    # Map team IDs to team names
    team_mapping = teams_df.set_index("id")["name"].to_dict()
    players_df["team_name"] = players_df["team"].map(team_mapping)

    # Add position information
    position_mapping = {1: "GK", 2: "DEF", 3: "MID", 4: "FWD"}
    players_df["position"] = players_df["element_type"].map(position_mapping)

    # Strength columns
    players_df["team_strength_home"] = players_df["team"].map(teams_df.set_index("id")["strength_attack_home"])
    players_df["team_strength_away"] = players_df["team"].map(teams_df.set_index("id")["strength_attack_away"])

    # Merge data into one dataset
    data = []
    for _, player in players_df.iterrows():
        player_fixtures = fixtures_df[
            (fixtures_df["team_h"] == player["team"]) | (fixtures_df["team_a"] == player["team"])
        ]
        for _, fixture in player_fixtures.iterrows():
            if fixture["team_h"] == player["team"]:
                opponent_team = team_mapping[fixture["team_a"]]
                difficulty = fixture["team_h_difficulty"]
            else:
                opponent_team = team_mapping[fixture["team_h"]]
                difficulty = fixture["team_a_difficulty"]

            data.append({
                "player_name": player["web_name"],
                "position": player["position"],
                "recent_form": player["form"],
                "total_points": player["total_points"],
                "team_name": player["team_name"],
                "team_strength_home": players_df.loc[players_df["team"] == player["team"], "team_strength_home"].values[0],
                "team_strength_away": players_df.loc[players_df["team"] == player["team"], "team_strength_away"].values[0],
                "opponent_team": opponent_team,
                "fixture_difficulty": difficulty,
                "gameweek": fixture["event"],  # Add gameweek information
            })

    data_df = pd.DataFrame(data)
    return data_df

if __name__ == "__main__":
    data = fetch_data()
    print(data.head())
    data.to_csv("training_data.csv", index=False)
