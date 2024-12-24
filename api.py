# flask api to fetch data
# allows chatbot to query data from the database

from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

# helper to connect to db

def query_db(query, args=(), one=False):
    conn = sqlite3.connect("fpl_data.db")
    conn.row_factory = sqlite3.Row  # Return rows as dictionaries
    cur = conn.cursor()
    # Execute query
    cur.execute(query, args)
    rows = cur.fetchall()
    conn.close()
    # Return results
    return (rows[0] if rows else None) if one else rows