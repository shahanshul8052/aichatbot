import sqlite3
from data_collection import fetch_fpl_data 
# live fetch

def populate_database():
    # Fetch data from FPL API
    data = fetch_fpl_data()
    if not data:
        print("Failed to fetch data. Exiting.")
        return

    # Connect to SQLite database
    conn = sqlite3.connect("fpl_data.db")
    cursor = conn.cursor()

    # 1: GK, 2: DEF, 3: MID, 4: FWD

    # Populate Players table
    players = data["players"]
    for player in players:
        cursor.execute("""
        INSERT OR REPLACE INTO Players (id, name, team_id, position, cost, form, points)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            player["id"],
            player["web_name"],
            player["team"],
            player["element_type"],  # 1: GK, 2: DEF, 3: MID, 4: FWD
            player["now_cost"] / 10,  # Convert cost to float
            float(player["form"]),
            player["total_points"]
        ))

    # Populate Teams table
    teams = data["teams"]
    for team in teams:
        cursor.execute("""
        INSERT OR REPLACE INTO Teams (id, name, strength_home, strength_away)
        VALUES (?, ?, ?, ?)
        """, (
            team["id"],
            team["name"],
            team["strength_overall_home"],
            team["strength_overall_away"]
        ))

    # Populate Fixtures table
    fixtures = data["fixtures"]
    for fixture in fixtures:
        cursor.execute("""
        INSERT OR REPLACE INTO Fixtures (gameweek, deadline_time, is_current, is_next)
        VALUES (?, ?, ?, ?)
        """, (
            fixture["id"],
            fixture["deadline_time"],
            fixture["is_current"],
            fixture["is_next"]
        ))

    # Commit changes and close the connection
    conn.commit()
    conn.close()
    print("Database populated successfully.")

if __name__ == "__main__":
    populate_database()
