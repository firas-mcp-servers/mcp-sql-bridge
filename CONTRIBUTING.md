# Contributing to MCP SQL Bridge

Thanks for your interest in contributing. This document covers local setup, running tests, and the release process.

## Prerequisites

- **Python 3.11+**
- **Poetry** ([installation](https://python-poetry.org/docs/#installation))

## Local setup

```bash
git clone https://github.com/firas-mcp-servers/mcp-sql-bridge.git
cd mcp-sql-bridge
poetry install
```

Optional backends (PostgreSQL, MySQL):

```bash
poetry install --extras pro
```

## Running tests

```bash
poetry run pytest
```

With verbose output:

```bash
poetry run pytest -v
```

Tests use only SQLite by default; no Postgres/MySQL services are required for the core suite.

## Code style

- Use the existing style in the codebase (Black-style formatting, type hints where helpful).
- New tools or resources should follow the same patterns as in `src/mcp_sql_bridge/server.py`.

## Release process

1. Bump version in `pyproject.toml` and add an entry to `CHANGELOG.md`.
2. Tag the release: `git tag v0.x.x`
3. Push the tag: `git push origin v0.x.x`
4. (Optional) Publish to PyPI: see the [Publish to PyPI](#publish-to-pypi) section in the repo docs or release checklist.

## Publish to PyPI

- Build: `poetry build`
- Upload to TestPyPI: `poetry config repositories.testpypi https://test.pypi.org/legacy/` then `poetry publish -r testpypi`
- Upload to PyPI: `poetry publish` (requires PyPI credentials).

## Questions or ideas?

Open a [GitHub Discussion](https://github.com/firas-mcp-servers/mcp-sql-bridge/discussions) or an [Issue](https://github.com/firas-mcp-servers/mcp-sql-bridge/issues).
