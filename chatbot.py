from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# API base URL

# connect flask to a chatbot 
API_BASE_URL = "http://127.0.0.1:5000"

@app.route("/chat", methods=["POST"])
def chatbot():
    # user input 

    user_input = request.json.get("message", "").lower()

    # basic matching intent for now 

    if "forwards" in user_input:
        # extract budget from message
        budget = extract_budget(user_input)
        return jsonify(get_pos_players("FWD", budget))
    elif "midfielders" in user_input:
        # extract budget from message
        budget = extract_budget(user_input)
        return jsonify(get_pos_players("MID", budget))
    elif "defenders" in user_input:
        # extract budget from message
        budget = extract_budget(user_input)
        return jsonify(get_pos_players("DEF", budget))
    elif "goalkeepers" in user_input:
        # extract budget from message
        budget = extract_budget(user_input)
        return jsonify(get_pos_players("GK", budget))
    elif "fixtures" in user_input:
        return jsonify(get_fixtures())
    elif "teams" in user_input:
        return jsonify(get_teams())
    else:
        return jsonify({"message": "I'm sorry, I don't understand that."})




def extract_budget(message):
    # extract budget from user input 
    words = message.split()
    for i, word in enumerate(words):
        if word in ["under", "below", "less"] and i + 1 < len(words):
            try:
                return float(words[i + 1])
            except ValueError:
                pass
    return None # no budget found

def get_pos_players(position, budget):
    # Construct API URL
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

# Helper function: Get all fixtures
def get_fixtures():
    response = requests.get(f"{API_BASE_URL}/fixtures")
    if response.status_code == 200:
        fixtures = response.json()
        return {"fixtures": fixtures}
    return {"message": "Error fetching fixture data."}

# Helper function: Get all teams
def get_teams():
    response = requests.get(f"{API_BASE_URL}/teams")
    if response.status_code == 200:
        teams = response.json()
        return {"teams": teams}
    return {"message": "Error fetching team data."}

if __name__ == "__main__":
    app.run(debug=True, port=5001)