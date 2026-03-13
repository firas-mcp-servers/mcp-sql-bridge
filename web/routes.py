"""API routes for FastAPI (enables OpenAPI / Swagger / ReDoc)."""

import time
from collections import Counter
from typing import Any

from fastapi import APIRouter, Request
from pydantic import BaseModel

api_router = APIRouter()

# Simple in-process counters for structured metrics (#27)
_start_time = time.time()
_request_counts: Counter[str] = Counter()


# ── Health / readiness (#26) ──────────────────────────────────────────────────


class HealthResponse(BaseModel):
    status: str
    service: str


class ReadyResponse(BaseModel):
    ready: bool
    service: str
    uptime_seconds: float


@api_router.get("/health", response_model=HealthResponse, tags=["ops"])
async def health() -> HealthResponse:
    """Liveness check — returns 200 if the process is running."""
    return HealthResponse(status="ok", service="mcp-sql-bridge-web")


@api_router.get("/ready", response_model=ReadyResponse, tags=["ops"])
async def ready() -> ReadyResponse:
    """Readiness check — returns 200 when the server is ready to serve traffic."""
    return ReadyResponse(
        ready=True,
        service="mcp-sql-bridge-web",
        uptime_seconds=round(time.time() - _start_time, 2),
    )


# ── Info ──────────────────────────────────────────────────────────────────────


class InfoResponse(BaseModel):
    name: str
    version: str
    description: str


@api_router.get("/info", response_model=InfoResponse, tags=["ops"])
async def info() -> InfoResponse:
    """Basic service info."""
    return InfoResponse(
        name="MCP SQL Bridge",
        version="0.2.0",
        description="MCP server for read-only SQL (SQLite, PostgreSQL, MySQL).",
    )


# ── Structured metrics (#27) ──────────────────────────────────────────────────


class MetricsResponse(BaseModel):
    uptime_seconds: float
    requests_by_path: dict[str, int]
    total_requests: int


@api_router.get("/metrics", response_model=MetricsResponse, tags=["ops"])
async def metrics(request: Request) -> MetricsResponse:
    """Structured request-count metrics (lightweight, no external deps)."""
    _request_counts[request.url.path] += 1
    return MetricsResponse(
        uptime_seconds=round(time.time() - _start_time, 2),
        requests_by_path=dict(_request_counts),
        total_requests=sum(_request_counts.values()),
    )


def record_request(path: str) -> None:
    """Call from middleware or route handlers to track a request."""
    _request_counts[path] += 1


# ── Middleware to auto-count all requests ────────────────────────────────────
# Installed in main.py via app.middleware("http")


async def count_requests_middleware(request: Request, call_next: Any) -> Any:
    record_request(request.url.path)
    return await call_next(request)
