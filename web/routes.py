"""API routes for FastAPI (enables OpenAPI / Swagger / ReDoc)."""

from fastapi import APIRouter
from pydantic import BaseModel

api_router = APIRouter()


class HealthResponse(BaseModel):
    status: str
    service: str


@api_router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Health check for the web server."""
    return HealthResponse(status="ok", service="mcp-sql-bridge-web")


class InfoResponse(BaseModel):
    name: str
    version: str
    description: str


@api_router.get("/info", response_model=InfoResponse)
async def info() -> InfoResponse:
    """Basic service info."""
    return InfoResponse(
        name="MCP SQL Bridge",
        version="0.2.0",
        description="MCP server for read-only SQL (SQLite, PostgreSQL, MySQL).",
    )
