import base64

import pytest

from vgstation13_mcp.tools.assets import list_dmi_states, read_asset


def test_read_asset_returns_base64(fixture_snapshot):
    out = read_asset("sound/blip.ogg")
    decoded = base64.b64decode(out["bytes_b64"])
    assert decoded.startswith(b"OggS")
    assert out["size"] == len(decoded)
    assert out["mime"] == "audio/ogg"


def test_read_asset_missing(fixture_snapshot):
    with pytest.raises(FileNotFoundError):
        read_asset("sound/missing.ogg")


def test_list_dmi_states_returns_idle_and_active(fixture_snapshot):
    states = list_dmi_states("icons/test.dmi")
    names = {s["name"] for s in states}
    assert names == {"idle", "active"}
    for s in states:
        assert s["dirs"] == 1
        assert s["frames"] == 1
