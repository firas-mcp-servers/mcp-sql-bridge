#!/usr/bin/env python3
"""Create examples/sample.db with a minimal schema for demos and testing."""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "sample.db"


def main() -> None:
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                created_at TEXT
            );
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                total REAL NOT NULL,
                created_at TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
            INSERT OR IGNORE INTO users (id, name, created_at) VALUES
                (1, 'Alice', datetime('now')),
                (2, 'Bob', datetime('now'));
            INSERT OR IGNORE INTO orders (id, user_id, total, created_at) VALUES
                (1, 1, 29.99, datetime('now')),
                (2, 1, 14.50, datetime('now')),
                (3, 2, 99.00, datetime('now'));
        """)
        conn.commit()
        print(f"Created {DB_PATH}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
