from datetime import datetime

from vgstation13_mcp.tools.meta import snapshot_info


def test_snapshot_info_reports_fixture_sha(fixture_snapshot):
    info = snapshot_info()
    assert info["vg13_sha"] == "fixturefixturefixturefixturefixturefix"
    assert isinstance(info["bumped_at"], str)
    # Should parse as ISO 8601.
    datetime.fromisoformat(info["bumped_at"])
    assert info["wiki_pages"] == 2
    assert info["dm_types_count"] >= 0  # index not built yet
