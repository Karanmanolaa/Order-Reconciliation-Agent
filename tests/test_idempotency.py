import sqlite3
import sys
import os

sys.path.append(
    os.path.dirname(
        os.path.dirname(__file__)
    )
)

import database

from database import (
    save_reconciliation_history,
    has_been_processed
)


def test_same_reconciliation_is_not_processed_twice(tmp_path):

    database_file = tmp_path / "orders.db"
    database.DATABASE_NAME = str(database_file)

    connection = sqlite3.connect(database_file)

    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE reconciliation_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id TEXT,
            action TEXT,
            reason TEXT,
            input_hash TEXT UNIQUE,
            processed_time TEXT
        )
    """)

    connection.commit()
    connection.close()

    input_hash = "abc123"

    save_reconciliation_history(
        "ORD001",
        "ACCEPT_LIVE",
        "Live update was newer",
        input_hash
    )

    assert has_been_processed(input_hash) is True

    # Trying to process the same reconciliation again should be detected
    assert has_been_processed(input_hash) is True

    connection = sqlite3.connect(database_file)

    cursor = connection.cursor()

    cursor.execute("""
        SELECT COUNT(*)
        FROM reconciliation_history
        WHERE input_hash = ?
    """, (
        input_hash,
    ))

    count = cursor.fetchone()[0]

    connection.close()

    assert count == 1