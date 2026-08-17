import sqlite3
from datetime import datetime


DATABASE_NAME = "orders.db"


def create_database():
    connection = sqlite3.connect(DATABASE_NAME)

    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            order_id TEXT PRIMARY KEY,
            status TEXT,
            amount INTEGER,
            source TEXT,
            last_updated TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reconciliation_history (
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


def save_order(order):
    connection = sqlite3.connect(DATABASE_NAME)

    cursor = connection.cursor()

    cursor.execute("""
        INSERT OR REPLACE INTO orders
        (
            order_id,
            status,
            amount,
            source,
            last_updated
        )
        VALUES (?, ?, ?, ?, ?)
    """, (
        order["order_id"],
        order["status"],
        order["amount"],
        order["source"],
        order["last_updated"]
    ))

    connection.commit()
    connection.close()


def has_been_processed(input_hash):
    connection = sqlite3.connect(DATABASE_NAME)

    cursor = connection.cursor()

    cursor.execute("""
        SELECT 1
        FROM reconciliation_history
        WHERE input_hash = ?
    """, (
        input_hash,
    ))

    result = cursor.fetchone()

    connection.close()

    return result is not None


def save_reconciliation_history(
    order_id,
    action,
    reason,
    input_hash
):
    connection = sqlite3.connect(DATABASE_NAME)

    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO reconciliation_history
        (
            order_id,
            action,
            reason,
            input_hash,
            processed_time
        )
        VALUES (?, ?, ?, ?, ?)
    """, (
        order_id,
        action,
        reason,
        input_hash,
        datetime.now().isoformat()
    ))

    connection.commit()
    connection.close()