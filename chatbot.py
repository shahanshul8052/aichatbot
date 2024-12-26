import sqlite3
from flask import Flask, request, jsonify
import requests
import string

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
        min_budget, max_budget = extract_budget(user_input)
        return jsonify(get_pos_players("FWD", min_budget, max_budget))
    elif "midfielders" in user_input:
        min_budget, max_budget = extract_budget(user_input)
        print(f"User input: {user_input}")  # Debugging: Original input
        print(f"Extracted min_budget: {min_budget}, max_budget: {max_budget}")  # Debugging
        return jsonify(get_pos_players("MID", min_budget, max_budget))
    elif "defenders" in user_input:
        min_budget, max_budget = extract_budget(user_input)
        return jsonify(get_pos_players("DEF", min_budget, max_budget))
    elif "goalkeepers" in user_input:
        min_budget, max_budget = extract_budget(user_input)
        return jsonify(get_pos_players("GK", min_budget, max_budget))
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

def get_pos_players(position, min_budget=None, max_budget=None):
    """
    Fetch players based on position and budget range.
    """
    # Prepare the query parameters
    params = {"position": position}
    if min_budget is not None:
        params["min_budget"] = min_budget
    if max_budget is not None:
        params["max_budget"] = max_budget

    # Debugging: Print the API parameters
    print("Params sent to API:", params)

    # Send the GET request to the API
    response = requests.get(f"{API_BASE_URL}/players", params=params)

    # Debugging: Log the API response
    print("API response status code:", response.status_code)
    print("API response:", response.json())

    # Check the response and return formatted results
    if response.status_code == 200:
        players = response.json()
        if not players:
            # Create a budget message for the response
            budget_msg = ""
            if min_budget is not None and max_budget is not None:
                budget_msg = f"between £{min_budget} and £{max_budget}"
            elif min_budget is not None:
                budget_msg = f"over £{min_budget}"
            elif max_budget is not None:
                budget_msg = f"under £{max_budget}"
            return {"message": f"No {position} players found {budget_msg}."}
        return {"players": players}

    # Return an error message if the API call fails
    return {"message": "Error fetching player data."}


def extract_budget(message):
    """
    Extract budget range from the user input if mentioned.
    Handles phrases like 'under', 'below', 'over', 'above', 'less', and 'more'.
    """
    words = message.split()
    min_budget = None
    max_budget = None

    for i, word in enumerate(words):
        try:
            # Handle max budget (e.g., "under 10")
            if word in ["under", "below", "less"] and i + 1 < len(words):
                # Strip any trailing punctuation from the next word
                budget = words[i + 1].rstrip(string.punctuation)
                max_budget = float(budget)
            # Handle min budget (e.g., "over 8")
            elif word in ["over", "above", "more"] and i + 1 < len(words):
                # Strip any trailing punctuation from the next word
                budget = words[i + 1].rstrip(string.punctuation)
                min_budget = float(budget)
        except ValueError:
            print(f"Error parsing budget value: {words[i + 1]}")  # Debugging

    # Debugging: Print the extracted values
    print(f"Extracted min_budget: {min_budget}, max_budget: {max_budget}")
    return min_budget, max_budget


def fetch_team_names():
    """
    Fetch the list of team names dynamically from the database.
    """
    conn = sqlite3.connect("fpl_data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM Teams")
    teams = [row[0].lower() for row in cursor.fetchall()]
    conn.close()
    return teams

def extract_team_name(message):
    """
    Extract a team's name from the user input.
    """
    # Dynamically fetch team names
    teams = fetch_team_names()
    for team in teams:
        if team in message.lower():
            return team.capitalize()
    return None


def extract_player_name(message):
    """
    Extract the player's name from the user input.
    handle punctuation and capitalization variations.
    """

    clean_word = message.translate(str.maketrans("", "", string.punctuation)).lower()

    words = clean_word.split()
    for i, word in enumerate(words):
        if word in ["buy", "sell", "hold"] and i + 1 < len(words):
            return " ".join(words[i + 1:]).strip()
    return None  # No player name found


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
