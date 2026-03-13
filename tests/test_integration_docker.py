"""
Integration tests: Postgres and MySQL via Docker.

Requires: Docker, docker compose, and optional deps: poetry install --extras pro

Start containers and run:
  docker compose -f docker-compose.test.yml up -d
  poetry run pytest tests/test_integration_docker.py -v -s

Or use scripts/run_docker_integration.py to see MCP tool output.
"""

import pytest
from conftest import populate_mysql, populate_postgres

# Import MCP impls (require pro extras for postgres/mysql)
try:
    from mcp_sql_bridge.server import (
        _execute_readonly_query_impl,
        _list_tables_impl,
    )

    HAS_MCP = True
except ImportError:
    HAS_MCP = False

pytestmark = [
    pytest.mark.skipif(not HAS_MCP, reason="mcp_sql_bridge not installed"),
]


class TestPostgresDocker:
    """Test MCP list_tables and execute_readonly_query against Postgres in Docker."""

    def test_list_tables_postgres(self, docker_services):
        populate_postgres(docker_services["postgres_url"])
        result = _list_tables_impl(
            "",
            backend="postgres",
            connection_string=docker_services["postgres_url"],
        )
        assert "widgets" in result
        assert "id" in result and "name" in result and "price" in result
        print("\n--- list_tables (Postgres) ---\n" + result)

    def test_execute_readonly_query_postgres(self, docker_services):
        populate_postgres(docker_services["postgres_url"])
        result = _execute_readonly_query_impl(
            "",
            "SELECT id, name, price FROM public.widgets ORDER BY id",
            backend="postgres",
            connection_string=docker_services["postgres_url"],
        )
        assert "Widget A" in result and "Widget B" in result
        assert "9.99" in result and "19.99" in result
        print("\n--- execute_readonly_query (Postgres) ---\n" + result)


class TestMySQLDocker:
    """Test MCP list_tables and execute_readonly_query against MySQL in Docker."""

    def test_list_tables_mysql(self, docker_services):
        populate_mysql(docker_services["mysql_url"])
        result = _list_tables_impl(
            "",
            backend="mysql",
            connection_string=docker_services["mysql_url"],
        )
        assert "widgets" in result
        assert "id" in result and "name" in result and "price" in result
        print("\n--- list_tables (MySQL) ---\n" + result)

    def test_execute_readonly_query_mysql(self, docker_services):
        populate_mysql(docker_services["mysql_url"])
        result = _execute_readonly_query_impl(
            "",
            "SELECT id, name, price FROM widgets ORDER BY id",
            backend="mysql",
            connection_string=docker_services["mysql_url"],
        )
        assert "Widget A" in result and "Widget B" in result
        assert "9.99" in result and "19.99" in result
        print("\n--- execute_readonly_query (MySQL) ---\n" + result)
