import pytest

from vgstation13_mcp.resources import read_resource


def test_read_source_resource(fixture_snapshot):
    content, mime = read_resource("vg13://source/code/modules/test/widget.dm")
    assert "/obj/test/widget" in content
    assert mime == "text/plain"


def test_read_wiki_resource(fixture_snapshot):
    content, mime = read_resource("vg13://wiki/Widget")
    assert content.startswith("# Widget")
    assert mime == "text/markdown"


def test_read_unknown_scheme(fixture_snapshot):
    with pytest.raises(ValueError, match="unknown URI scheme"):
        read_resource("foo://bar")


def test_read_unknown_resource_kind(fixture_snapshot):
    with pytest.raises(ValueError, match="unknown resource"):
        read_resource("vg13://nonsense/x")
