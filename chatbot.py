import sqlite3
from flask import Flask, request, jsonify
import requests
import string
import pandas as pd
import numpy as np
import pickle
import joblib
from fuzzywuzzy import process

app = Flask(__name__)

# Base URL for the main API
API_BASE_URL = "http://127.0.0.1:5000"
# Load the trained model and dataset
MODEL_PATH = "trained_model.pkl"
DATA_PATH = "training_data.csv"

try:
    model = joblib.load("trained_model.pkl")
    print("Model loaded successfully!")
except Exception as e:
    print(f"Error loading model: {e}")

try:
    data = pd.read_csv(DATA_PATH)
    print("Data loaded successfully.")
except Exception as e:
    print(f"Error loading data: {e}")

    

@app.route("/chat", methods=["POST"])
def chatbot():
    """
    Main chatbot endpoint to handle user input.
    Matches user intent and responds with appropriate data.
    """
    # Get user input from the request
    user_input = request.json.get("message", "").lower()

    # Basic intent matching
    if "predict points" in user_input:
        player_name = extract_player_name_prediction(user_input)
        gameweek = extract_gameweek(user_input)
        if player_name and gameweek:
            return jsonify(predict_player_points(player_name, gameweek))
        return jsonify({"message": "Please provide both a valid player name and gameweek for prediction."})
    elif "forwards" in user_input:
        min_budget, max_budget = extract_budget(user_input)
        return jsonify(get_pos_players("FWD", min_budget, max_budget))
    elif "midfielders" in user_input:
        min_budget, max_budget = extract_budget(user_input)
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
        player_name = extract_player_name_transfer(user_input)
        if player_name:
            return jsonify(get_player_recommendation(player_name))
        return jsonify({"message": "Please specify a player for recommendations (e.g., 'Should I buy Salah?')."})
    elif "teams" in user_input:
        return jsonify(get_teams())
    else:
        return jsonify({"message": "I'm sorry, I don't understand that. Please try asking about players, fixtures, or teams."})
    
@app.route("/predicted-points", methods=["POST"])
def get_predicted_points():
    """
    Fetch predicted points for a specific player from fplform.com.
    """
    player_name = extract_player_name_prediction(request.json.get("message", ""))
    if not player_name:
        return jsonify({"message": "Please provide a valid player name."})

    try:
        # Load the predicted points
        df = pd.read_csv("predicted_points.csv")

        # Match player name
        player_row = df[df["Player"].str.lower() == player_name.lower()]
        if not player_row.empty:
            predicted_points = player_row["Predicted Points"].values[0]
            return jsonify({
                "message": f"{player_name.capitalize()} is expected to score approximately {predicted_points} points."
            })
        else:
            return jsonify({"message": f"No predicted points data found for {player_name.capitalize()}."})

    except Exception as e:
        return jsonify({"message": f"Error fetching predicted points: {str(e)}"})

def extract_gameweek(message):
    """
    Extract gameweek number from the user input.
    """
    words = message.lower().split()
    for i, word in enumerate(words):
        if word.lower() == "gameweek" and i + 1 < len(words):
            try:
                return int(words[i + 1].strip(string.punctuation))
            except ValueError:
                continue
    return None


def parse_query(user_input):
    """
    Parse the user input to extract player name and gameweek.
    """
    words = user_input.split()
    player_name = None
    gameweek = None

    for i, word in enumerate(words):
        if word == "gameweek" and i + 1 < len(words):
            try:
                gameweek = int(words[i + 1])
            except ValueError:
                continue
        elif word == "for" and i + 1 < len(words):
            player_name = words[i + 1].capitalize()

    return player_name, gameweek


def predict_points(player_name, gameweek):
    """
    Predict the next gameweek points for a player.
    """
    # Filter data for the given player and gameweek
    player_data = data[(data["player_name"].str.lower() == player_name.lower()) & (data["gameweek"] == gameweek)]

    if player_data.empty:
        return f"Data for {player_name} in Gameweek {gameweek} is not available."

    # Extract features for the prediction
    features = player_data[["recent_form", "team_strength_home", "team_strength_away", "fixture_difficulty", "gameweek"]].values

    # Make prediction using the trained model
    predicted_points = model.predict(features)

    return f"{player_name} is expected to score approximately {predicted_points[0]:.2f} points in Gameweek {gameweek}."

