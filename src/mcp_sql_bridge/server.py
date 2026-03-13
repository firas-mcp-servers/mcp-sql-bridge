"""MCP SQL Bridge server entry point."""

from __future__ import annotations

import json
import logging
import os
import re
import sqlite3
import sys
import uuid
from collections.abc import Sequence
from contextvars import ContextVar
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlparse

import anyio
import mcp.types as types
from mcp.server import NotificationOptions, Server
from mcp.server.lowlevel.helper_types import ReadResourceContents
from mcp.server.stdio import stdio_server
from pydantic import AnyUrl

SERVER_NAME = "Local-SQL-Insight"

# SQLite magic header (first 16 bytes of a valid SQLite3 database file)
SQLITE_MAGIC = b"SQLite format 3\x00"

# Defaults for result limiting
DEFAULT_MAX_ROWS = 500
DEFAULT_MAX_BYTES: int | None = None  # Unlimited by default

# URI for the static README template resource
README_TEMPLATE_URI = "mcp-sql-bridge://readme-template"

logger = logging.getLogger("mcp_sql_bridge")

# Optional request ID for observability (set at tool/resource entry)
_request_id: ContextVar[str | None] = ContextVar("request_id", default=None)

# Error categories for AI-friendly messages (see docs/ERROR_TAXONOMY.md)
ERR_VALIDATION = "Validation"
ERR_CONNECTION = "Connection"
ERR_QUERY = "Query"
ERR_RESOURCE = "Resource"
ERR_TOOL = "Tool"


def _redact_connection_string(url: str) -> str:
    """Redact password from a connection URL for safe logging."""
    try:
        p = urlparse(url)
        if p.password:
            netloc = f"{p.username or ''}:***@{p.hostname or ''}:{p.port or ''}"
        else:
            netloc = f"{p.hostname or ''}:{p.port or ''}"
        return f"{p.scheme}://{netloc}{(p.path or '')}"
    except Exception:
        return "***"


def _err(message: str, category: str = ERR_VALIDATION) -> str:
    """Return a consistent, actionable error message with optional category prefix."""
    return f"[{category}] {message}"


def _utc_iso_now() -> str:
    return datetime.now(UTC).isoformat()


def _log(event: str, level: str = "info", **extra: object) -> None:
    """Structured logging helper that always logs to stderr as a single JSON line."""
    record = {
        "ts": _utc_iso_now(),
        "level": level,
        "event": event,
        **extra,
    }
    rid = _request_id.get()
    if rid is not None:
        record["request_id"] = rid
    try:
        line = json.dumps(record, ensure_ascii=False)
    except Exception:
        line = str(record)
    # Use the logger so hosts can still control logging if desired
    logger.log(
        getattr(logging, level.upper(), logging.INFO),
        line,
    )


# Bounds for MAX_ROWS (config hardening)
MAX_ROWS_LIMIT = 50_000


def _get_max_rows_from_env() -> int:
    value = os.getenv("MCP_SQL_BRIDGE_MAX_ROWS")
    if not value:
        return DEFAULT_MAX_ROWS
    try:
        parsed = int(value)
        if parsed <= 0:
            return DEFAULT_MAX_ROWS
        return min(parsed, MAX_ROWS_LIMIT)
    except ValueError:
        return DEFAULT_MAX_ROWS


def _get_max_bytes_from_env() -> int | None:
    value = os.getenv("MCP_SQL_BRIDGE_MAX_BYTES")
    if not value:
        return DEFAULT_MAX_BYTES
    try:
        parsed = int(value)
    except ValueError:
        return DEFAULT_MAX_BYTES
    return parsed if parsed > 0 else DEFAULT_MAX_BYTES


def _get_allowed_dirs_from_env() -> list[Path]:
    raw = os.getenv("MCP_SQL_BRIDGE_DB_ALLOWED_DIRS")
    if not raw:
        return []
    parts = [p for p in raw.split(os.pathsep) if p.strip()]
    return [Path(p).expanduser().resolve() for p in parts]


def _enforce_allowed_dirs(path: Path) -> None:
    """Ensure that path is under one of the allowed base directories, if configured."""
    allowed_dirs = _get_allowed_dirs_from_env()
    if not allowed_dirs:
        return

    for base in allowed_dirs:
        try:
            # Python 3.11+ Path.is_relative_to
            if path.is_relative_to(base):
                return
        except ValueError:
            # Fallback if path / base are on different drives on Windows, etc.
            continue

    allowed_str = ", ".join(str(d) for d in allowed_dirs)
    raise ValueError(
        f"The database path {path} is not within any allowed directory.\n"
        f"Allowed base directories (MCP_SQL_BRIDGE_DB_ALLOWED_DIRS): {allowed_str}"
    )


def _validate_db_path(db_path: str) -> Path:
    """Validate that the path exists, is a file, and is a valid SQLite database.
    Returns the resolved Path on success.
    Raises ValueError with a clear message on failure.
    """
    path = Path(db_path).expanduser().resolve()
    _enforce_allowed_dirs(path)
    if not path.exists():
        raise ValueError(
            f"The path does not exist: {path}\n"
            "Please provide an absolute or relative path to an existing SQLite database file."
        )
    if not path.is_file():
        raise ValueError(
            f"The path is not a file: {path}\n"
            "Please provide a path to a file (e.g. .db or .sqlite), not a directory."
        )
    try:
        with open(path, "rb") as f:
            header = f.read(16)
    except OSError as e:
        raise ValueError(
            f"Cannot read the file: {path}\n"
            f"System error: {e}\n"
            "Ensure the file is readable and not locked by another process."
        ) from e
    if header != SQLITE_MAGIC:
        raise ValueError(
            f"The file does not appear to be a SQLite database: {path}\n"
            "SQLite database files start with the magic bytes 'SQLite format 3'. "
            "Please provide a path to a valid .db or .sqlite file."
        )
    return path


