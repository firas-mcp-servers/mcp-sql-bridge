import sqlite3
from pathlib import Path

from mcp_sql_bridge.server import _list_tables_impl


def _make_db(tmp_path: Path) -> Path:
    db_path = tmp_path / "schema.db"
    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(
            """
            CREATE TABLE users (
                id INTEGER PRIMARY KEY,
                name TEXT
            );
            CREATE TABLE orders (
                id INTEGER PRIMARY KEY,
                user_id INTEGER,
                total REAL
            );
            """
        )
        conn.commit()
    finally:
        conn.close()
    return db_path


def test_list_tables_includes_columns_and_create_table(tmp_path: Path) -> None:
    db_path = _make_db(tmp_path)
    output = _list_tables_impl(str(db_path))

    # Tables and columns
    assert "users" in output
    assert "orders" in output
    assert "id, name" in output
    assert "id, user_id, total" in output

    # CREATE TABLE statements
    assert "CREATE TABLE" in output
    assert "CREATE TABLE users" in output
    assert "CREATE TABLE orders" in output

