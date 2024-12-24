import requests

def fetch_fpl_data():
    # FPL API endpoints
    bootstrap_url = "https://fantasy.premierleague.com/api/bootstrap-static/"
    fixtures_url = "https://fantasy.premierleague.com/api/fixtures/"

    # Fetch bootstrap data (players, teams, and events)
    bootstrap_response = requests.get(bootstrap_url)
    if bootstrap_response.status_code != 200:
        print(f"Failed to fetch bootstrap data. Status code: {bootstrap_response.status_code}")
        return None

    bootstrap_data = bootstrap_response.json()

    # Extract important sections
    players = bootstrap_data["elements"]  # Player statistics
    teams = bootstrap_data["teams"]       # Team strengths
    events = bootstrap_data["events"]     # Gameweeks (not detailed fixtures)

    # Fetch detailed fixture data
    fixtures_response = requests.get(fixtures_url)
    if fixtures_response.status_code != 200:
        print(f"Failed to fetch fixture data. Status code: {fixtures_response.status_code}")
        fixtures = []
    else:
        fixtures = fixtures_response.json()  # Detailed fixtures

    # Return the data as dictionaries
    return {
        "players": players,
        "teams": teams,
        "events": events,  # Gameweeks
        "fixtures": fixtures,  # Detailed fixtures
    }

if __name__ == "__main__":
    data = fetch_fpl_data()
    if data:
        print("Data fetched successfully!")
        print(f"Number of players: {len(data['players'])}")
        print(f"Number of teams: {len(data['teams'])}")
        print(f"Number of events (gameweeks): {len(data['events'])}")
        print(f"Number of fixtures: {len(data['fixtures'])}")
    else:    
        print("Failed to fetch data. Exiting.")