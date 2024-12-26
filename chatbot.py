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
    elif "fixtures" in user_input or "upcoming games" in user_input:
        team_name = extract_team_name(user_input)
        if team_name:
            return jsonify(get_team_fixtures(team_name))
        return jsonify({"message": "Please specify a team for fixture analysis (e.g., 'What are Liverpool's next fixtures?')."})
    elif "buy" in user_input or "sell" in user_input or "hold" in user_input:
        player_name = extract_player_name(user_input)
        if player_name:
            return jsonify(get_player_recommendation(player_name))
        return jsonify({"message": "Please specify a player for recommendations (e.g., 'Should I buy Salah?')."})
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


def extract_team_name(message):
    """
    Extract a team's name from the user input.
    """
    teams = ["liverpool", "man city", "chelsea", "arsenal", "spurs", "man united"]  # Expand this list
    for team in teams:
        if team in message:
            return team.capitalize()
    return None


def extract_player_name(message):
    """
    Extract the player's name from the user input.
    """
    words = message.split()
    for i, word in enumerate(words):
        if word in ["buy", "sell", "hold"] and i + 1 < len(words):
            return " ".join(words[i + 1:])  # Assume the player's name follows
    return None


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


def get_team_fixtures(team_name):
    """
    Fetch upcoming fixtures for a team.
    """
    response = requests.get(f"{API_BASE_URL}/fixtures/difficulty", params={"team_name": team_name, "gameweeks": 3})
    if response.status_code == 200:
        return response.json()
    return {"message": "Error fetching fixture data."}


def get_player_recommendation(player_name):
    """
    Fetch player recommendation based on form and cost.
    """
    # Fetch recommendations from the API
    response = requests.get(f"{API_BASE_URL}/players/recommendations", params={"player_name": player_name})
    if response.status_code == 200:
        recommendations = response.json()

        # Normalize the player name for matching
        player_name_normalized = player_name.lower().replace(".", "").strip()

        # Debugging: Print player_name_normalized
        print(f"Normalized input name: {player_name_normalized}")

        # Search for the player in the buy, sell, and hold lists
        for category, players in recommendations.items():
            for player in players:
                # Normalize the player's name in the database
                player_name_in_db = player["name"].lower().replace(".", "").strip()
                
                # Debugging: Print normalized database name
                print(f"Checking against database name: {player_name_in_db}")
                
                if player_name_normalized in player_name_in_db:
                    if category == "buy":
                        return {"message": f"{player['name']} is recommended to buy based on current form and points."}
                    elif category == "sell":
                        return {"message": f"{player['name']} is recommended to sell based on current form and points."}
                    elif category == "hold":
                        return {"message": f"{player['name']} is recommended to hold based on current form and points."}

        # If the player isn't found in any list
        return {"message": f"{player_name.capitalize()} does not meet any recommendation criteria at the moment."}

    return {"message": "Error fetching player recommendation."}


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
