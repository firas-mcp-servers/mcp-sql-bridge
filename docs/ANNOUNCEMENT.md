# Announcement post and social copy

Templates for announcing `mcp-sql-bridge` across channels.

---

## GitHub Discussions / dev community post

**Title:** MCP SQL Bridge — give your AI read-only access to SQLite, Postgres, and MySQL (open source)

**Body:**

Hey everyone! I built **mcp-sql-bridge**, an open-source MCP server that gives AI assistants (Cursor, Claude Desktop, etc.) direct, read-only access to your SQL databases — locally, with no cloud and no API keys.

**What it does:**
- 🔍 Schema inspection (`list_tables`) — shows every table, column, and CREATE TABLE DDL
- 📊 Read-only queries (`execute_readonly_query`) — SELECT only, enforced server-side
- 🧠 Smart tools — schema summary, sample rows, index suggestions, database explanation
- 🗄️ Multi-database — SQLite, PostgreSQL, MySQL / MariaDB
- 🔒 Safe by design — path restrictions, no writes, connection strings are redacted in logs

**Quick start:**
```bash
git clone https://github.com/firas-mcp-servers/mcp-sql-bridge
cd mcp-sql-bridge
poetry install
```
Then add it to your Cursor / Claude Desktop MCP config (see README).

**Repo:** https://github.com/firas-mcp-servers/mcp-sql-bridge

Feedback and contributions welcome!

---

## Twitter / X thread

**Tweet 1:**
🚀 Introducing mcp-sql-bridge — give your AI assistant (Cursor, Claude) read-only access to your SQL databases, locally. No cloud, no API keys.

SQLite ✅  PostgreSQL ✅  MySQL ✅

https://github.com/firas-mcp-servers/mcp-sql-bridge

#MCP #AI #OpenSource #SQL

**Tweet 2:**
How it works: the MCP server exposes `list_tables` (schema + DDL) and `execute_readonly_query` (SELECT only). Your AI can explore your DB and write correct SQL — without ever leaving your machine.

**Tweet 3:**
Works with @cursor_ai and @AnthropicAI Claude Desktop out of the box. Just add it to your MCP config.

`poetry install && poetry run mcp-sql-bridge`

**Tweet 4:**
Open source, MIT license. Contributions welcome! Drop a ⭐ if you find it useful.

https://github.com/firas-mcp-servers/mcp-sql-bridge

---

## LinkedIn post

I just open-sourced **mcp-sql-bridge** — a Model Context Protocol (MCP) server that gives AI assistants direct, read-only access to SQL databases (SQLite, PostgreSQL, MySQL) running locally on your machine.

Why? Most AI coding tools can't "see" your database schema or data, so they write SQL that doesn't match your real tables. This bridges that gap — securely, locally, with no cloud involved.

Key features:
• Schema-aware: the AI sees full CREATE TABLE DDL, not just column names
• Read-only enforced: only SELECT queries are allowed, server-side
• Multi-database: SQLite for local files, Postgres/MySQL for team DBs
• Works with Cursor, Claude Desktop, and any MCP host

GitHub: https://github.com/firas-mcp-servers/mcp-sql-bridge

---

## Hacker News / Product Hunt tagline

**Tagline:** Read-only MCP server for SQL — let your AI explore SQLite, Postgres, and MySQL locally.

**One-liner:** Open-source MCP server that gives AI assistants schema-aware, read-only access to your SQL databases, with no cloud and no API keys.
