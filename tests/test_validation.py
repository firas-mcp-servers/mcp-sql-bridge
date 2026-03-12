import os
import sqlite3
from pathlib import Path

import pytest

from mcp_sql_bridge.server import _validate_db_path


def _make_sqlite_db(tmp_path: Path, name: str = "test.db") -> Path:
    db_path = tmp_path / name
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("CREATE TABLE items (id INTEGER PRIMARY KEY, name TEXT)")
        conn.commit()
    finally:
        conn.close()
    return db_path


def test_validate_db_path_nonexistent(tmp_path: Path) -> None:
    path = tmp_path / "does_not_exist.db"
    with pytest.raises(ValueError) as exc:
        _validate_db_path(str(path))
    assert "does not exist" in str(exc.value)


def test_validate_db_path_directory(tmp_path: Path) -> None:
    with pytest.raises(ValueError) as exc:
        _validate_db_path(str(tmp_path))
    assert "is not a file" in str(exc.value)


def test_validate_db_path_not_sqlite(tmp_path: Path) -> None:
    file_path = tmp_path / "not_db.txt"
    file_path.write_text("not a database", encoding="utf-8")
    with pytest.raises(ValueError) as exc:
        _validate_db_path(str(file_path))
    assert "does not appear to be a SQLite database" in str(exc.value)


def test_validate_db_path_allowed_dirs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    allowed = tmp_path / "allowed"
    disallowed = tmp_path / "disallowed"
    allowed.mkdir()
    disallowed.mkdir()

    allowed_db = _make_sqlite_db(allowed, "ok.db")
    disallowed_db = _make_sqlite_db(disallowed, "bad.db")

    monkeypatch.setenv("MCP_SQL_BRIDGE_DB_ALLOWED_DIRS", str(allowed))

    # Inside allowed dir → ok
    assert _validate_db_path(str(allowed_db)) == allowed_db.resolve()

    # Outside allowed dir → error
    with pytest.raises(ValueError) as exc:
        _validate_db_path(str(disallowed_db))
    assert "not within any allowed directory" in str(exc.value)