def _normalize_backend(backend: str | None) -> str:
    """Normalize backend identifiers and validate."""
    if backend is None or backend == "":
        return "sqlite"
    value = backend.strip().lower()
    if value not in {"sqlite", "postgres", "mysql"}:
        raise ValueError(
            f"Unsupported backend: {backend!r}. Supported backends are: sqlite, postgres, mysql."
        )
    return value


def _parse_mysql_url(url: str) -> dict:
    """Parse a basic MySQL URL into connection kwargs for PyMySQL."""
    parsed = urlparse(url)
    if parsed.scheme not in {"mysql", "mariadb"}:
        raise ValueError("MySQL connection_string must use mysql:// or mariadb:// URL format.")
    if not parsed.path or parsed.path == "/":
        raise ValueError("MySQL URL must include a database name in the path.")
    db_name = parsed.path.lstrip("/")
    return {
        "host": parsed.hostname or "localhost",
        "port": parsed.port or 3306,
        "user": parsed.username or "",
        "password": parsed.password or "",
        "database": db_name,
    }


def _readme_path() -> Path:
    """Path to README.md in the current working directory."""
    return Path.cwd().resolve() / "README.md"


def _readme_uri() -> str:
    """URI for the local README resource (file:// so it validates as AnyUrl)."""
    return _readme_path().as_uri()


def _is_readme_uri(uri: AnyUrl | str) -> bool:
    """True if the URI refers to the local README resource."""
    s = str(uri).rstrip("/")
    return s == _readme_uri() or s == _readme_uri().rstrip("/")


def _is_readme_template_uri(uri: AnyUrl | str) -> bool:
    """True if the URI refers to the static README template resource."""
    return str(uri).rstrip("/") == README_TEMPLATE_URI


def _readme_template_content() -> str:
    """Static template text for per-database README files."""
    return (
        "# Database README template\n\n"
        "Use this template to document the business context and conventions for a specific database.\n\n"
        "## Overview\n"
        "- Database name: <fill in>\n"
        "- Primary use cases: <analytics / product / logging / etc>\n"
        "- Owners / team: <who maintains this DB>\n\n"
        "## Conventions\n"
        "- Naming patterns (tables, columns, enums)\n"
        "- Timezone rules\n"
        "- Soft-delete flags\n\n"
        "## Key tables\n"
        "- <table_name>: short description\n"
        "- <table_name>: short description\n\n"
        "## Gotchas\n"
        "- Known quirks, legacy fields, or privacy constraints\n"
    )


def _format_table(
    col_names: Sequence[str],
    rows: Sequence[Sequence[object]],
) -> tuple[str, int, int, bool]:
    """Format rows into a text table and apply row/byte limits.

    Returns (text, original_row_count, returned_row_count, truncated_rows_flag).
    """
    if not col_names:
        return "(No columns returned)", 0, 0, False

    max_rows = _get_max_rows_from_env()
    original_row_count = len(rows)
    truncated_rows = False
    if original_row_count > max_rows:
        rows = rows[:max_rows]
        truncated_rows = True

    widths = [max(len(str(col)), 2) for col in col_names]
    for row in rows:
        for i, cell in enumerate(row):
            if i < len(widths):
                widths[i] = max(
                    widths[i],
                    len(str(cell) if cell is not None else "NULL"),
                )

    sep = "+" + "+".join("-" * (w + 2) for w in widths) + "+"
    lines = [sep]
    lines.append("| " + " | ".join(str(c).ljust(widths[i]) for i, c in enumerate(col_names)) + " |")
    lines.append(sep)
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                (str(cell) if cell is not None else "NULL").ljust(widths[i])
                for i, cell in enumerate(row)
            )
            + " |"
        )
    lines.append(sep)
    result = "\n".join(lines)

    max_bytes = _get_max_bytes_from_env()
    truncated_bytes = False
    if max_bytes is not None and len(result.encode("utf-8")) > max_bytes:
        encoded = result.encode("utf-8")
        truncated = encoded[:max_bytes]
        try:
            result = truncated.decode("utf-8", errors="ignore")
        finally:
            truncated_bytes = True
        result += "\n…\n[output truncated due to size limit]"

    if truncated_rows:
        result += (
            f"\n\n[results truncated to {max_rows} rows; "
            f"original result had at least {original_row_count} rows]"
        )

    return result, original_row_count, len(rows), truncated_bytes


