from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# Base URL for the main API
API_BASE_URL = "http://127.0.0.1:5000"

@app.route("/chat", methods=["POST"])
def chatbot():
    """
    Main chatbot endpoint to handle user input.
    Matches user intent and responds with appropriate data.
    """
    # Get user input from the request
    user_input = request.json.get("message", "").lower()

    # Basic intent matching
    if "forwards" in user_input:
        budget = extract_budget(user_input)
        return jsonify(get_pos_players("FWD", budget))
    elif "midfielders" in user_input:
        budget = extract_budget(user_input)
        return jsonify(get_pos_players("MID", budget))
    elif "defenders" in user_input:
        budget = extract_budget(user_input)
        return jsonify(get_pos_players("DEF", budget))
    elif "goalkeepers" in user_input:
        budget = extract_budget(user_input)
        return jsonify(get_pos_players("GK", budget))
    elif "fixtures" in user_input:
        return jsonify(get_fixtures())
    elif "teams" in user_input:
        return jsonify(get_teams())
    else:
        return jsonify({"message": "I'm sorry, I don't understand that. Please try asking about players, fixtures, or teams."})

def extract_budget(message):
    """
    Extract budget from the user input if mentioned.
    Looks for keywords like 'under', 'below', or 'less' followed by a number.
    """
    words = message.split()
    for i, word in enumerate(words):
        if word in ["under", "below", "less"] and i + 1 < len(words):
            try:
                return float(words[i + 1])
            except ValueError:
                continue
    return None  # No budget found

def get_pos_players(position, budget):
    """
    Fetch players based on position and budget.
    """
    params = {"position": position}
    if budget:
        params["budget"] = budget

    response = requests.get(f"{API_BASE_URL}/players", params=params)
    if response.status_code == 200:
        players = response.json()
        if not players:
            return {"message": f"No {position} players found under £{budget}."}
        return {"players": players}
    return {"message": "Error fetching player data."}

def get_fixtures():
    """
    Fetch fixtures from the API.
    """
    response = requests.get(f"{API_BASE_URL}/fixtures")
    if response.status_code == 200:
        fixtures = response.json()
        return {"fixtures": fixtures}
    return {"message": "Error fetching fixture data."}

def get_teams():
    """
    Fetch teams from the API.
    """
    response = requests.get(f"{API_BASE_URL}/teams")
    if response.status_code == 200:
        teams = response.json()
        return {"teams": teams}
    return {"message": "Error fetching team data."}

if __name__ == "__main__":
    app.run(debug=True, port=5001)
