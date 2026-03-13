# Sprint plan (next 5 sprints)

Backlog is tracked as **GitHub issues** with milestones. This doc summarizes the plan.

---

## Sprint 1 — Polish & reliability

**Goal:** Error handling, logging, and small fixes to stabilize the MCP and web server.

| Issue | Title |
|-------|--------|
| [#17](https://github.com/firas-mcp-servers/mcp-sql-bridge/issues/17) | Unify and sanitize MCP error messages |
| [#18](https://github.com/firas-mcp-servers/mcp-sql-bridge/issues/18) | Add --version and --help to MCP CLI |
| [#19](https://github.com/firas-mcp-servers/mcp-sql-bridge/issues/19) | Web server: graceful shutdown and port config |
| [#20](https://github.com/firas-mcp-servers/mcp-sql-bridge/issues/20) | Postgres: fallback when pg_get_tabledef is missing |

---

## Sprint 2 — Developer experience

**Goal:** CLI, examples, and DX so contributors and users get a smoother experience.

| Issue | Title |
|-------|--------|
| [#22](https://github.com/firas-mcp-servers/mcp-sql-bridge/issues/22) | Add Makefile or just script for common commands |
| [#23](https://github.com/firas-mcp-servers/mcp-sql-bridge/issues/23) | Expand examples: Postgres/MySQL connection strings in README |
| [#24](https://github.com/firas-mcp-servers/mcp-sql-bridge/issues/24) | Pre-commit or CI lint (ruff/black) |
| [#25](https://github.com/firas-mcp-servers/mcp-sql-bridge/issues/25) | Document run_docker_integration.py in README |

---

## Sprint 3 — Production readiness

**Goal:** Observability, health checks, and operational hardening for 1.0.

| Issue | Title |
|-------|--------|
| [#26](https://github.com/firas-mcp-servers/mcp-sql-bridge/issues/26) | Web server: /health and /ready endpoints |
| [#27](https://github.com/firas-mcp-servers/mcp-sql-bridge/issues/27) | Structured metrics (optional) |
| [#28](https://github.com/firas-mcp-servers/mcp-sql-bridge/issues/28) | CI: run Docker integration tests on schedule or tag |
| [#29](https://github.com/firas-mcp-servers/mcp-sql-bridge/issues/29) | Document 1.0 release criteria |

---

## Sprint 4 — Growth & distribution

**Goal:** MCP registry, landing page, and distribution to grow adoption.

| Issue | Title |
|-------|--------|
| [#30](https://github.com/firas-mcp-servers/mcp-sql-bridge/issues/30) | Submit to MCP registry or community list |
| [#31](https://github.com/firas-mcp-servers/mcp-sql-bridge/issues/31) | Landing page: GitHub Pages or Vercel |
| [#32](https://github.com/firas-mcp-servers/mcp-sql-bridge/issues/32) | Announcement post and social copy |
| [#33](https://github.com/firas-mcp-servers/mcp-sql-bridge/issues/33) | Repo topics and description |

---

## Sprint 5 — Scale & maintainability

**Goal:** Optional features, deprecation policy, and long-term maintainability.

| Issue | Title |
|-------|--------|
| [#34](https://github.com/firas-mcp-servers/mcp-sql-bridge/issues/34) | Deprecation and support policy document |
| [#35](https://github.com/firas-mcp-servers/mcp-sql-bridge/issues/35) | Optional: DuckDB or SQL Server backend |
| [#36](https://github.com/firas-mcp-servers/mcp-sql-bridge/issues/36) | Docs refresh and versioned docs |
| [#37](https://github.com/firas-mcp-servers/mcp-sql-bridge/issues/37) | Security and dependency audit in CI |

---

**View all open issues by milestone:** [Milestones](https://github.com/firas-mcp-servers/mcp-sql-bridge/milestones)
