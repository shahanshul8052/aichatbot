import sqlite3

def setup_database():
    # Connect to SQLite database (or create it if it doesn't exist)
    conn = sqlite3.connect("fpl_data.db")
    cursor = conn.cursor()

    # Create table for teams
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Teams (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        strength_home INTEGER NOT NULL,
        strength_away INTEGER NOT NULL
    )
    """)

    # Create table for players
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Players (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        team_id INTEGER NOT NULL,
        position INTEGER NOT NULL,  -- 1: GK, 2: DEF, 3: MID, 4: FWD
        cost REAL NOT NULL,
        form REAL NOT NULL,
        points INTEGER NOT NULL,
        FOREIGN KEY(team_id) REFERENCES Teams(id)
    )
    """)

    # Commit changes and close the connection
    conn.commit()
    conn.close()
    print("Database setup complete. Tables created.")

if __name__ == "__main__":
    setup_database()
