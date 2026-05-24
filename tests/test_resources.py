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


def test_register_wiki_resources_uses_public_fastmcp_api(fixture_snapshot):
    """Closes issue #3: register via mcp.add_resource (public) not _mcp_server (private).

    If a future mcp SDK bump renames add_resource or FunctionResource, this test
    catches it at import time instead of at runtime under a real client.
    """
    from vgstation13_mcp.server import mcp, register_wiki_resources

    count = register_wiki_resources()
    assert count > 0, "fixture wiki should register at least one resource"
    listed = {str(r.uri) for r in mcp._resource_manager._resources.values()}
    assert any(uri.startswith("vg13://wiki/") for uri in listed)
