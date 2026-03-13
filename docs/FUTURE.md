# Future ideas (roadmap beyond 0.2.x)

This document tracks potential enhancements. None are committed; they are ideas for discussion and prioritization.

---

## Planned optional backends

### DuckDB
[DuckDB](https://duckdb.org/) is an in-process analytical SQL database optimised for OLAP workloads. It reads Parquet, CSV, and Arrow files directly.

- **Driver:** `duckdb` Python package (MIT, no separate server needed).
- **backend value:** `"duckdb"`
- **connection_string:** a file path (e.g. `./analytics.duckdb`) or `":memory:"`.
- **Use case:** query Parquet / CSV files or an embedded analytics DB from the AI.
- **Complexity:** Low — DuckDB's Python API is similar to sqlite3.

### SQL Server / Azure SQL
[Microsoft SQL Server](https://www.microsoft.com/sql-server) is widely used in enterprise environments.

- **Driver:** `pyodbc` + ODBC driver, or `pymssql`.
- **backend value:** `"sqlserver"` or `"mssql"`
- **connection_string:** `mssql://user:pass@host:1433/db` (pyodbc DSN or URL).
- **Use case:** enterprise BI, Azure SQL, on-prem SQL Server.
- **Complexity:** Medium — requires ODBC driver installation on the host.

### Oracle
- **Driver:** `oracledb` (python-oracledb, MIT).
- **Complexity:** Medium — thin mode works without an Oracle client install.

### BigQuery
- **Driver:** `google-cloud-bigquery`.
- **Complexity:** High — requires GCP auth; read-only is natural (IAM roles).

---

## Other ideas

- **Advanced prompts** — MCP prompts for "Generate a report from this schema", "Find unused tables", "Suggest a data model".
- **Deeper analytics** — richer schema summary (row counts, index list, FK graph), cardinality estimates.
- **Performance tuning** — connection pooling, configurable query timeouts, streaming for large result sets.
- **MCP SDK alignment** — adopt new MCP features (progress notifications, streaming) as the protocol evolves.
- **Read-replica targeting** — detect and prefer read replicas in Postgres/MySQL when available.

---

Contribute ideas via [GitHub Discussions](https://github.com/firas-mcp-servers/mcp-sql-bridge/discussions) or [issues](https://github.com/firas-mcp-servers/mcp-sql-bridge/issues).
