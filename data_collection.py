import requests

def fetch_fpl_data():
    # FPL API endpoint
    url = "https://fantasy.premierleague.com/api/bootstrap-static/"
    response = requests.get(url)

    if response.status_code != 200:
        print(f"Failed to fetch data. Status code: {response.status_code}")
        return None

    # Parse JSON response
    data = response.json()

    # Extract important areas 
    players = data["elements"]  # Player statistics
    teams = data["teams"]       # Team strengths
    fixtures = data["events"]   # Fixture schedules

    # Return the data as dictionaries
    return {"players": players, "teams": teams, "fixtures": fixtures}

if __name__ == "__main__":
    data = fetch_fpl_data()
    if data:
        print("Data fetched successfully!")
        print(f"Number of players: {len(data['players'])}")
        print(f"Number of teams: {len(data['teams'])}")
        print(f"Number of fixtures: {len(data['fixtures'])}")
