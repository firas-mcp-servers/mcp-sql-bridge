# Deprecation and support policy

## Versioning

`mcp-sql-bridge` follows [Semantic Versioning](https://semver.org/):

- **Patch** (`0.2.x`): bug fixes, security patches, documentation. No breaking changes.
- **Minor** (`0.x.0`): new features, new optional backends, new MCP tools. Backwards-compatible.
- **Major** (`x.0.0`): breaking changes to the public interface (tool signatures, config env vars, wire format). Announced with a migration guide in `CHANGELOG.md`.

## Supported Python versions

| Python | Status |
|--------|--------|
| 3.13   | ✅ Supported |
| 3.12   | ✅ Supported |
| 3.11   | ✅ Supported |
| 3.10   | ⬜ Not tested (may work) |
| < 3.10 | ❌ Not supported |

Python versions are dropped 12 months after they reach [end-of-life](https://devguide.python.org/versions/).

## MCP SDK compatibility

The server targets the current stable MCP Python SDK. When breaking changes occur in the SDK, a new minor or major version of `mcp-sql-bridge` will be released.

## Deprecation process

1. A feature to be removed is marked **deprecated** in a minor release. The relevant code emits a `DeprecationWarning` at import or call time and the change is noted in `CHANGELOG.md`.
2. The deprecated feature is removed in the **next major release**, no sooner than **3 months** after the deprecation notice.
3. Migration instructions are included in `CHANGELOG.md` and, if significant, in `docs/`.

## Security patches

Security fixes are back-ported to the current stable release branch and released as a patch version within **7 days** of a verified report. See `docs/SECURITY.md` for reporting.

## End-of-life

When the project reaches end-of-life (unlikely before 1.0 is stable), a notice will be posted in the README and repository description with at least **6 months** of warning.
