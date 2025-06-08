import os
import sqlite3
from datetime import date

from flask import Flask, render_template

app = Flask(__name__)


@app.route('/')
def hello_world():
    """
    This function is the main route of the Flask application.
    It connects to a SQLite database, executes a SQL query to fetch all records from the current date,
    and then passes the fetched rows to a template for rendering.
    """
    # Connect to the SQLite database
    # Try to connect to the database in the current directory first, then fall back to parent directory
    if os.path.exists('/netnews/netnews.db'):
        conn = sqlite3.connect('/netnews/netnews.db')
    else:
        conn = sqlite3.connect('../netnews.db')

    # Create a cursor
    cur = conn.cursor()

    # Write a SQL query to fetch all records from today
    # Replace 'table_name' and 'date_column' with your actual table name and date column name
    query = f"SELECT * FROM news WHERE date(created_date) = date('{date.today()}')"

    # Execute the SQL query
    cur.execute(query)

    # Fetch all rows
    summaries = cur.fetchall()

    # Close the connection
    conn.close()

    # Pass the fetched rows to the render_template function
    return render_template('the_news.html', summaries=summaries)


if __name__ == '__main__':
    """
    This conditional is used to check whether this module is being run directly or imported. 
    If it is run directly, it starts the Flask application on port 8080.
    """
    app.run(host='0.0.0.0', port=8080)
