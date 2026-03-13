## 1.0.0 — Production release

### New features
- **CLI flags:** `--version` / `-V` (prints package version) and `--help` / `-h` (prints usage) added to `mcp-sql-bridge` entry point.
- **Web server config:** `MCP_SQL_BRIDGE_WEB_HOST` and `MCP_SQL_BRIDGE_WEB_PORT` env vars control the uvicorn bind address and port.
- **Web server endpoints:** `/api/ready` (readiness, returns `uptime_seconds`) and `/api/metrics` (request counters by path, no external deps) added alongside the existing `/api/health` and `/api/info`.
- **Postgres DDL fallback:** when `pg_get_tabledef` is not installed, `list_tables` falls back to building a `CREATE TABLE` statement from `information_schema.columns`.

### Quality & CI
- **Ruff lint + format** added to dev dependencies and `pyproject.toml`. CI now has a dedicated `lint` job that gates the test matrix.
- **Pre-commit config** (`.pre-commit-config.yaml`) added for local ruff hooks.
- **Docker integration CI** (`.github/workflows/integration.yml`): Postgres 15 + MySQL 8 via GitHub Actions services; triggers nightly at 02:00 UTC and on `v*` tags.
- **Security audit CI** (`.github/workflows/security.yml`): weekly `pip-audit` scan on every push/PR and on Mondays.
- **GitHub Pages CI** (`.github/workflows/pages.yml`): auto-deploys MkDocs site to GitHub Pages on every push to `main`.

### Error handling & observability
- `_err(message, category)` helper prefixes user-facing errors with `[Validation]`, `[Connection]`, `[Query]`, `[Resource]`, `[Tool]` for AI-friendly parsing.
- `_redact_connection_string()` strips passwords from all logs. SQLite paths log `path.name` only (no full filesystem path in error output).
- `docs/ERROR_TAXONOMY.md` updated to document category-prefix format.

### Developer experience
- **Makefile** with 11 targets: `install`, `install-web`, `test`, `lint`, `format`, `check`, `docker-up/down`, `docker-test`, `run-mcp`, `run-web`.
- `scripts/run_docker_integration.py` documented in README and `RUN_AND_TEST.md`.
- PostgreSQL and MySQL connection-string examples added to README.

### Documentation
- `docs/RELEASE_CRITERIA.md` — 1.0 gate criteria.
- `docs/DEPRECATION_AND_SUPPORT.md` — semver policy, Python support table, 7-day security patch SLA.
- `docs/FUTURE.md` — DuckDB, SQL Server, Oracle, BigQuery backend plans with drivers and complexity ratings.
- `docs/MCP_REGISTRY.md` — submission checklist and target lists.
- `docs/GITHUB_PAGES.md` — GitHub Pages and Vercel deployment guide.
- `docs/ANNOUNCEMENT.md` — templates for GitHub Discussions, Twitter/X, LinkedIn, HN/PH.
- `docs/REPO_TOPICS.md` — canonical repo description and topic list.
- `mkdocs.yml` refreshed: correct `site_url`, Material features, nav reorganised into Roadmap / Operations / Distribution sections.

### Repository
- GitHub repo description and 13 topics set.
- Published to PyPI as `mcp-sql-bridge`.

---

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

---

## 0.1.0 — Initial release

- SQLite-only MCP server (`Local-SQL-Insight`) with:
  - `list_tables(db_path)`
  - `execute_readonly_query(db_path, query)`
  - Database README resource (local `README.md`).
- Path validation, basic tests, and CI.
