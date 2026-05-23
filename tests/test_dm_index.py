import pytest

from vgstation13_mcp.tools.dm_index import get_type, list_subtypes


def test_get_type_returns_full_record(fixture_snapshot):
    info = get_type("/obj/test/widget")
    assert info["parent"] == "/obj/test"
    assert {"name": "charge", "value": "0"} in info["vars"]
    assert "zap" in info["procs"]
    assert info["file"] == "code/modules/test/widget.dm"
    assert info["line"] == 1


def test_get_type_missing(fixture_snapshot):
    with pytest.raises(KeyError):
        get_type("/obj/test/nonexistent")


def test_list_subtypes_direct(fixture_snapshot):
    kids = list_subtypes("/obj/test/widget")
    assert kids == ["/obj/test/widget/super"]


def test_list_subtypes_transitive(fixture_snapshot):
    kids = list_subtypes("/obj/test", transitive=True)
    assert "/obj/test/widget" in kids
    assert "/obj/test/widget/super" in kids
