# flask api to fetch data
# allows chatbot to query data from the database

from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

# helper to connect to db

def query_db(query, args=(), one=False):
    conn = sqlite3.connect("fpl_data.db")
    conn.row_factory = sqlite3.Row  # Return rows as dictionaries
    cur = conn.cursor()
    # Execute query
    cur.execute(query, args)
    rows = cur.fetchall()
    conn.close()
    # Return results
    return (rows[0] if rows else None) if one else rows


# endpoint to get all players
@app.route("/players", methods=["GET"])

def get_players():

    # mapping for input 
    position_mapping = {
        "GK": "1",
        "DEF": "2",
        "MID": "3",
        "FWD": "4"
    }



    position = request.args.get("position") # query param for MID, DEF, FWD, GK
    budget = request.args.get("budget") # query param for budget such as 8.0, 8.5, etc
    name = request.args.get("name") # query param for player name

    # Query to get players based on position and budget
    query = "SELECT * FROM Players"
    args = []


    # if query params provided, then add filters

    if position or budget or name:
        query += " WHERE"
        # Add filters based on query parameters
        if position:
            query += " position = ?"
            args.append(position_mapping[position])
        if budget:
            if position:
                query += " AND"
            query += " cost <= ?"
            args.append(budget)
        if name:
            if position or budget:
                query += " AND"
            query += " name LIKE ?"
            args.append(f"%{name}%")
    
    # Execute query
    players = query_db(query, args)
    return jsonify([dict(player) for player in players])

# get player by id
@app.route("/players/<int:player_id>", methods=["GET"])
def get_player(player_id):
    player = query_db("SELECT * FROM Players WHERE id = ?", [player_id], one=True)
    if player is None:
        return jsonify({"error": "Player not found"}), 404
    return jsonify(dict(player))

# get all teams
@app.route("/teams", methods=["GET"])
def get_teams():
    teams = query_db("SELECT * FROM Teams")
    return jsonify([dict(team) for team in teams])

# get fixtures
@app.route("/fixtures", methods=["GET"])
def get_fixtures():
    # 2 params
    current = request.args.get("is_current")
    next = request.args.get("is_next")

    query = "SELECT * FROM Fixtures"
    args = []

    # if query params provided, then add filters
    if current or next:
        query += " WHERE"
        # Add filters based on query parameters
        if current:
            query += " is_current = ?"
            args.append((int) (current))
        if next:
            if current:
                query += " AND"
            query += " is_next = ?"
            args.append((int) (next))
    
    fixtures = query_db(query, args)
    return jsonify([dict(fixture) for fixture in fixtures])

if __name__ == "__main__":
    app.run(debug=True)
# Run the API and test the endpoints