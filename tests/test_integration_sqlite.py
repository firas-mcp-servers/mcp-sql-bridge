"""Integration-style tests: full list_tables + execute_readonly_query flow on SQLite."""

import sqlite3
from pathlib import Path

from mcp_sql_bridge.server import _execute_readonly_query_impl, _list_tables_impl


def _make_db(tmp_path: Path) -> Path:
    db_path = tmp_path / "integration.db"
    conn = sqlite3.connect(db_path)
    try:
        conn.executescript("""
            CREATE TABLE products (id INTEGER PRIMARY KEY, name TEXT, price REAL);
            CREATE TABLE sales (id INTEGER PRIMARY KEY, product_id INTEGER, qty INTEGER);
            INSERT INTO products (id, name, price) VALUES (1, 'Widget', 9.99), (2, 'Gadget', 19.99);
            INSERT INTO sales (id, product_id, qty) VALUES (1, 1, 10), (2, 2, 5);
        """)
        conn.commit()
    finally:
        conn.close()
    return db_path


def test_integration_list_then_query(tmp_path: Path) -> None:
    """List tables then run a SELECT that joins; validates full SQLite path."""
    db_path = _make_db(tmp_path)
    schema = _list_tables_impl(str(db_path))
    assert "products" in schema
    assert "sales" in schema
    assert "name" in schema and "price" in schema

    out = _execute_readonly_query_impl(
        str(db_path),
        "SELECT p.name, s.qty FROM products p JOIN sales s ON p.id = s.product_id ORDER BY s.qty DESC",
    )
    assert "Widget" in out and "Gadget" in out
    assert "10" in out and "5" in out


def test_integration_backend_normalization(tmp_path: Path) -> None:
    """Explicit backend=sqlite works like default."""
    db_path = _make_db(tmp_path)
    out1 = _list_tables_impl(str(db_path))
    out2 = _list_tables_impl(str(db_path), backend="sqlite")
    assert out1 == out2
