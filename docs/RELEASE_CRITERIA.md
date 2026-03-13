# 1.0 Release criteria

This document defines what "done" means for the `mcp-sql-bridge` 1.0 release.

---

## Functional requirements

| Criterion | Status |
|-----------|--------|
| SQLite backend: list_tables, execute_readonly_query, schema_summary, sample_rows, explain_database, suggest_indexes_for_query | ✅ Done |
| PostgreSQL backend (psycopg) with connection-string auth | ✅ Done |
| MySQL / MariaDB backend (pymysql) | ✅ Done |
| Postgres DDL fallback via information_schema when pg_get_tabledef is absent | ✅ Done |
| Read-only enforcement (SELECT only) | ✅ Done |
| Path validation and SQLite magic-header check | ✅ Done |
| MCP_SQL_BRIDGE_DB_ALLOWED_DIRS path restriction | ✅ Done |
| Database README resource and README template resource | ✅ Done |
| Structured, actionable error messages with category prefixes | ✅ Done |
| `--version` / `--help` CLI flags | ✅ Done |
| Web server: landing page, Swagger, ReDoc, /health, /ready, /metrics | ✅ Done |
| Web server port/host configurable via env vars | ✅ Done |

## Quality requirements

| Criterion | Status |
|-----------|--------|
| Python 3.11 – 3.13 test matrix passing in CI | ✅ Done |
| Ruff lint + format gate in CI | ✅ Done |
| Unit test coverage for core logic (execute, list, validate) | ✅ Done |
| Docker-based Postgres + MySQL integration tests | ✅ Done |
| Scheduled nightly + tag-triggered integration CI | ✅ Done |
| Weekly pip-audit security scan in CI | ✅ Done |

## Documentation requirements

| Criterion | Status |
|-----------|--------|
| README: quick start, Cursor / Claude Desktop setup, connection strings | ✅ Done |
| RUN_AND_TEST.md: local dev, tests, Docker integration | ✅ Done |
| docs/ERROR_TAXONOMY.md | ✅ Done |
| docs/SECURITY.md | ✅ Done |
| docs/CONTRIBUTING.md | ✅ Done |
| docs/DEPRECATION_AND_SUPPORT.md | ✅ Done |
| CHANGELOG.md with 0.1.0, 0.2.0, and 1.0.0 entries | ✅ Done |
| MkDocs site builds cleanly (`mkdocs build`) | ✅ Done |

## Distribution / visibility

| Criterion | Status |
|-----------|--------|
| Published to PyPI as `mcp-sql-bridge` | ⬜ Pending |
| GitHub repo topics set | ✅ Done |
| Submitted to MCP community list / registry | ⬜ Pending |
| Announcement post drafted | ✅ Done |

---

## Definition of done

A release is cut as `v1.0.0` when **all** rows in the table above are ✅. Items marked ⬜ are the remaining gate criteria.

Tag the release with `git tag v1.0.0 && git push --tags`. The tag triggers the integration CI workflow automatically.
