from flask import Flask, request, jsonify
import requests
import sqlite3

app = Flask(__name__)

FPL_API_BASE_URL = "https://fantasy.premierleague.com/api"


def query_db(query, args=(), one=False):
    """
    Execute a query on the SQLite database and return the results.
    :param query: SQL query string
    :param args: Query parameters
    :param one: Whether to fetch one result or all results
    :return: Query result(s)
    """
    conn = sqlite3.connect("fpl_data.db")
    conn.row_factory = sqlite3.Row  # Enable row access as dictionaries
    cur = conn.cursor()
    cur.execute(query, args)
    rows = cur.fetchall()
    conn.close()
    return (rows[0] if rows else None) if one else rows

# get all players

@app.route("/players", methods=["GET"])
def get_players():
    """
    Get all players with optional filters for position, budget, and name.
    Query Params:
      - position: GK, DEF, MID, FWD (e.g., position=GK)
      - min_budget: Minimum cost (e.g., min_budget=8.0)
      - max_budget: Maximum cost (e.g., max_budget=10.0)
    """
    # Mapping for player positions
    position_mapping = {
        "GK": "1",
        "DEF": "2",
        "MID": "3",
        "FWD": "4"
    }

    # Extract query parameters
    position = request.args.get("position")
    min_budget = request.args.get("min_budget", type=float)
    max_budget = request.args.get("max_budget", type=float)

    # Ensure position is mapped correctly
    if position and position.upper() in position_mapping:
        position = position_mapping[position.upper()]
    else:
        return jsonify({"error": "Invalid or missing position parameter"}), 400

    # Build the SQL query
    query = "SELECT * FROM Players WHERE position = ?"
    args = [position]

    if min_budget is not None:
        query += " AND cost >= ?"
        args.append(min_budget)
    if max_budget is not None:
        query += " AND cost <= ?"
        args.append(max_budget)

    # Execute the query and fetch results
    players = query_db(query, args)

    return jsonify([dict(player) for player in players])


@app.route("/players/<int:player_id>", methods=["GET"])
def get_player(player_id):
    """
    Get player details by ID.
    :param player_id: Player ID
    """
    player = query_db("SELECT * FROM Players WHERE id = ?", [player_id], one=True)
    if not player:
        return jsonify({"error": "Player not found"}), 404
    return jsonify(dict(player))

# endpoint to get all teams

@app.route("/teams", methods=["GET"])
def get_teams():
    """
    Get all teams.
    """
    teams = query_db("SELECT * FROM Teams")
    return jsonify([dict(team) for team in teams])

# fixtures endpoint l

@app.route("/fixtures", methods=["GET"])
def get_fixtures():
    """
    Fetch live fixtures with optional filters for current, next, or specific gameweeks.
    Query Params:
      - is_current: Boolean (1 or 0)
      - is_next: Boolean (1 or 0)
      - gameweek: Specific gameweek number
    """
    # Optional query parameters
    is_current = request.args.get("is_current", None)
    is_next = request.args.get("is_next", None)
    gameweek = request.args.get("gameweek", None)

    # Fetch fixtures from FPL API
    response = requests.get(f"{FPL_API_BASE_URL}/fixtures/")
    if response.status_code != 200:
        return jsonify({"error": "Failed to fetch live fixtures"}), 500
    fixtures = response.json()

    # Fetch current gameweek from bootstrap data
    bootstrap_response = requests.get(f"{FPL_API_BASE_URL}/bootstrap-static/")
    if bootstrap_response.status_code != 200:
        return jsonify({"error": "Failed to fetch bootstrap data"}), 500
    bootstrap_data = bootstrap_response.json()
    current_gameweek = next(
        (event["id"] for event in bootstrap_data["events"] if event["is_current"]), None
    )
    next_gameweek = current_gameweek + 1 if current_gameweek else None

    # Filter fixtures
    if gameweek:
        fixtures = [f for f in fixtures if f.get("event") == int(gameweek)]
    if is_current:
        fixtures = [f for f in fixtures if f.get("event") == current_gameweek]
    if is_next:
        fixtures = [f for f in fixtures if f.get("event") == next_gameweek]

    # Map team names to IDs
    team_data = {team["id"]: team["name"] for team in bootstrap_data["teams"]}
    simple_fixtures = []
    for fixture in fixtures:
        simple_fixtures.append({
            "team_h_name": team_data.get(fixture["team_h"], "Unknown"),
            "team_a_name": team_data.get(fixture["team_a"], "Unknown"),
            "kickoff_time": fixture.get("kickoff_time"),
            "team_h_score": fixture.get("team_h_score"),
            "team_a_score": fixture.get("team_a_score"),
            "difficulty": {
                "home": fixture.get("team_h_difficulty"),
                "away": fixture.get("team_a_difficulty")
            }
        })

    return jsonify(simple_fixtures)

