from pathlib import Path

import pytest
from pydantic import AnyUrl

from mcp_sql_bridge.server import _is_readme_uri, _readme_path, _readme_uri


def test_readme_uri_points_to_readme(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Change cwd so _readme_path/_readme_uri point into tmp_path
    monkeypatch.chdir(tmp_path)
    path = _readme_path()
    assert path == tmp_path / "README.md"

    uri = _readme_uri()
    # Simple sanity checks: file:// URI and path component ends with README.md
    assert uri.startswith("file://")
    assert uri.endswith("/README.md")


def test_is_readme_uri_matches_exact(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    uri = _readme_uri()
    assert _is_readme_uri(AnyUrl(uri))
    # Trailing slash variation should also match
    assert _is_readme_uri(AnyUrl(uri.rstrip("/") + "/"))

