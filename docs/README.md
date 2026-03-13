# MCP SQL Bridge — Documentation hub

This folder contains additional documentation for [MCP SQL Bridge](https://github.com/firas-mcp-servers/mcp-sql-bridge).

| Document | Description |
|----------|-------------|
| [SECURITY.md](SECURITY.md) | Security and hardening: read-only design, env vars, deployment practices. |
| [ERROR_TAXONOMY.md](ERROR_TAXONOMY.md) | Error categories and how errors are surfaced to the AI. |
| [PRICING_AND_LICENSING.md](PRICING_AND_LICENSING.md) | Licensing (MIT), free vs optional Pro, and future paid offerings. |
| [LAUNCH_AND_MARKETING.md](LAUNCH_AND_MARKETING.md) | Launch plan, channels, messaging, and checklist. |
| [FUTURE.md](FUTURE.md) | Future ideas and roadmap beyond 0.2.x. |
| [SPRINT_PLAN.md](SPRINT_PLAN.md) | Next 5 sprints (issues and milestones). |

For quick start, installation, and usage with Cursor or Claude Desktop, see the [main README](../README.md) in the repository root.

**Web server:** The repo includes an optional FastAPI app (landing page, Swagger at `/docs`, ReDoc at `/redoc`, and this documentation at `/documentation` after `mkdocs build`). Run with `poetry install --with web` then `poetry run mcp-sql-bridge-web`.