@app.route("/fixtures/<string:team_name>", methods=["GET"])
def get_team_fixtures(team_name):
    """
    Get fixtures for a specific team by name.
    :param team_name: Name of the team (case-insensitive)
    """
    # Fetch fixtures from FPL API
    response = requests.get(f"{FPL_API_BASE_URL}/fixtures/")
    if response.status_code != 200:
        return jsonify({"error": "Failed to fetch live fixtures"}), 500
    fixtures = response.json()

    # Fetch team data from bootstrap API
    team_response = requests.get(f"{FPL_API_BASE_URL}/bootstrap-static/")
    if team_response.status_code != 200:
        return jsonify({"error": "Failed to fetch team data"}), 500
    team_data = {team["id"]: team["name"] for team in team_response.json()["teams"]}

    # Find team ID by name
    team_id = next((id for id, name in team_data.items() if name.lower() == team_name.lower()), None)
    if not team_id:
        return jsonify({"error": f"Team '{team_name}' not found"}), 404

    # Filter fixtures for the team
    team_fixtures = [
        f for f in fixtures if f.get("team_h") == team_id or f.get("team_a") == team_id
    ]

    # Add team names to fixtures
    for fixture in team_fixtures:
        fixture["team_h_name"] = team_data.get(fixture["team_h"], "Unknown")
        fixture["team_a_name"] = team_data.get(fixture["team_a"], "Unknown")

    return jsonify(team_fixtures)


# In api.py
@app.route("/players/recommendations", methods=["GET"])
def get_recs():
    """
    Get player recommendations based on form and points.
    """
    # Query players from the database
    players = query_db("SELECT * FROM Players")
    if not players:
        return jsonify({"error": "No players found"}), 404

    # Recommendation thresholds
    buy_criteria = {"form": 4.0, "cost": 8.0}
    sell_criteria = {"form": 2.9, "cost": 8.0}

    # Recommendation lists
    recommendations = {"buy": [], "sell": [], "hold": []}

    # Logic to populate recommendations
    for player in players:
        player_data = dict(player)
        form = player_data["form"]
        cost = player_data["cost"]

        if form >= buy_criteria["form"] and cost <= buy_criteria["cost"]:
            recommendations["buy"].append(player_data)
        elif form <= sell_criteria["form"] and cost >= sell_criteria["cost"]:
            recommendations["sell"].append(player_data)
        else:
            recommendations["hold"].append(player_data)

    return jsonify(recommendations)



# fixture difficulty endpoint
@app.route("/fixtures/difficulty", methods=["GET"])
def get_fixture_difficulty():
    """
    Endpoint to calculate fixture difficulty for a team over the next N gameweeks.
    Query parameters:
    - team_name: Name of the team (required)
    - gameweeks: Number of upcoming gameweeks to analyze (default: 3)
    """
    # Query parameters
    team_name = request.args.get("team_name")
    gameweeks = int(request.args.get("gameweeks", 3))  # Default to 3 upcoming fixtures

    if not team_name:
        return jsonify({"error": "Please provide a team_name parameter"}), 400

    # Fetch live fixtures
    response = requests.get(f"{FPL_API_BASE_URL}/fixtures/")
    if response.status_code != 200:
        return jsonify({"error": "Failed to fetch live fixtures"}), 500

    fixtures = response.json()

    # Fetch bootstrap-static data to get the current gameweek and team info
    bootstrap_response = requests.get(f"{FPL_API_BASE_URL}/bootstrap-static/")
    if bootstrap_response.status_code != 200:
        return jsonify({"error": "Failed to fetch bootstrap data"}), 500

    bootstrap_data = bootstrap_response.json()
    current_gameweek = next(
        (event["id"] for event in bootstrap_data["events"] if event["is_current"]), None
    )
    if not current_gameweek:
        return jsonify({"error": "Could not determine the current gameweek"}), 500

    teams = {team["id"]: team["name"] for team in bootstrap_data["teams"]}

    # Find the team ID for the given name
    team_id = next((id for id, name in teams.items() if name.lower() == team_name.lower()), None)
    if not team_id:
        return jsonify({"error": f"Team '{team_name}' not found"}), 404

    # Filter fixtures for the given team and upcoming gameweeks
    upcoming_fixtures = [
        f for f in fixtures if f.get("event") and f["event"] >= current_gameweek and
        (f["team_h"] == team_id or f["team_a"] == team_id)
    ]

    # Limit to the next N gameweeks
    upcoming_fixtures = sorted(upcoming_fixtures, key=lambda x: x["event"])[:gameweeks]

    # Map fixture details
    fixture_difficulties = []
    for fixture in upcoming_fixtures:
        fixture_difficulties.append({
            "gameweek": fixture["event"],
            "opponent": teams[fixture["team_a"]] if fixture["team_h"] == team_id else teams[fixture["team_h"]],
            "home_away": "Home" if fixture["team_h"] == team_id else "Away",
            "difficulty": fixture["team_h_difficulty"] if fixture["team_h"] == team_id else fixture["team_a_difficulty"]
        })

    # Calculate average difficulty
    avg_difficulty = (
        sum(f["difficulty"] for f in fixture_difficulties) / len(fixture_difficulties)
        if fixture_difficulties else 0
    )

    return jsonify({
        "team": team_name,
        "upcoming_fixtures": fixture_difficulties,
        "average_difficulty": round(avg_difficulty, 2)
    })

# FUTURE ENHANCEMENT - FIXTURED BASED LOGIC FOR RECS


# start the Flask app

if __name__ == "__main__":
    app.run(debug=True)
