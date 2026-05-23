import pytest

from vgstation13_mcp.tools.source import list_dir, read_file, search_files


def test_list_dir_returns_entries(fixture_snapshot):
    entries = list_dir("code/modules/test")
    names = {e["name"] for e in entries}
    assert names == {"widget.dm", "super_widget.dm"}
    assert all(e["type"] == "file" for e in entries)


def test_list_dir_rejects_escape(fixture_snapshot):
    with pytest.raises(ValueError, match="outside snapshot"):
        list_dir("../../../etc")


def test_read_file_full(fixture_snapshot):
    content = read_file("code/modules/test/widget.dm")
    assert "/obj/test/widget" in content
    assert "proc/zap()" in content


def test_read_file_range(fixture_snapshot):
    content = read_file("code/modules/test/widget.dm", range=[1, 3])
    lines = content.splitlines()
    assert len(lines) == 3
    assert lines[0].startswith("/obj/test/widget")


def test_read_file_missing(fixture_snapshot):
    with pytest.raises(FileNotFoundError):
        read_file("code/does/not/exist.dm")


def test_search_files_finds_matches(fixture_snapshot):
    hits = search_files("widget", glob="code/**/*.dm")
    assert len(hits) >= 2
    paths = {h["path"] for h in hits}
    assert "code/modules/test/widget.dm" in paths
    for hit in hits:
        assert "line" in hit
        assert "text" in hit


def test_search_files_glob_narrows(fixture_snapshot):
    hits = search_files("widget", glob="code/modules/test/super_widget.dm")
    assert all(h["path"] == "code/modules/test/super_widget.dm" for h in hits)