def match_player_name(player_name, available_names):
    """
    Match a player's name from the available names in the CSV.
    Uses fuzzy matching to allow partial matches.
    """
    best_match, score = process.extractOne(player_name, available_names)
    if score > 70:  # Threshold for a valid match
        return best_match
    return None

def predict_player_points(player_name, gameweek):
    """
    Fetch predicted points for a specific player and gameweek from the scraped data.
    """
    try:
        # Load the predicted points
        df = pd.read_csv("predicted_points.csv")

        # Get all available player names
        available_names = df["Player"].tolist()

        # Match user input to available player names
        matched_name = match_player_name(player_name, available_names)

        if not matched_name:
            return {"message": f"No predicted points data found for {player_name.capitalize()}."}

        # Match player name and gameweek
        player_row = df[(df["Player"].str.lower() == matched_name.lower()) & (df["GW"] == gameweek)]
        if not player_row.empty:
            predicted_points = player_row["Predicted Points"].values[0]
            return {"message": f"{matched_name} is expected to score approximately {predicted_points} points in Gameweek {gameweek}."}
        else:
            return {"message": f"No predicted points data found for {player_name.capitalize()} in Gameweek {gameweek}."}

    except Exception as e:
        return {"message": f"Error fetching predicted points: {str(e)}"}



def get_current_gameweek():
    """
    Fetch the current gameweek dynamically from the official FPL API.
    """
    try:
        # Official FPL API URL
        url = "https://fantasy.premierleague.com/api/bootstrap-static/"
        response = requests.get(url)

        if response.status_code != 200:
            print("Failed to fetch data from the FPL API.")
            return None

        # Parse the JSON response
        data = response.json()

        # Find the current gameweek (is_current = True)
        for event in data["events"]:
            if event["is_current"]:
                return event["id"]

        # Fallback if no current gameweek is found
        print("No current gameweek found in the FPL data.")
        return None

    except Exception as e:
        print(f"Error fetching current gameweek: {str(e)}")
        return None
    

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

    # Send the GET request to the API
    response = requests.get(f"{API_BASE_URL}/players", params=params)

    

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
            print(f"Error parsing budget value: {words[i + 1]}")  

   
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


def extract_player_name_transfer(message):
    """
    Extract the player's name from transfer-related queries like "Should I buy Salah?"
    """
    # Remove punctuation and convert to lowercase
    clean_message = message.translate(str.maketrans("", "", string.punctuation)).lower()

    # Identify keywords before the player name
    keywords = ["buy", "sell", "hold", "recommend"]

    words = clean_message.split()
    for i, word in enumerate(words):
        if word in keywords and i + 1 < len(words):
            # Return the word(s) following the keyword as the player's name
            return " ".join(words[i + 1:]).capitalize()
    return None  # No player name found


def extract_player_name_prediction(message):
    """
    Extract the player's name from prediction-related queries like "Predict points for Saka in Gameweek 18."
    """
    # Remove punctuation and convert to lowercase
    clean_message = message.translate(str.maketrans("", "", string.punctuation)).lower()

    words = clean_message.split()
    for i, word in enumerate(words):
        if word == "for" and i + 1 < len(words):
            player_name_parts = []
            for j in range(i + 1, len(words)):
                if words[j] in ["in", "gameweek", "gw"]:  # Stop at boundary terms
                    break
                player_name_parts.append(words[j])
            if player_name_parts:
                return " ".join(player_name_parts).capitalize()
    return None  # No player name found


# def extract_player_name(message):
#     """
#     Extract the player's name from the user input.
#     Handles queries like "Should I buy Salah?"
#     """
#     # Remove punctuation and convert to lowercase
#     clean_message = message.translate(str.maketrans("", "", string.punctuation)).lower()

#     # Identify keywords before the player name
#     keywords = ["buy", "sell", "hold", "recommend"]

#     words = clean_message.split()
#     for i, word in enumerate(words):
#         if word in keywords and i + 1 < len(words):
#             # Return the word(s) following the keyword as the player's name
#             return " ".join(words[i + 1:]).capitalize()
#     return None  # No player name found




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


        # Search for the player in the buy, sell, and hold lists
        for category, players in recommendations.items():
            for player in players:
                # Normalize the player's name in the database
                player_name_in_db = player["name"].lower().replace(".", "").strip()
                
                
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
