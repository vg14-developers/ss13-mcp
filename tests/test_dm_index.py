import pytest

from ss13_mcp.tools.dm_index import find_proc, find_var, get_type, list_subtypes, path_lookup


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


def test_find_proc_unscoped(fixture_snapshot):
    hits = find_proc("zap")
    assert len(hits) == 1
    assert hits[0]["type"] == "/obj/test/widget"


def test_find_proc_scoped(fixture_snapshot):
    hits = find_proc("megazap", scope="/obj/test/widget")
    assert len(hits) == 1
    assert hits[0]["type"] == "/obj/test/widget/super"


def test_find_var_finds_charge(fixture_snapshot):
    hits = find_var("charge")
    types = {h["type"] for h in hits}
    assert "/obj/test/widget" in types
    assert "/obj/test/widget/super" in types


def test_path_lookup_exact(fixture_snapshot):
    cands = path_lookup("/obj/test/widget")
    assert cands[0]["path"] == "/obj/test/widget"


def test_path_lookup_fuzzy(fixture_snapshot):
    cands = path_lookup("widgit")  # typo
    paths = [c["path"] for c in cands]
    assert "/obj/test/widget" in paths
