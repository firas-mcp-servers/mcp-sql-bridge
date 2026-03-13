"""Basic performance sanity: queries complete within a reasonable time."""

import sqlite3
import time
from pathlib import Path

from mcp_sql_bridge.server import _execute_readonly_query_impl


def _make_large_db(tmp_path: Path, rows: int = 2000) -> Path:
    db_path = tmp_path / "perf.db"
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("CREATE TABLE t (id INTEGER PRIMARY KEY, x INTEGER)")
        conn.executemany("INSERT INTO t (id, x) VALUES (?, ?)", [(i, i * 2) for i in range(rows)])
        conn.commit()
    finally:
        conn.close()
    return db_path


def test_execute_readonly_query_completes_quickly(tmp_path: Path) -> None:
    """Execute a medium-sized result set; should finish in under 5 seconds."""
    db_path = _make_large_db(tmp_path)
    start = time.monotonic()
    out = _execute_readonly_query_impl(str(db_path), "SELECT id, x FROM t ORDER BY id LIMIT 500")
    elapsed = time.monotonic() - start
    assert "id" in out and "x" in out
    assert elapsed < 5.0, f"Query took {elapsed:.2f}s (expected < 5s)"
