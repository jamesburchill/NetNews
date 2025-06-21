import sys  # noqa: E402
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))  # noqa: E402

import sqlite3
import tempfile
from datetime import datetime, timedelta

from core.main import cleanup_old_entries


def test_cleanup_old_entries():
    db = tempfile.NamedTemporaryFile()
    conn = sqlite3.connect(db.name)
    conn.execute("CREATE TABLE news (id INTEGER PRIMARY KEY, created_date DATE)")
    today = datetime.now().strftime("%Y-%m-%d")
    old_day = (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d")
    conn.executemany(
        "INSERT INTO news (created_date) VALUES (?)",
        [(today,), (old_day,)],
    )
    conn.commit()

    removed = cleanup_old_entries(conn, days_to_keep=5)
    remaining = conn.execute("SELECT COUNT(*) FROM news").fetchone()[0]
    conn.close()
    assert removed == 1
    assert remaining == 1
