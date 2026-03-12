# Examples

Sample configs and queries to get started with MCP SQL Bridge.

## Contents

| File / folder     | Description |
|-------------------|-------------|
| `mcp-config-cursor.json` | Example Cursor MCP config (SQLite). |
| `mcp-config-pro.json`    | Example config for Pro (Postgres/MySQL) with env-based connection. |
| `sample.db`              | Example SQLite database (created by `create_sample_db.py`). |
| `queries.sql`             | Example SELECT queries you can run via `execute_readonly_query`. |

## Quick start

1. Create the sample SQLite database:

   ```bash
   cd examples
   python create_sample_db.py
   ```

2. Point your MCP config at this repo and set `cwd` to the repo root. In a chat, ask the AI to use `list_tables` with `db_path` set to `examples/sample.db`, then try queries from `queries.sql`.

3. For Postgres/MySQL, use `mcp-config-pro.json` as a reference and set `connection_string` via environment or your host’s config (never commit secrets).