def _list_tables_sqlite(db_path: str) -> str:
    """Return a list of all tables, their column names, and CREATE TABLE statements for SQLite."""
    path = _validate_db_path(db_path)
    try:
        conn = sqlite3.connect(path, uri=False)
    except sqlite3.Error as e:
        _log("list_tables_db_open_error", level="error", db_path=path.name, error=str(e))
        raise ValueError(
            f"Could not open the database: {path}\n"
            f"SQLite error: {e}\n"
            "The file may be corrupted or in use by another process."
        ) from e
    try:
        cursor = conn.execute(
            "SELECT name, sql FROM sqlite_master "
            "WHERE type = 'table' AND name NOT LIKE 'sqlite_%' "
            "ORDER BY name"
        )
        rows = cursor.fetchall()
        if not rows:
            _log("list_tables_no_tables", level="info", db_path=path.name)
            return "The database contains no user tables."
        lines = []
        for table_name, create_sql in rows:
            cursor = conn.execute(f"PRAGMA table_info({table_name!r})")
            columns = [row[1] for row in cursor.fetchall()]
            lines.append(f"• {table_name}: {', '.join(columns)}")
            if create_sql:
                lines.append(f"  CREATE TABLE:\n  {create_sql}")
            lines.append("")
        result = "\n".join(lines).strip()
        _log(
            "list_tables_success",
            level="info",
            db_path=path.name,
            table_count=len(rows),
        )
        return result
    finally:
        conn.close()


def _pg_build_create_table_from_info_schema(
    cur: object,
    schema: str,
    table: str,
) -> str | None:
    """Build a best-effort CREATE TABLE from information_schema when pg_get_tabledef is unavailable."""
    try:
        cur.execute(
            """
            SELECT column_name, data_type, character_maximum_length,
                   numeric_precision, numeric_scale, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_schema = %s AND table_name = %s
            ORDER BY ordinal_position
            """,
            (schema, table),
        )
        rows = cur.fetchall()
    except Exception:
        return None
    if not rows:
        return None
    parts: list[str] = []
    for row in rows:
        col_name, data_type, char_max, num_prec, num_scale, is_nullable, col_default = row
        safe_name = f'"{col_name}"' if col_name else ""
        if data_type == "character varying" and char_max:
            type_str = f"character varying({char_max})"
        elif data_type == "numeric" and (num_prec is not None or num_scale is not None):
            type_str = f"numeric({num_prec or 0},{num_scale or 0})"
        else:
            type_str = data_type or "unknown"
        null_str = "" if is_nullable == "YES" else " NOT NULL"
        default_str = f" DEFAULT {col_default}" if col_default else ""
        parts.append(f"  {safe_name} {type_str}{null_str}{default_str}")
    qualified = f'"{schema}"."{table}"' if schema else f'"{table}"'
    return f"CREATE TABLE {qualified}(\n" + ",\n".join(parts) + "\n);"


def _list_tables_postgres(connection_string: str) -> str:
    """List tables and columns for a PostgreSQL database."""
    try:
        import psycopg  # type: ignore[import]
    except ImportError as e:  # pragma: no cover - depends on optional extra
        raise ValueError(
            "PostgreSQL support requires the 'psycopg' package. "
            "Install it with the appropriate optional dependency/extras."
        ) from e
    try:
        conn = psycopg.connect(connection_string)
    except psycopg.Error as e:
        _log(
            "list_tables_pg_connect_error",
            level="error",
            connection=_redact_connection_string(connection_string),
            error=str(e),
        )
        raise ValueError(
            _err(
                "Could not connect to PostgreSQL. "
                f"Connection error: {e}. "
                "Verify host, database name, and credentials.",
                ERR_CONNECTION,
            )
        ) from e
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT table_schema, table_name
            FROM information_schema.tables
            WHERE table_type = 'BASE TABLE'
              AND table_schema NOT IN ('pg_catalog', 'information_schema')
            ORDER BY table_schema, table_name
            """
        )
        tables = cur.fetchall()
        if not tables:
            _log("list_tables_pg_no_tables", level="info")
            return "The database contains no user tables."

        lines: list[str] = []
        for schema, table in tables:
            cur.execute(
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = %s AND table_name = %s
                ORDER BY ordinal_position
                """,
                (schema, table),
            )
            columns = [row[0] for row in cur.fetchall()]

            create_sql: str | None = None
            try:
                cur.execute(
                    """
                    SELECT pg_get_tabledef(c.oid)
                    FROM pg_class c
                    JOIN pg_namespace n ON n.oid = c.relnamespace
                    WHERE n.nspname = %s AND c.relname = %s AND c.relkind = 'r'
                    """,
                    (schema, table),
                )
                ddl_row = cur.fetchone()
                if ddl_row and ddl_row[0]:
                    create_sql = ddl_row[0]
            except Exception as e:  # pragma: no cover - optional helper
                _log(
                    "list_tables_pg_ddl_error",
                    level="warning",
                    schema=schema,
                    table=table,
                    error=str(e),
                )

            if not create_sql:
                create_sql = _pg_build_create_table_from_info_schema(cur, schema, table)

            lines.append(f"• {schema}.{table}: {', '.join(columns)}")
            if create_sql:
                lines.append(f"  CREATE TABLE:\n  {create_sql}")
            else:
                lines.append(
                    "  CREATE TABLE definition unavailable "
                    "(pg_get_tabledef extension may not be installed)."
                )
            lines.append("")

        result = "\n".join(lines).strip()
        _log(
            "list_tables_pg_success",
            level="info",
            table_count=len(tables),
        )
        return result
    finally:
        conn.close()


