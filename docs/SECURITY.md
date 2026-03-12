# Security and hardening

This document describes how to run MCP SQL Bridge safely in production-like environments.

## Read-only by design

- **SELECT only** — The server only executes `SELECT` queries. All tools that run SQL enforce this; `INSERT`, `UPDATE`, `DELETE`, and DDL are rejected.
- **No schema or data changes** — The server never modifies your database schema or data.

## Recommended deployment practices

### 1. Restrict database paths (SQLite)

Set `MCP_SQL_BRIDGE_DB_ALLOWED_DIRS` to a list of directories that may contain SQLite files. The server will reject any `db_path` that is not under one of these directories.

Example (colon-separated on macOS/Linux, semicolon on Windows):

```bash
export MCP_SQL_BRIDGE_DB_ALLOWED_DIRS="/var/data/dbs:/home/app/readonly-dbs"
```

Leave unset to allow any path (suitable only for trusted, single-tenant use).

### 2. Limit result size

- **Rows:** `MCP_SQL_BRIDGE_MAX_ROWS` (default: 500). Caps the number of rows returned per query. Clamped to 1–50000 for safety.
- **Bytes:** `MCP_SQL_BRIDGE_MAX_BYTES`. Caps the size of the formatted result in bytes. Unset by default (no limit).

Example:

```bash
export MCP_SQL_BRIDGE_MAX_ROWS=1000
export MCP_SQL_BRIDGE_MAX_BYTES=524288
```

### 3. PostgreSQL and MySQL

- Use a **dedicated read-only database user** (e.g. `default_transaction_read_only = on` in Postgres, or a user with only `SELECT`).
- Prefer **connection strings in environment variables** or a secrets manager; avoid hardcoding credentials in config.
- Run the MCP server in a network segment that can reach only the database(s) you intend to expose.

### 4. Stdio and process isolation

The server talks over stdio to the MCP host (e.g. Cursor, Claude Desktop). The host is responsible for:

- Running the server process with an appropriate user and permissions.
- Not exposing stdio to untrusted parties.

### 5. Logging

Structured logs are written to stderr (JSON lines). Avoid logging connection strings or sensitive query parameters; the server logs tool names, paths, and error messages, not full connection details.

## Reporting vulnerabilities

If you believe you have found a security issue, please open a private [Security Advisory](https://github.com/firas-mcp-servers/mcp-sql-bridge/security/advisories/new) on GitHub rather than a public issue.
