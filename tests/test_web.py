import sys  # noqa: E402
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))  # noqa: E402

import os
import sqlite3

from web.app import app


def test_index_route(tmp_path):
    db_path = tmp_path / "netnews.db"
    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        CREATE TABLE news (
            id INTEGER PRIMARY KEY,
            feed TEXT,
            title TEXT,
            link TEXT,
            summary TEXT,
            created_date DATE
        )
        """
    )
    conn.execute(
        "INSERT INTO news (feed, title, link, summary) VALUES (?, ?, ?, ?)",
        ("test", "title", "link", "summary"),
    )
    conn.commit()
    conn.close()

    app.config["TESTING"] = True
    os.environ["DATABASE_PATH"] = str(db_path)
    with app.test_client() as client:
        resp = client.get("/")
    assert resp.status_code == 200
    assert b"title" in resp.data
