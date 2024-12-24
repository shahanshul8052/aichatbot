import sqlite3
from data_collection import fetch_fpl_data  # Live fetch

def populate_database():
    # Fetch data from FPL API
    data = fetch_fpl_data()
    if not data:
        print("Failed to fetch data. Exiting.")
        return

    # Connect to SQLite database
    conn = sqlite3.connect("fpl_data.db")
    cursor = conn.cursor()

    try:
        # Populate Teams table
        teams = data["teams"]
        for team in teams:
            cursor.execute("""
            INSERT OR REPLACE INTO Teams (id, name, strength_home, strength_away)
            VALUES (?, ?, ?, ?)
            """, (
                team["id"],                          # Team ID from API
                team["name"],                        # Team name
                team["strength_overall_home"],       # Home strength
                team["strength_overall_away"]        # Away strength
            ))
        print(f"Populated Teams table with {len(teams)} entries.")

        # Populate Players table
        players = data["players"]
        for player in players:
            cursor.execute("""
            INSERT OR REPLACE INTO Players (id, name, team_id, position, cost, form, points)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                player["id"],                        # Player ID
                player["web_name"],                  # Player name
                player["team"],                      # Team ID
                player["element_type"],              # 1: GK, 2: DEF, 3: MID, 4: FWD
                player["now_cost"] / 10,             # Cost in millions
                float(player["form"]),               # Form
                player["total_points"]               # Total points
            ))
        print(f"Populated Players table with {len(players)} entries.")

        # Commit changes to the database
        conn.commit()
        print("Database populated successfully.")

    except Exception as e:
        print(f"Error populating database: {e}")

    finally:
        conn.close()

if __name__ == "__main__":
    populate_database()
