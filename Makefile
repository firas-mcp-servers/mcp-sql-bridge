# MCP SQL Bridge — common commands
# Usage: make [target]

.PHONY: install install-web test lint format check docker-up docker-down docker-test run-mcp run-web help

# Default target
help:
	@echo "MCP SQL Bridge — common targets:"
	@echo "  make install       Install core dependencies (poetry install)"
	@echo "  make install-web   Install with web extra (poetry install --with web)"
	@echo "  make test          Run pytest"
	@echo "  make lint          Run ruff check"
	@echo "  make format        Run ruff format"
	@echo "  make check         Lint + format check (CI)"
	@echo "  make docker-up     Start Postgres+MySQL for integration tests"
	@echo "  make docker-down   Stop integration test containers"
	@echo "  make docker-test   Run Docker integration tests"
	@echo "  make run-mcp       Run MCP server (stdio)"
	@echo "  make run-web       Run web server (port 8000)"

install:
	poetry install

install-web:
	poetry install --with web

test:
	poetry run pytest -v

lint:
	poetry run ruff check .

format:
	poetry run ruff format .

check: lint format
	@echo "Lint and format check passed."

docker-up:
	docker compose -f docker-compose.test.yml up -d

docker-down:
	docker compose -f docker-compose.test.yml down

docker-test: docker-up
	poetry run pytest tests/test_integration_docker.py -v -s
	$(MAKE) docker-down

run-mcp:
	poetry run mcp-sql-bridge

run-web:
	poetry run mcp-sql-bridge-web
