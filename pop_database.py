import sqlite3
from data_collection import fetch_fpl_data

def pop_db():
    data = fetch_fpl_data()
    if not data: 
        print("No data to populate database")
        return
    
    conn = sqlite3.connect('fpl_data.db')
    cursor = conn.cursor()