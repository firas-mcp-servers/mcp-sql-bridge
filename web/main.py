"""FastAPI web app: landing page, Swagger, and documentation."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from .routes import api_router

# Paths relative to this file
WEB_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = WEB_DIR.parent
DOCS_SITE = PROJECT_ROOT / "site"  # mkdocs build output

app = FastAPI(
    title="MCP SQL Bridge",
    description="Give your AI read-only access to SQL databases (SQLite, PostgreSQL, MySQL) over the Model Context Protocol.",
    version="0.2.0",
    docs_url=None,  # we mount custom /docs (Swagger) and /redoc
    redoc_url=None,
)

app.include_router(api_router, prefix="/api", tags=["api"])

# Serve MkDocs site at /documentation if built
if DOCS_SITE.exists() and (DOCS_SITE / "index.html").exists():
    app.mount(
        "/documentation", StaticFiles(directory=str(DOCS_SITE), html=True), name="documentation"
    )


@app.get("/", response_class=HTMLResponse)
async def home() -> HTMLResponse:
    """Landing page."""
    html = (WEB_DIR / "templates" / "index.html").read_text(encoding="utf-8")
    return HTMLResponse(html)


@app.get("/docs", response_class=HTMLResponse, include_in_schema=False)
async def swagger_ui() -> HTMLResponse:
    """Swagger UI at /docs."""
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=f"{app.title} — Swagger UI",
    )


@app.get("/redoc", response_class=HTMLResponse, include_in_schema=False)
async def redoc() -> HTMLResponse:
    """ReDoc at /redoc."""
    from fastapi.openapi.docs import get_redoc_html

    return get_redoc_html(
        openapi_url=app.openapi_url,
        title=f"{app.title} — ReDoc",
    )


@app.get("/documentation")
async def documentation_redirect():
    """Redirect /documentation to the docs site index if built, else info page."""
    if DOCS_SITE.exists() and (DOCS_SITE / "index.html").exists():
        return RedirectResponse(url="/documentation/", status_code=302)
    # No built site: return simple info
    return HTMLResponse(
        "<!DOCTYPE html><html><head><title>Documentation</title></head><body>"
        "<h1>Documentation</h1><p>Build the docs with: <code>mkdocs build</code></p>"
        "<p>Then restart the server. Or see the <a href='/docs'>Swagger UI</a> and <a href='/redoc'>ReDoc</a> for the API.</p>"
        "</body></html>"
    )


def run() -> None:
    """Entry point for the web server (poetry run mcp-sql-bridge-web)."""
    import os
    import sys

    # Ensure project root is on path so "web" package is found when run via console script
    _root = WEB_DIR.parent
    if str(_root) not in sys.path:
        sys.path.insert(0, str(_root))
    import uvicorn

    host = os.environ.get("MCP_SQL_BRIDGE_WEB_HOST", "0.0.0.0")
    port_str = os.environ.get("MCP_SQL_BRIDGE_WEB_PORT", "8000")
    try:
        port = int(port_str)
    except ValueError:
        port = 8000
    uvicorn.run(app, host=host, port=port)
