import sqlite3
from pathlib import Path

import pytest

from mcp_sql_bridge.server import _execute_readonly_query_impl


def _make_db(tmp_path: Path) -> Path:
    db_path = tmp_path / "data.db"
    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(
            """
            CREATE TABLE items (
                id INTEGER PRIMARY KEY,
                name TEXT
            );
            INSERT INTO items (name) VALUES ('a'), ('b'), ('c'), ('d');
            """
        )
        conn.commit()
    finally:
        conn.close()
    return db_path


def test_execute_readonly_query_simple_select(tmp_path: Path) -> None:
    db_path = _make_db(tmp_path)
    out = _execute_readonly_query_impl(str(db_path), "SELECT id, name FROM items ORDER BY id")
    assert "id" in out and "name" in out
    assert "a" in out and "d" in out


def test_execute_readonly_query_rejects_non_select(tmp_path: Path) -> None:
    db_path = _make_db(tmp_path)
    with pytest.raises(ValueError) as exc:
        _execute_readonly_query_impl(str(db_path), "UPDATE items SET name = 'x'")
    assert "Only SELECT queries are allowed" in str(exc.value)


def test_execute_readonly_query_truncates_rows(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    db_path = _make_db(tmp_path)
    # Force a tiny row limit
    monkeypatch.setenv("MCP_SQL_BRIDGE_MAX_ROWS", "2")
    out = _execute_readonly_query_impl(str(db_path), "SELECT id, name FROM items ORDER BY id")
    # We inserted 4 rows, but should only see 2 plus truncation note
    assert "results truncated to 2 rows" in out


def test_execute_readonly_query_truncates_bytes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    db_path = _make_db(tmp_path)
    # Very small byte limit to force truncation
    monkeypatch.setenv("MCP_SQL_BRIDGE_MAX_BYTES", "50")
    out = _execute_readonly_query_impl(str(db_path), "SELECT id, name FROM items ORDER BY id")
    assert "[output truncated due to size limit]" in out
