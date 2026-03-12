# Error taxonomy

The server surfaces errors as `ValueError` messages. For clarity and AI parsing, errors fall into these categories:

| Category    | When it happens | Example |
|------------|------------------|--------|
| **Validation** | Invalid `db_path`, missing required args, unsupported `backend` | Path does not exist; `db_path` (string) is required when backend is 'sqlite'. |
| **Connection** | Cannot open SQLite file or connect to Postgres/MySQL | Could not open the database; Could not connect to PostgreSQL. |
| **Query**     | SELECT rejected (non-SELECT) or query execution failed | Only SELECT queries are allowed; Query failed: ... |
| **Resource**  | Unknown resource URI or README not found | Unknown resource; README.md not found. |
| **Tool**      | Unknown tool name | Unknown tool: ... |

All errors are intended to be **actionable**: they explain what went wrong and, where possible, what to do next (e.g. set `MCP_SQL_BRIDGE_DB_ALLOWED_DIRS`, use a valid path, or provide `connection_string`).
