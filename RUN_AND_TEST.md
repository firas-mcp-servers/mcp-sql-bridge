# How to run and test the project (MCP + Web)

## One-time setup

```bash
cd /path/to/mcp-sql-bridge
poetry install
```

Optional (for the web server and full docs):

```bash
poetry install --with web
poetry run mkdocs build
```

---

## Run the MCP server

The MCP server talks over **stdio** to a host (Cursor, Claude Desktop, etc.). It does not open a port.

**Start it from the project root:**

```bash
poetry run mcp-sql-bridge
```

It will wait for JSON-RPC on stdin. To test it manually you need an MCP client or use Cursor/Claude.

**Quick sanity check (no MCP client):** run the unit tests so the server code path is exercised:

```bash
poetry run pytest -v
```

**Test with a real SQLite file:**

1. Create the example DB:
   ```bash
   python examples/create_sample_db.py
   ```
2. In Cursor (or another MCP host), add this repo’s MCP config and point the AI at `examples/sample.db` for `list_tables` or `execute_readonly_query`.

---

## Run the web server

From the project root:

```bash
poetry run mcp-sql-bridge-web
```

Then open in a browser:

| URL | What you get |
|-----|----------------|
| http://localhost:8000 | Landing page |
| http://localhost:8000/docs | Swagger UI |
| http://localhost:8000/redoc | ReDoc |
| http://localhost:8000/documentation/ | Full docs (after `mkdocs build`) |

**Test from the terminal:**

```bash
curl -s http://localhost:8000/api/health
# {"status":"ok","service":"mcp-sql-bridge-web"}

curl -s http://localhost:8000/api/info
# {"name":"MCP SQL Bridge","version":"0.2.0","description":"..."}
```

---

## Run tests

**All tests (MCP logic, no web):**

```bash
poetry run pytest -v
```

**With coverage (if you add pytest-cov):**

```bash
poetry run pytest -v --cov=mcp_sql_bridge --cov-report=term-missing
```

Tests use only SQLite; no Postgres/MySQL or network required.

---

## Run Docker integration (Postgres + MySQL)

**Prerequisites:** Docker, docker compose, and `poetry install --extras pro`.

**Option A — See MCP tool output (script):**

```bash
poetry run python scripts/run_docker_integration.py
```

This starts Postgres and MySQL in Docker, creates a `widgets` table and rows, then runs `list_tables` and `execute_readonly_query` for both backends and prints the results. Containers are left running; stop with:

```bash
docker compose -f docker-compose.test.yml down
```

**Option B — Pytest (same flow, with assertions):**

```bash
docker compose -f docker-compose.test.yml up -d   # if not already up
poetry run pytest tests/test_integration_docker.py -v -s
```

Use `-s` to see the printed MCP output. The fixture brings containers up before the module and down after.

---

## Summary

| Goal | Command |
|------|---------|
| Install (core) | `poetry install` |
| Install + web | `poetry install --with web` |
| Build docs site | `poetry run mkdocs build` |
| Run MCP server | `poetry run mcp-sql-bridge` |
| Run web server | `poetry run mcp-sql-bridge-web` |
| Run tests | `poetry run pytest -v` |
| Example DB | `python examples/create_sample_db.py` |
| Docker integration (script) | `poetry run python scripts/run_docker_integration.py` |
| Docker integration (pytest) | `poetry run pytest tests/test_integration_docker.py -v -s` |
