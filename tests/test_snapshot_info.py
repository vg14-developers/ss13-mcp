from datetime import datetime

from vgstation13_mcp.tools.meta import snapshot_info


def test_snapshot_info_reports_configured(fixture_snapshot):
    info = snapshot_info()
    assert info["configured"] is True
    assert info["vg13_sha"] == "fixturefixturefixturefixturefixturefix"
    datetime.fromisoformat(info["bumped_at"])
    assert info["dm_types_count"] >= 1


def test_snapshot_info_unconfigured(monkeypatch, tmp_path):
    monkeypatch.setenv("VG_SNAPSHOT_DIR", str(tmp_path / "empty"))
    monkeypatch.delenv("VG13_PATH", raising=False)
    info = snapshot_info()
    assert info["configured"] is False
    assert "setup" in info["message"].lower()
