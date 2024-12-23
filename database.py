import sqlite3

def setup_database():
    # Connect to SQLite database (or create it if it doesn't exist)
    conn = sqlite3.connect("fpl_data.db")
    cursor = conn.cursor()

    # Create Players table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Players (
        id INTEGER PRIMARY KEY,
        name TEXT,
        team_id INTEGER,
        position TEXT,
        cost REAL,
        form REAL,
        points INTEGER
    )
    """)

    # Create Teams table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Teams (
        id INTEGER PRIMARY KEY,
        name TEXT,
        strength_home INTEGER,
        strength_away INTEGER
    )
    """)

    # Create Fixtures table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Fixtures (
        gameweek INTEGER PRIMARY KEY,
        deadline_time TEXT,
        is_current BOOLEAN,
        is_next BOOLEAN
    )
    """)

    # Commit changes and close the connection
    conn.commit()
    conn.close()
    print("Database setup complete.")

if __name__ == "__main__":
    setup_database()
