import os
import sqlite3
from datetime import date

from flask import Flask, render_template

app = Flask(__name__)


@app.route("/")
def hello_world():
    """Display today's news entries from the SQLite database."""
    # Connect to the SQLite database
    db_path = os.getenv("DATABASE_PATH")
    if db_path and os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
    elif os.path.exists("/netnews/netnews.db"):
        conn = sqlite3.connect("/netnews/netnews.db")
    else:
        conn = sqlite3.connect("../netnews.db")

    # Create a cursor
    cur = conn.cursor()

    # Write a SQL query to fetch all records from today
    # Query the 'news' table for entries with today's date in the 'created_date' column
    query = "SELECT * FROM news WHERE date(created_date) = date(?)"

    # Execute the SQL query
    cur.execute(query, (date.today(),))

    # Fetch all rows
    summaries = cur.fetchall()

    # Close the connection
    conn.close()

    # Pass the fetched rows to the render_template function
    return render_template("the_news.html", summaries=summaries)


if __name__ == "__main__":
    """
    This conditional is used to check whether this module is being run directly or imported.
    If it is run directly, it starts the Flask application on port 8080.
    """
    app.run(host="0.0.0.0", port=8080)
