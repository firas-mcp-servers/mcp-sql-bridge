#!/usr/bin/env python3
"""
Run Postgres and MySQL via Docker, populate them, call MCP tools, and print results.

Requires: Docker, docker compose, and: poetry install --extras pro

Usage (from project root):
  poetry run python scripts/run_docker_integration.py
"""

import subprocess
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
COMPOSE_FILE = PROJECT_ROOT / "docker-compose.test.yml"
POSTGRES_URL = "postgresql://testuser:testpass@127.0.0.1:15432/testdb"
MYSQL_URL = "mysql://testuser:testpass@127.0.0.1:13306/testdb"


def run(*args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        args,
        capture_output=True,
        text=True,
        timeout=120,
        cwd=PROJECT_ROOT,
    )


def wait_for_postgres(timeout: float = 45.0) -> bool:
    import psycopg

    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            conn = psycopg.connect(POSTGRES_URL)
            conn.close()
            return True
        except Exception:
            time.sleep(0.5)
    return False


def wait_for_mysql(timeout: float = 45.0) -> bool:
    from urllib.parse import urlparse

    import pymysql

    p = urlparse(MYSQL_URL)
    kwargs = {
        "host": p.hostname or "127.0.0.1",
        "port": p.port or 3306,
        "user": p.username,
        "password": p.password,
        "database": (p.path or "").strip("/"),
    }
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            conn = pymysql.connect(**kwargs)
            conn.close()
            return True
        except Exception:
            time.sleep(0.5)
    return False


def populate_postgres() -> None:
    import psycopg

    conn = psycopg.connect(POSTGRES_URL)
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS widgets (
                    id SERIAL PRIMARY KEY,
                    name TEXT NOT NULL,
                    price NUMERIC(10,2)
                );
            """)
            cur.execute("DELETE FROM widgets")
            cur.execute(
                "INSERT INTO widgets (name, price) VALUES ('Widget A', 9.99), ('Widget B', 19.99)"
            )
        conn.commit()
    finally:
        conn.close()


def populate_mysql() -> None:
    from urllib.parse import urlparse

    import pymysql

    p = urlparse(MYSQL_URL)
    conn = pymysql.connect(
        host=p.hostname or "127.0.0.1",
        port=p.port or 3306,
        user=p.username,
        password=p.password,
        database=(p.path or "").strip("/"),
    )
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS widgets (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    price DECIMAL(10,2)
                );
            """)
            cur.execute("DELETE FROM widgets")
            cur.execute(
                "INSERT INTO widgets (name, price) VALUES ('Widget A', 9.99), ('Widget B', 19.99)"
            )
        conn.commit()
    finally:
        conn.close()


def main() -> int:
    sys.path.insert(0, str(PROJECT_ROOT))
    from mcp_sql_bridge.server import _execute_readonly_query_impl, _list_tables_impl

    if not COMPOSE_FILE.exists():
        print("ERROR: docker-compose.test.yml not found", file=sys.stderr)
        return 1

    print("Starting Postgres and MySQL (docker compose up -d)...")
    r = run("docker", "compose", "-f", str(COMPOSE_FILE), "up", "-d")
    if r.returncode != 0:
        print("ERROR: docker compose up failed:", r.stderr, file=sys.stderr)
        return 1

    try:
        print("Waiting for Postgres...")
        if not wait_for_postgres():
            print("ERROR: Postgres did not become ready", file=sys.stderr)
            return 1
        print("Waiting for MySQL...")
        if not wait_for_mysql():
            print("ERROR: MySQL did not become ready", file=sys.stderr)
            return 1

        print("Populating Postgres and MySQL...")
        populate_postgres()
        populate_mysql()

        print("\n" + "=" * 60)
        print("MCP TOOL: list_tables (Postgres)")
        print("=" * 60)
        out = _list_tables_impl("", backend="postgres", connection_string=POSTGRES_URL)
        print(out)

        print("\n" + "=" * 60)
        print("MCP TOOL: execute_readonly_query (Postgres)")
        print("=" * 60)
        out = _execute_readonly_query_impl(
            "",
            "SELECT id, name, price FROM public.widgets ORDER BY id",
            backend="postgres",
            connection_string=POSTGRES_URL,
        )
        print(out)

        print("\n" + "=" * 60)
        print("MCP TOOL: list_tables (MySQL)")
        print("=" * 60)
        out = _list_tables_impl("", backend="mysql", connection_string=MYSQL_URL)
        print(out)

        print("\n" + "=" * 60)
        print("MCP TOOL: execute_readonly_query (MySQL)")
        print("=" * 60)
        out = _execute_readonly_query_impl(
            "",
            "SELECT id, name, price FROM widgets ORDER BY id",
            backend="mysql",
            connection_string=MYSQL_URL,
        )
        print(out)

        print("\n" + "=" * 60)
        print("Done. Containers left running; stop with:")
        print("  docker compose -f docker-compose.test.yml down")
        print("=" * 60)
        return 0
    finally:
        # Optionally tear down; comment out to leave running for inspection
        # print("Stopping containers...")
        # run("docker", "compose", "-f", str(COMPOSE_FILE), "down", "-v")
        pass


if __name__ == "__main__":
    sys.exit(main())
