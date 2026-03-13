"""Pytest fixtures, including Docker-based Postgres/MySQL for integration tests."""

import subprocess
import time
from pathlib import Path

import pytest

COMPOSE_FILE = Path(__file__).resolve().parent.parent / "docker-compose.test.yml"
POSTGRES_URL = "postgresql://testuser:testpass@127.0.0.1:15432/testdb"
MYSQL_URL = "mysql://testuser:testpass@127.0.0.1:13306/testdb"


def _docker_compose(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["docker", "compose", "-f", str(COMPOSE_FILE)] + list(args),
        capture_output=True,
        text=True,
        timeout=120,
        cwd=COMPOSE_FILE.parent,
    )


def _wait_for_postgres(url: str, timeout: float = 30.0) -> bool:
    try:
        import psycopg
    except ImportError:
        return False
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            conn = psycopg.connect(url)
            conn.close()
            return True
        except Exception:
            time.sleep(0.5)
    return False


def _wait_for_mysql(url: str, timeout: float = 30.0) -> bool:
    try:
        import pymysql
    except ImportError:
        return False
    from urllib.parse import urlparse

    parsed = urlparse(url)
    kwargs = {
        "host": parsed.hostname or "127.0.0.1",
        "port": parsed.port or 3306,
        "user": parsed.username or "",
        "password": parsed.password or "",
        "database": (parsed.path or "").strip("/"),
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


@pytest.fixture(scope="module")
def docker_services():
    """Start Postgres and MySQL with docker compose; yield connection URLs; teardown."""
    if not COMPOSE_FILE.exists():
        pytest.skip("docker-compose.test.yml not found")
    out = _docker_compose("up", "-d")
    if out.returncode != 0:
        pytest.skip(f"docker compose up failed: {out.stderr}")
    try:
        if not _wait_for_postgres(POSTGRES_URL):
            pytest.skip("Postgres did not become ready")
        if not _wait_for_mysql(MYSQL_URL):
            pytest.skip("MySQL did not become ready")
        yield {"postgres_url": POSTGRES_URL, "mysql_url": MYSQL_URL}
    finally:
        _docker_compose("down", "-v")


def populate_postgres(url: str) -> None:
    import psycopg

    conn = psycopg.connect(url)
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


def populate_mysql(url: str) -> None:
    from urllib.parse import urlparse

    import pymysql

    p = urlparse(url)
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