def _list_tables_mysql(connection_string: str) -> str:
    """List tables and columns for a MySQL database."""
    try:
        import pymysql  # type: ignore[import]
    except ImportError as e:  # pragma: no cover - depends on optional extra
        raise ValueError(
            "MySQL support requires the 'pymysql' package. "
            "Install it with the appropriate optional dependency/extras."
        ) from e
    kwargs = _parse_mysql_url(connection_string)
    try:
        conn = pymysql.connect(**kwargs)
    except pymysql.MySQLError as e:
        _log(
            "list_tables_mysql_connect_error",
            level="error",
            host=kwargs.get("host"),
            database=kwargs.get("database"),
            error=str(e),
        )
        raise ValueError(
            "Could not connect to MySQL.\n"
            f"Connection error: {e}\n"
            "Verify host, database name, and credentials."
        ) from e
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT TABLE_NAME
            FROM information_schema.tables
            WHERE TABLE_TYPE = 'BASE TABLE'
              AND TABLE_SCHEMA = DATABASE()
            ORDER BY TABLE_NAME
            """
        )
        tables = [row[0] for row in cur.fetchall()]
        if not tables:
            _log("list_tables_mysql_no_tables", level="info")
            return "The database contains no user tables."

        lines: list[str] = []
        for table in tables:
            cur.execute(
                """
                SELECT COLUMN_NAME
                FROM information_schema.columns
                WHERE TABLE_SCHEMA = DATABASE()
                  AND TABLE_NAME = %s
                ORDER BY ORDINAL_POSITION
                """,
                (table,),
            )
            columns = [row[0] for row in cur.fetchall()]

            create_sql: str | None = None
            try:
                cur.execute(f"SHOW CREATE TABLE `{table}`")
                ddl_row = cur.fetchone()
                if ddl_row and len(ddl_row) >= 2:
                    create_sql = ddl_row[1]
            except pymysql.MySQLError as e:  # pragma: no cover - optional helper
                _log(
                    "list_tables_mysql_ddl_error",
                    level="warning",
                    table=table,
                    error=str(e),
                )

            lines.append(f"• {table}: {', '.join(columns)}")
            if create_sql:
                lines.append(f"  CREATE TABLE:\n  {create_sql}")
            else:
                lines.append("  CREATE TABLE definition unavailable.")
            lines.append("")

        result = "\n".join(lines).strip()
        _log(
            "list_tables_mysql_success",
            level="info",
            table_count=len(tables),
        )
        return result
    finally:
        conn.close()


def _list_tables_impl(
    db_path: str,
    backend: str = "sqlite",
    connection_string: str | None = None,
) -> str:
    """Return a list of all tables, their column names, and CREATE TABLE statements."""
    normalized = _normalize_backend(backend)
    if normalized == "sqlite":
        return _list_tables_sqlite(db_path)
    if normalized == "postgres":
        if not connection_string:
            raise ValueError(
                "connection_string (PostgreSQL URL) is required when backend='postgres'."
            )
        return _list_tables_postgres(connection_string)
    if normalized == "mysql":
        if not connection_string:
            raise ValueError("connection_string (MySQL URL) is required when backend='mysql'.")
        return _list_tables_mysql(connection_string)
    # _normalize_backend already validates, so this is defensive only.
    raise ValueError(f"Unsupported backend: {backend!r}")


def _execute_readonly_query_sqlite(db_path: str, query: str) -> tuple[str, int, int, bool]:
    path = _validate_db_path(db_path)
    try:
        conn = sqlite3.connect(path, uri=False)
    except sqlite3.Error as e:
        _log("execute_query_db_open_error", level="error", db_path=path.name, error=str(e))
        raise ValueError(f"Could not open the database: {path}\nSQLite error: {e}") from e
    try:
        cursor = conn.execute(query)
        rows = cursor.fetchall()
        col_names = [d[0] for d in cursor.description] if cursor.description else []
    except sqlite3.Error as e:
        _log(
            "execute_query_sql_error",
            level="error",
            db_path=path.name,
            error=str(e),
            query_preview=query[:200],
        )
        raise ValueError(_err(f"Query failed: {e}", ERR_QUERY)) from e
    finally:
        conn.close()

    text, original_row_count, returned_rows, truncated_bytes = _format_table(
        col_names,
        rows,
    )
    _log(
        "execute_query_success",
        level="info",
        db_path=path.name,
        row_count=original_row_count,
        returned_rows=returned_rows,
        truncated_rows=original_row_count != returned_rows,
        truncated_bytes=truncated_bytes,
    )
    return text, original_row_count, returned_rows, truncated_bytes


def _execute_readonly_query_postgres(
    connection_string: str, query: str
) -> tuple[str, int, int, bool]:
    try:
        import psycopg  # type: ignore[import]
    except ImportError as e:  # pragma: no cover - depends on optional extra
        raise ValueError(
            "PostgreSQL support requires the 'psycopg' package. "
            "Install it with the appropriate optional dependency/extras."
        ) from e
    try:
        conn = psycopg.connect(connection_string)
    except psycopg.Error as e:
        _log(
            "execute_query_pg_connect_error",
            level="error",
            connection=_redact_connection_string(connection_string),
            error=str(e),
        )
        raise ValueError(
            _err(
                "Could not connect to PostgreSQL. "
                f"Connection error: {e}. "
                "Verify host, database name, and credentials.",
                ERR_CONNECTION,
            )
        ) from e
    try:
        cur = conn.cursor()
        try:
            cur.execute("SET SESSION CHARACTERISTICS AS TRANSACTION READ ONLY;")
        except Exception as e:  # pragma: no cover - best-effort safety
            _log(
                "execute_query_pg_readonly_warning",
                level="warning",
                error=str(e),
            )
        cur.execute(query)
        rows = cur.fetchall()
        col_names = [d[0] for d in cur.description] if cur.description else []
    except psycopg.Error as e:
        _log(
            "execute_query_pg_sql_error",
            level="error",
            error=str(e),
            query_preview=query[:200],
        )
        raise ValueError(_err(f"Query failed: {e}", ERR_QUERY)) from e
    finally:
        conn.close()

    text, original_row_count, returned_rows, truncated_bytes = _format_table(
        col_names,
        rows,
    )
    _log(
        "execute_query_pg_success",
        level="info",
        row_count=original_row_count,
        returned_rows=returned_rows,
        truncated_rows=original_row_count != returned_rows,
        truncated_bytes=truncated_bytes,
    )
    return text, original_row_count, returned_rows, truncated_bytes


def _execute_readonly_query_mysql(connection_string: str, query: str) -> tuple[str, int, int, bool]:
    try:
        import pymysql  # type: ignore[import]
    except ImportError as e:  # pragma: no cover - depends on optional extra
        raise ValueError(
            "MySQL support requires the 'pymysql' package. "
            "Install it with the appropriate optional dependency/extras."
        ) from e
    kwargs = _parse_mysql_url(connection_string)
    try:
        conn = pymysql.connect(**kwargs)
    except pymysql.MySQLError as e:
        _log(
            "execute_query_mysql_connect_error",
            level="error",
            host=kwargs.get("host"),
            database=kwargs.get("database"),
            error=str(e),
        )
        raise ValueError(
            _err(
                "Could not connect to MySQL. "
                f"Connection error: {e}. "
                "Verify host, database name, and credentials.",
                ERR_CONNECTION,
            )
        ) from e
    try:
        cur = conn.cursor()
        try:
            cur.execute("SET SESSION TRANSACTION READ ONLY")
        except pymysql.MySQLError as e:  # pragma: no cover - best-effort safety
            _log(
                "execute_query_mysql_readonly_warning",
                level="warning",
                error=str(e),
            )
        cur.execute(query)
        rows = cur.fetchall()
        col_names = [d[0] for d in cur.description] if cur.description else []
    except pymysql.MySQLError as e:
        _log(
            "execute_query_mysql_sql_error",
            level="error",
            error=str(e),
            query_preview=query[:200],
        )
        raise ValueError(_err(f"Query failed: {e}", ERR_QUERY)) from e
    finally:
        conn.close()

    text, original_row_count, returned_rows, truncated_bytes = _format_table(
        col_names,
        rows,
    )
    _log(
        "execute_query_mysql_success",
        level="info",
        row_count=original_row_count,
        returned_rows=returned_rows,
        truncated_rows=original_row_count != returned_rows,
        truncated_bytes=truncated_bytes,
    )
    return text, original_row_count, returned_rows, truncated_bytes


def _execute_readonly_query_impl(
    db_path: str,
    query: str,
    backend: str = "sqlite",
    connection_string: str | None = None,
) -> str:
    """Safely execute a SELECT query and return results as a formatted string."""
    q = query.strip()
    normalized_query = (
        re.sub(
            r"^[\s\n\r]*(--[^\n]*\n?|\/\*[\s\S]*?\*\/)*",
            "",
            q,
            flags=re.IGNORECASE,
        )
        .strip()
        .upper()
    )
    if not normalized_query.startswith("SELECT"):
        _log(
            "execute_query_rejected_non_select",
            level="warning",
            query_preview=q[:200],
        )
        raise ValueError(
            "Only SELECT queries are allowed for safety. "
            "Modifying the database (INSERT, UPDATE, DELETE, DDL) is not permitted."
        )

    backend_normalized = _normalize_backend(backend)

    if backend_normalized == "sqlite":
        text, original_row_count, returned_rows, truncated_bytes = _execute_readonly_query_sqlite(
            db_path,
            q,
        )
        db_identifier = _validate_db_path(db_path)
        db_info = {"db_path": str(db_identifier)}
    elif backend_normalized == "postgres":
        if not connection_string:
            raise ValueError(
                "connection_string (PostgreSQL URL) is required when backend='postgres'."
            )
        text, original_row_count, returned_rows, truncated_bytes = _execute_readonly_query_postgres(
            connection_string,
            q,
        )
        db_info = {"backend": "postgres"}
    elif backend_normalized == "mysql":
        if not connection_string:
            raise ValueError("connection_string (MySQL URL) is required when backend='mysql'.")
        text, original_row_count, returned_rows, truncated_bytes = _execute_readonly_query_mysql(
            connection_string,
            q,
        )
        db_info = {"backend": "mysql"}
    else:  # pragma: no cover - _normalize_backend already validates
        raise ValueError(f"Unsupported backend: {backend!r}")

    _log(
        "execute_query_success",
        level="info",
        row_count=original_row_count,
        returned_rows=returned_rows,
        truncated_rows=original_row_count != returned_rows,
        truncated_bytes=truncated_bytes,
        **db_info,
    )
    return text


def _create_server() -> Server:
    """Create and configure the MCP server with tools."""
    server = Server(SERVER_NAME)

    @server.list_tools()
    async def list_tools() -> list[types.Tool]:
        return [
            types.Tool(
                name="list_tables",
                description=(
                    "List all tables in a database (SQLite, PostgreSQL, or MySQL) "
                    "with their column names and full CREATE TABLE statements. "
                    "Use this to understand the full schema before writing queries."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "backend": {
                            "type": "string",
                            "enum": ["sqlite", "postgres", "mysql"],
                            "description": "Database backend. Defaults to 'sqlite' when omitted.",
                        },
                        "db_path": {
                            "type": "string",
                            "description": (
                                "Path to the SQLite database file (.db or .sqlite). "
                                "Required when backend is 'sqlite'."
                            ),
                        },
                        "connection_string": {
                            "type": "string",
                            "description": (
                                "PostgreSQL or MySQL connection URL. "
                                "Required when backend is 'postgres' or 'mysql'."
                            ),
                        },
                    },
                    "required": ["db_path"],
                },
            ),
            types.Tool(
                name="execute_readonly_query",
                description=(
                    "Safely execute a SELECT query on a database (SQLite, PostgreSQL, or MySQL) "
                    "and return the results as a formatted table."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "backend": {
                            "type": "string",
                            "enum": ["sqlite", "postgres", "mysql"],
                            "description": "Database backend. Defaults to 'sqlite' when omitted.",
                        },
                        "db_path": {
                            "type": "string",
                            "description": (
                                "Path to the SQLite database file. "
                                "Required when backend is 'sqlite'."
                            ),
                        },
                        "connection_string": {
                            "type": "string",
                            "description": (
                                "PostgreSQL or MySQL connection URL. "
                                "Required when backend is 'postgres' or 'mysql'."
                            ),
                        },
                        "query": {
                            "type": "string",
                            "description": "A SELECT query to run.",
                        },
                    },
                    "required": ["db_path", "query"],
                },
            ),
            types.Tool(
                name="schema_summary",
                description=(
                    "Return a compact schema summary (table names and key columns) "
                    "for a database. Use this when you need a quick overview instead "
                    "of full CREATE TABLE DDL."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "backend": {
                            "type": "string",
                            "enum": ["sqlite", "postgres", "mysql"],
                            "description": "Database backend. Defaults to 'sqlite' when omitted.",
                        },
                        "db_path": {
                            "type": "string",
                            "description": (
                                "Path to the SQLite database file (.db or .sqlite). "
                                "Required when backend is 'sqlite'."
                            ),
                        },
                        "connection_string": {
                            "type": "string",
                            "description": (
                                "PostgreSQL or MySQL connection URL. "
                                "Required when backend is 'postgres' or 'mysql'."
                            ),
                        },
                    },
                    "required": ["db_path"],
                },
            ),
            types.Tool(
                name="sample_rows",
                description=(
                    "Return a limited number of sample rows for a given table. "
                    "Use this to understand data shape and example values."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "backend": {
                            "type": "string",
                            "enum": ["sqlite", "postgres", "mysql"],
                            "description": "Database backend. Defaults to 'sqlite' when omitted.",
                        },
                        "db_path": {
                            "type": "string",
                            "description": (
                                "Path to the SQLite database file (.db or .sqlite). "
                                "Required when backend is 'sqlite'."
                            ),
                        },
                        "connection_string": {
                            "type": "string",
                            "description": (
                                "PostgreSQL or MySQL connection URL. "
                                "Required when backend is 'postgres' or 'mysql'."
                            ),
                        },
                        "table": {
                            "type": "string",
                            "description": "Table name to sample from.",
                        },
                        "limit": {
                            "type": "integer",
                            "minimum": 1,
                            "description": "Maximum number of rows to return (default 10).",
                        },
                    },
                    "required": ["table"],
                },
            ),
            types.Tool(
                name="explain_database",
                description=(
                    "High-level explanation of a database schema and its likely purpose, "
                    "based on the schema summary and table/column names."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "backend": {
                            "type": "string",
                            "enum": ["sqlite", "postgres", "mysql"],
                            "description": "Database backend. Defaults to 'sqlite' when omitted.",
                        },
                        "db_path": {
                            "type": "string",
                            "description": (
                                "Path to the SQLite database file (.db or .sqlite). "
                                "Required when backend is 'sqlite'."
                            ),
                        },
                        "connection_string": {
                            "type": "string",
                            "description": (
                                "PostgreSQL or MySQL connection URL. "
                                "Required when backend is 'postgres' or 'mysql'."
                            ),
                        },
                    },
                    "required": ["db_path"],
                },
            ),
            types.Tool(
                name="suggest_indexes_for_query",
                description=(
                    "Given a SELECT query and knowledge of the schema, suggest indexes "
                    "that might improve performance. This does not modify the database."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The SELECT query to analyze.",
                        }
                    },
                    "required": ["query"],
                },
            ),
        ]

    @server.list_resources()
    async def list_resources() -> list[types.Resource]:
        return [
            types.Resource(
                uri=AnyUrl(_readme_uri()),
                name="Database README",
                description="README.md from the local directory describing the database's business context. Use this to understand domain and conventions before writing SQL.",
                mimeType="text/markdown",
            ),
            types.Resource(
                uri=AnyUrl(README_TEMPLATE_URI),
                name="Database README template",
                description=(
                    "Template for per-database README files, describing business context, "
                    "conventions, key tables, and gotchas."
                ),
                mimeType="text/markdown",
            ),
        ]

    @server.read_resource()
    async def read_resource(uri: AnyUrl) -> list[ReadResourceContents]:
        token = _request_id.set(uuid.uuid4().hex[:8])
        try:
            return await _read_resource_impl(uri)
        finally:
            _request_id.reset(token)

    async def _read_resource_impl(uri: AnyUrl) -> list[ReadResourceContents]:
        if _is_readme_uri(uri):
            path = _readme_path()
            if not path.exists():
                raise ValueError(
                    f"README.md not found in the current directory: {path.parent}\n"
                    "Add a README.md file to describe the database's business context."
                )
            if not path.is_file():
                raise ValueError(f"README path is not a file: {path}")
            try:
                text = path.read_text(encoding="utf-8")
            except OSError as e:
                _log("readme_read_error", level="error", path=str(path), error=str(e))
                raise ValueError(f"Cannot read README.md: {e}") from e
            _log("readme_read_success", level="info", path=str(path))
            return [ReadResourceContents(content=text, mime_type="text/markdown")]
        if _is_readme_template_uri(uri):
            _log("readme_template_served", level="info")
            return [
                ReadResourceContents(
                    content=_readme_template_content(),
                    mime_type="text/markdown",
                )
            ]
        raise ValueError(
            f"Unknown resource: {uri}. "
            "This server only serves the local Database README and README template resources."
        )

    @server.call_tool()
    async def call_tool(
        name: str,
        arguments: dict,
    ) -> list[types.TextContent]:
        token = _request_id.set(uuid.uuid4().hex[:8])
        try:
            return _call_tool_impl(name, arguments)
        finally:
            _request_id.reset(token)

    async def _call_tool_impl(name: str, arguments: dict) -> list[types.TextContent]:
        if name == "list_tables":
            db_path = arguments.get("db_path")
            backend = arguments.get("backend") or "sqlite"
            connection_string = arguments.get("connection_string")
            if backend in (None, "", "sqlite") and (not db_path or not isinstance(db_path, str)):
                raise ValueError(
                    "db_path (string) is required when backend is 'sqlite' or omitted."
                )
            result = _list_tables_impl(
                db_path or "",
                backend=backend,
                connection_string=connection_string,
            )
            return [types.TextContent(type="text", text=result)]
        if name == "execute_readonly_query":
            db_path = arguments.get("db_path")
            query = arguments.get("query")
            backend = arguments.get("backend") or "sqlite"
            connection_string = arguments.get("connection_string")
            if backend in (None, "", "sqlite") and (not db_path or not isinstance(db_path, str)):
                raise ValueError(
                    "db_path (string) is required when backend is 'sqlite' or omitted."
                )
            if query is None or not isinstance(query, str):
                raise ValueError("query (string) is required.")
            result = _execute_readonly_query_impl(
                db_path or "",
                query,
                backend=backend,
                connection_string=connection_string,
            )
            return [types.TextContent(type="text", text=result)]
        if name == "schema_summary":
            backend = arguments.get("backend") or "sqlite"
            db_path = arguments.get("db_path")
            connection_string = arguments.get("connection_string")
            normalized = _normalize_backend(backend)
            if normalized == "sqlite":
                if not db_path or not isinstance(db_path, str):
                    raise ValueError(
                        "db_path (string) is required when backend is 'sqlite' or omitted."
                    )
                summary = _list_tables_sqlite(db_path)
            elif normalized == "postgres":
                if not connection_string or not isinstance(connection_string, str):
                    raise ValueError(
                        "connection_string (PostgreSQL URL) is required when backend='postgres'."
                    )
                summary = _list_tables_postgres(connection_string)
            elif normalized == "mysql":
                if not connection_string or not isinstance(connection_string, str):
                    raise ValueError(
                        "connection_string (MySQL URL) is required when backend='mysql'."
                    )
                summary = _list_tables_mysql(connection_string)
            else:  # pragma: no cover - _normalize_backend already validates
                raise ValueError(f"Unsupported backend: {backend!r}")
            # For a compact summary, keep only the first line of each table block.
            lines = []
            for block in summary.split("\n\n"):
                first_line = block.strip().splitlines()[0] if block.strip() else ""
                if first_line:
                    lines.append(first_line)
            compact = "\n".join(lines)
            return [types.TextContent(type="text", text=compact)]
        if name == "sample_rows":
            backend = arguments.get("backend") or "sqlite"
            db_path = arguments.get("db_path")
            connection_string = arguments.get("connection_string")
            table = arguments.get("table")
            limit = arguments.get("limit") or 10
            if not isinstance(table, str) or not table:
                raise ValueError("table (string) is required.")
            if not isinstance(limit, int) or limit <= 0:
                raise ValueError("limit must be a positive integer.")
            normalized = _normalize_backend(backend)
            if normalized == "sqlite":
                if not db_path or not isinstance(db_path, str):
                    raise ValueError(
                        "db_path (string) is required when backend is 'sqlite' or omitted."
                    )
                query = f"SELECT * FROM {table!r} LIMIT {limit}"
                result = _execute_readonly_query_impl(db_path, query, backend="sqlite")
            elif normalized == "postgres":
                if not connection_string or not isinstance(connection_string, str):
                    raise ValueError(
                        "connection_string (PostgreSQL URL) is required when backend='postgres'."
                    )
                query = f'SELECT * FROM "{table}" LIMIT {limit}'
                result = _execute_readonly_query_impl(
                    "",
                    query,
                    backend="postgres",
                    connection_string=connection_string,
                )
            elif normalized == "mysql":
                if not connection_string or not isinstance(connection_string, str):
                    raise ValueError(
                        "connection_string (MySQL URL) is required when backend='mysql'."
                    )
                query = f"SELECT * FROM `{table}` LIMIT {limit}"
                result = _execute_readonly_query_impl(
                    "",
                    query,
                    backend="mysql",
                    connection_string=connection_string,
                )
            else:  # pragma: no cover - _normalize_backend already validates
                raise ValueError(f"Unsupported backend: {backend!r}")
            return [types.TextContent(type="text", text=result)]
        if name == "explain_database":
            backend = arguments.get("backend") or "sqlite"
            db_path = arguments.get("db_path")
            connection_string = arguments.get("connection_string")
            normalized = _normalize_backend(backend)
            if normalized == "sqlite":
                if not db_path or not isinstance(db_path, str):
                    raise ValueError(
                        "db_path (string) is required when backend is 'sqlite' or omitted."
                    )
                summary = _list_tables_sqlite(db_path)
            elif normalized == "postgres":
                if not connection_string or not isinstance(connection_string, str):
                    raise ValueError(
                        "connection_string (PostgreSQL URL) is required when backend='postgres'."
                    )
                summary = _list_tables_postgres(connection_string)
            elif normalized == "mysql":
                if not connection_string or not isinstance(connection_string, str):
                    raise ValueError(
                        "connection_string (MySQL URL) is required when backend='mysql'."
                    )
                summary = _list_tables_mysql(connection_string)
            else:  # pragma: no cover
                raise ValueError(f"Unsupported backend: {backend!r}")

            lines = [line for line in summary.splitlines() if line.startswith("• ")]
            explanation_lines = [
                "This database appears to contain the following key tables:",
            ]
            for line in lines:
                explanation_lines.append(f"- {line[2:]}")
            explanation_lines.append(
                "\nUse this as a starting point to understand the domain; "
                "combine with the Database README for full business context."
            )
            explanation = "\n".join(explanation_lines)
            return [types.TextContent(type="text", text=explanation)]
        if name == "suggest_indexes_for_query":
            query = arguments.get("query")
            if query is None or not isinstance(query, str):
                raise ValueError("query (string) is required.")
            # Simple heuristic: suggest indexes on columns used in WHERE and JOIN clauses.
            where_matches = re.findall(
                r"\bWHERE\b(.*?)(?:\bGROUP\b|\bORDER\b|\bLIMIT\b|$)",
                query,
                flags=re.IGNORECASE | re.DOTALL,
            )
            join_matches = re.findall(
                r"\bJOIN\b\s+[\w\.]+\s+ON\s+(.*?)(?:\bJOIN\b|\bWHERE\b|\bGROUP\b|\bORDER\b|\bLIMIT\b|$)",
                query,
                flags=re.IGNORECASE | re.DOTALL,
            )

            candidates: set[str] = set()
            for segment in where_matches + join_matches:
                for match in re.findall(r"([A-Za-z_][\w\.]*)\s*=", segment):
                    candidates.add(match)

            if not candidates:
                text = (
                    "No obvious index candidates were detected from simple WHERE/JOIN analysis.\n"
                    "Consider indexing columns used in equality predicates or as foreign keys."
                )
            else:
                sorted_cols = sorted(candidates)
                lines = [
                    "Based on a simple analysis of WHERE and JOIN clauses, "
                    "the following columns look like index candidates:",
                ]
                for col in sorted_cols:
                    lines.append(f"- {col}")
                lines.append(
                    "\nThese are heuristic suggestions only; always validate with "
                    "EXPLAIN plans and real workload characteristics."
                )
                text = "\n".join(lines)
            return [types.TextContent(type="text", text=text)]
        raise ValueError(f"Unknown tool: {name}.")

    return server


async def _run_server() -> None:
    """Run the MCP server over stdio."""
    server = _create_server()
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(notification_options=NotificationOptions()),
        )


def main() -> None:
    """Entry point for the mcp-sql-bridge CLI."""
    argv = sys.argv[1:] if len(sys.argv) > 1 else []
    if "--help" in argv or "-h" in argv:
        print(
            "Usage: mcp-sql-bridge [OPTIONS]\n"
            "  Start the MCP SQL Bridge server (stdio). No options required.\n"
            "  Use with Cursor or Claude Desktop by adding this command to your MCP config.\n"
            "  See README for setup. Options: --version, -V, --help, -h.",
            file=sys.stderr,
        )
        sys.exit(0)
    if "--version" in argv or "-V" in argv:
        try:
            from importlib.metadata import version

            print(version("mcp-sql-bridge"), end="")
        except Exception:
            print("0.2.0", end="")
        sys.exit(0)
    # Use stderr for any logging so stdout is reserved for JSON-RPC
    anyio.run(_run_server)
