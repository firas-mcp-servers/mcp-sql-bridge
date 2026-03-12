# MCP SQL Bridge

**Local-SQL-Insight** — Give your AI assistant direct, read-only access to your SQL databases over the [Model Context Protocol](https://modelcontextprotocol.io). No APIs, no cloud. Your data stays on your machine.

---

## Why use this?

- **Schema-aware AI** — The agent sees table names, columns, and full `CREATE TABLE` DDL so it can write correct SQL.
- **Business context** — Expose a project `README.md` as a resource so the AI understands your domain and conventions.
- **Read-only by design** — Only `SELECT` is allowed. No accidental writes or schema changes.
- **Stdio transport** — Works with Cursor, Claude Desktop, and any MCP host. No ports or network setup.
- **Multi-database (Pro)** — Use the same tools against SQLite, PostgreSQL, and MySQL by switching a `backend` and connection string.

---

## Quick start

```bash
git clone <your-repo-url>
cd mcp-sql-bridge
poetry install
```

Then plug the server into your editor or desktop app (see below).

---

## How to use with Cursor

1. **Install the server** (if not already):
   ```bash
   cd /path/to/mcp-sql-bridge
   poetry install
   ```

2. **Configure MCP**  
   Open Cursor Settings → **Tools & MCP** (or edit the config file directly).  
   Add the server using the template in **`mcp-config.json`** in this repo:

   - **Option A — Global config**  
     Put the contents of `mcp-config.json` into:
     - **macOS / Linux:** `~/.cursor/mcp.json`
     - **Windows:** `%APPDATA%\Cursor\mcp.json`

   - **Option B — Project config**  
     Copy `mcp-config.json` into your project as `.cursor/mcp.json` (and adjust the `cwd` path to this repo if needed).

3. **Set the path**  
   In the config, set `cwd` (or the path in `args`) to the **absolute path** of your `mcp-sql-bridge` project directory so Cursor can run `poetry run mcp-sql-bridge` from there.

4. **Restart Cursor**  
   MCP servers load at startup. Restart Cursor after changing the config.

5. **Use it**  
   In any chat, the AI can call **Local-SQL-Insight** tools: `list_tables`, `execute_readonly_query`, and read the **Database README** resource.  
   - For SQLite, point it at a file path (e.g. `./data/app.db`) with `backend: "sqlite"` or by omitting `backend`.  
   - For PostgreSQL/MySQL (Pro), provide a `backend` and `connection_string` URL.

---

## How to use with Claude Desktop

1. **Install the server** (if not already):
   ```bash
   cd /path/to/mcp-sql-bridge
   poetry install
   ```

2. **Locate Claude’s config file**  
   - **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`  
   - **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

3. **Add the MCP server**  
   Add a `mcpServers` entry (or merge into existing) like this, using the **absolute path** to your `mcp-sql-bridge` directory:

   ```json
   {
     "mcpServers": {
       "local-sql-insight": {
         "command": "poetry",
         "args": ["run", "mcp-sql-bridge"],
         "cwd": "/absolute/path/to/mcp-sql-bridge"
       }
     }
   }
   ```

   If Claude Desktop uses a different Python environment, you can instead use the full path to the `mcp-sql-bridge` executable in the project’s virtualenv, for example:

   ```json
   {
     "mcpServers": {
       "local-sql-insight": {
         "command": "/absolute/path/to/mcp-sql-bridge/.venv/bin/mcp-sql-bridge",
         "args": []
       }
     }
   }
   ```

4. **Restart Claude Desktop**  
   Restart the app so it picks up the new MCP config.

5. **Use it**  
   Claude can use the **list_tables** and **execute_readonly_query** tools and read the **Database README** resource.  
   - For SQLite, use your SQLite file path (e.g. `~/project/data/app.db`).  
   - For PostgreSQL/MySQL, supply connection URLs when the model asks for database details.

---

## What the server provides

| Capability | Description |
|------------|-------------|
| **list_tables** | Lists every table, its columns, and the full `CREATE TABLE` statement. Supports `backend: "sqlite" | "postgres" | "mysql"`. |
| **execute_readonly_query** | Runs a `SELECT` query and returns results as a formatted text table. Supports all backends via `backend` and `connection_string` / `db_path`. |
| **schema_summary** | Compact overview of tables and key columns for a quick schema scan. |
| **sample_rows** | Limited sample rows from a given table to understand data shape and example values. |
| **explain_database** | High-level explanation of the database based on its schema. |
| **suggest_indexes_for_query** | Heuristic index suggestions for a given SELECT query (no writes). |
| **Database README** (resource) | Serves `README.md` from the server’s current working directory so the AI can read your project’s business context. |
| **Database README template** (resource) | A markdown template for per-database README files (owners, conventions, key tables, gotchas). |

For SQLite, the server validates that paths point to real SQLite files (magic header check) and returns clear errors if a path is wrong or not a database.  
For PostgreSQL/MySQL, it validates connections and reports connection/auth errors clearly; use read-only roles in production.

---

## Requirements

- **Python 3.11+**
- **Poetry** (recommended) or `pip` for dependencies
- Optional extras:
  - `postgres` extra for PostgreSQL (`psycopg`)
  - `mysql` extra for MySQL (`pymysql`)

## Support & maintenance

- Targeted Python: 3.11+
- MCP: current stable versions at time of release
- Backwards-compatible changes will be released as minor versions; breaking changes will bump the major or minor version and be noted in `CHANGELOG.md`.
- The project is intended to be feature-complete after the 0.2.x line; future work will focus on fixes and compatibility updates only.

---

## License

MIT. See [LICENSE](LICENSE) for details.
