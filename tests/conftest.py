from pathlib import Path

import pytest

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "mini-vg13"


@pytest.fixture
def fixture_snapshot(monkeypatch, tmp_path):
    """Point the server at the fixture snapshot dir."""
    monkeypatch.setenv("VG_SNAPSHOT_DIR", str(FIXTURE_DIR))
    monkeypatch.setenv("VG_CACHE_DIR", str(tmp_path / "cache"))
    return FIXTURE_DIR
