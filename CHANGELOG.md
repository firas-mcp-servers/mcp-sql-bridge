## 0.2.0 — Multi-database Pro release

- Add connection abstraction with `backend` support for **sqlite**, **postgres**, and **mysql**.
- Extend `list_tables` and `execute_readonly_query` to work across all supported backends.
- Add optional tools:
  - `schema_summary` — compact overview of tables and key columns.
  - `sample_rows` — limited sample rows from a given table.
  - `explain_database` — high-level explanation of a database schema.
  - `suggest_indexes_for_query` — heuristic index suggestions for a SELECT query.
- Add README template resource for per-database documentation.
- Add optional dependencies / extras for PostgreSQL (`psycopg`) and MySQL (`pymysql`).

## 0.1.0 — Initial release

- SQLite-only MCP server (`Local-SQL-Insight`) with:
  - `list_tables(db_path)`
  - `execute_readonly_query(db_path, query)`
  - Database README resource (local `README.md`).
- Path validation, basic tests, and CI.

