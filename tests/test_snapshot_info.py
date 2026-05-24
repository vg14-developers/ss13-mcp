from datetime import datetime

from ss13_mcp.tools.meta import snapshot_info


def test_snapshot_info_reports_configured(fixture_snapshot):
    info = snapshot_info()
    assert info["configured"] is True
    assert info["ss13_sha"] == "fixturefixturefixturefixturefixturefix"
    assert info["fork"] == "vg"
    datetime.fromisoformat(info["bumped_at"])
    assert info["dm_types_count"] >= 1


def test_snapshot_info_unconfigured(monkeypatch, tmp_path):
    monkeypatch.setenv("SS13_SNAPSHOT_DIR", str(tmp_path / "empty"))
    monkeypatch.delenv("SS13_PATH", raising=False)
    info = snapshot_info()
    assert info["configured"] is False
    assert "setup" in info["message"].lower()
