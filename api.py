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
    position = request.args.get("position") # query param for MID, DEF, FWD, GK
    budget = request.args.get("budget") # query param for budget such as 8.0, 8.5, etc

    # Query to get players based on position and budget
    query = "SELECT * FROM Players"
    args = []


    # if query params provided, then add filters

    if position or budget:
        query += " WHERE"
        # Add filters based on query parameters
        if position:
            query += " position = ?"
            args.append(position)
        
        # Add budget filter
        if budget:
            if position:
                query += " AND"
            query += " cost <= ?"
            args.append(budget)
    
    # Execute query
    players = query_db(query, args)
    return jsonify([dict(player) for player in players])