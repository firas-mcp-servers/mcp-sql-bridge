# Submitting to MCP community lists and registries

This document tracks where `mcp-sql-bridge` should be listed and the checklist to complete before submission.

---

## Submission checklist

Before submitting to any list, make sure these are all true:

- [ ] Repository is public on GitHub (`firas-mcp-servers/mcp-sql-bridge`)
- [ ] `README.md` has clear install + quick-start instructions
- [ ] MCP config examples are in `examples/` (`mcp-config-cursor.json`, `mcp-config-pro.json`)
- [ ] `pyproject.toml` has correct `name`, `description`, `version`, and `authors`
- [ ] CI is green (lint + tests pass on Python 3.11–3.13)
- [ ] At least one tagged release exists (e.g. `v0.2.0`)
- [ ] Published to PyPI: `poetry publish` (requires `PYPI_TOKEN`)
- [ ] Repository topics set (see `docs/REPO_TOPICS.md`)

---

## Target lists

### 1. Awesome MCP Servers
- Repo: https://github.com/punkpeye/awesome-mcp-servers
- How: Open a PR adding a row to the relevant table (SQL / database tools section).
- Row template:
  ```
  | [mcp-sql-bridge](https://github.com/firas-mcp-servers/mcp-sql-bridge) | Read-only SQL queries and schema exploration (SQLite, Postgres, MySQL) via MCP | Python |
  ```

### 2. MCP.so / MCP Hub
- URL: https://mcp.so / https://mcphub.io (check current canonical URL)
- How: Submit via their web form or GitHub PR if they accept community submissions.
- Info needed: repo URL, short description, categories (database, SQL, developer-tools), author.

### 3. Glama MCP servers list
- URL: https://glama.ai/mcp/servers
- How: Submit PR to their registry repo or web submission form.

### 4. Cursor MCP Marketplace (if available)
- Check Cursor's official docs for any MCP marketplace or plugin directory.

---

## Description copy (for all submissions)

> **mcp-sql-bridge** — Give your AI assistant direct, read-only access to SQLite, PostgreSQL, and MySQL databases over the Model Context Protocol. No APIs, no cloud. Your data stays local. Supports schema inspection, SELECT queries, sample rows, and index suggestions. Works with Cursor, Claude Desktop, and any MCP host.
