from flask import Flask, request, jsonify
import requests
import sqlite3

app = Flask(__name__)

# Base URL for FPL API
FPL_API_BASE_URL = "https://fantasy.premierleague.com/api"

# Helper to connect to SQLite database
def query_db(query, args=(), one=False):
    conn = sqlite3.connect("fpl_data.db")
    conn.row_factory = sqlite3.Row  # Return rows as dictionaries
    cur = conn.cursor()
    cur.execute(query, args)
    rows = cur.fetchall()
    conn.close()
    return (rows[0] if rows else None) if one else rows

# ============================
# Players Endpoints
# ============================

# Get all players with optional filters
@app.route("/players", methods=["GET"])
def get_players():
    position_mapping = {
        "GK": "1",
        "DEF": "2",
        "MID": "3",
        "FWD": "4"
    }

    # Query parameters
    position = request.args.get("position")  # GK, DEF, MID, FWD
    budget = request.args.get("budget")      # e.g., 8.0
    name = request.args.get("name")          # Player name (e.g., Salah)

    query = "SELECT * FROM Players"
    args = []

    # Apply filters if query params are provided
    if position or budget or name:
        query += " WHERE"
        if position:
            query += " position = ?"
            args.append(position_mapping[position.upper()])
        if budget:
            if args:
                query += " AND"
            query += " cost <= ?"
            args.append(float(budget))
        if name:
            if args:
                query += " AND"
            query += " name LIKE ?"
            args.append(f"%{name}%")
    
    # Fetch players from DB
    players = query_db(query, args)
    return jsonify([dict(player) for player in players])

# Get player by ID
@app.route("/players/<int:player_id>", methods=["GET"])
def get_player(player_id):
    player = query_db("SELECT * FROM Players WHERE id = ?", [player_id], one=True)
    if not player:
        return jsonify({"error": "Player not found"}), 404
    return jsonify(dict(player))

# ============================
# Teams Endpoints
# ============================

# Get all teams
@app.route("/teams", methods=["GET"])
def get_teams():
    teams = query_db("SELECT * FROM Teams")
    return jsonify([dict(team) for team in teams])

# ============================
# Fixtures Endpoints (Live)
# ============================

# Fetch live fixtures with optional filters
@app.route("/fixtures", methods=["GET"])
def get_fixtures():
    # Optional query parameters
    is_current = request.args.get("is_current", None)
    is_next = request.args.get("is_next", None)
    gameweek = request.args.get("gameweek", None)

    # Fetch live fixtures
    response = requests.get(f"{FPL_API_BASE_URL}/fixtures/")
    if response.status_code != 200:
        return jsonify({"error": "Failed to fetch live fixtures"}), 500
    fixtures = response.json()

    # Fetch current gameweek
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

    # Map team names and prepare a simplified response
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

# ============================
# Helper Endpoints
# ============================

# Get a team's upcoming fixtures
@app.route("/fixtures/<string:team_name>", methods=["GET"])
def get_team_fixtures(team_name):
    # Fetch live fixtures
    response = requests.get(f"{FPL_API_BASE_URL}/fixtures/")
    if response.status_code != 200:
        return jsonify({"error": "Failed to fetch live fixtures"}), 500
    
    fixtures = response.json()

    # Fetch team ID for the given name
    team_response = requests.get(f"{FPL_API_BASE_URL}/bootstrap-static/")
    if team_response.status_code != 200:
        return jsonify({"error": "Failed to fetch team data"}), 500
    
    team_data = {team["id"]: team["name"] for team in team_response.json()["teams"]}
    team_id = next((id for id, name in team_data.items() if name.lower() == team_name.lower()), None)
    if not team_id:
        return jsonify({"error": f"Team '{team_name}' not found"}), 404

    # Filter fixtures for the given team
    team_fixtures = [
        f for f in fixtures if f.get("team_h") == team_id or f.get("team_a") == team_id
    ]

    # Add team names to fixtures
    for fixture in team_fixtures:
        fixture["team_h_name"] = team_data.get(fixture["team_h"], "Unknown")
        fixture["team_a_name"] = team_data.get(fixture["team_a"], "Unknown")

    return jsonify(team_fixtures)

if __name__ == "__main__":
    app.run(debug=True)
