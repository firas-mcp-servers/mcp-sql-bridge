# Pricing model and licensing

## Current licensing

- **Open source (MIT)** — The MCP SQL Bridge codebase is licensed under the [MIT License](https://github.com/firas-mcp-servers/mcp-sql-bridge/blob/master/LICENSE). You can use, modify, and distribute it for free.
- **SQLite** — All features that use SQLite (including `list_tables`, `execute_readonly_query`, README resource, schema summary, sample rows, explain_database, suggest_indexes_for_query) are available in the OSS build with no payment required.

## Pro / paid offerings (optional)

- **PostgreSQL and MySQL support** — Implemented in the same repo via optional dependencies (`psycopg`, `pymysql`). You can install them locally with `poetry install --extras pro` at no cost.
- **Commercial / “Pro” distribution** — If we offer a separate commercial distribution (e.g. a branded build, support, or a Gumroad bundle), that will be documented here and in the README. Today there is no separate paid package; the project is fully usable as OSS.

## Upgrade path

- From “SQLite-only” usage to “SQLite + Postgres + MySQL”: install the optional extras and use `backend` and `connection_string` in tool calls. No license change required.

## Summary

| Area              | Model        | Notes                                      |
|-------------------|-------------|--------------------------------------------|
| Code              | MIT         | Use and modify freely                      |
| SQLite features   | Free        | No payment required                        |
| Postgres/MySQL    | Optional deps | Install `--extras pro`; no separate license |
| Future paid tiers | TBD         | Will be documented here if introduced     |
