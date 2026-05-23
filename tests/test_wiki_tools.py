import pytest

from vgstation13_mcp.tools.wiki import wiki_read, wiki_search


def test_wiki_search_finds_page(fixture_snapshot):
    hits = wiki_search("widget")
    pages = {h["page"] for h in hits}
    assert "Widget" in pages
    assert "Super_widget" in pages
    for h in hits:
        assert "excerpt" in h


def test_wiki_search_no_match(fixture_snapshot):
    assert wiki_search("zzzzznonexistentzzzz") == []


def test_wiki_read_returns_markdown(fixture_snapshot):
    text = wiki_read("Widget")
    assert text.startswith("# Widget")


def test_wiki_read_missing(fixture_snapshot):
    with pytest.raises(FileNotFoundError):
        wiki_read("DoesNotExist")
