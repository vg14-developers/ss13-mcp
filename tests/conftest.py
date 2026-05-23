from pathlib import Path

import pytest

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "mini-vg13"
INDEX_DIR = FIXTURE_DIR / "index"


def _bake_fixture_index() -> None:
    """Generate index/ for the fixture so DM-query tests have data."""
    if INDEX_DIR.exists():
        return
    from pipeline.build_dm_index import massage_dmm_output

    records = [
        {
            "path": "/datum",
            "parent": None,
            "vars": [],
            "procs": [],
            "file": "code/datum.dm",
            "line": 1,
        },
        {
            "path": "/atom",
            "parent": "/datum",
            "vars": [],
            "procs": [],
            "file": "code/atom.dm",
            "line": 1,
        },
        {
            "path": "/obj",
            "parent": "/atom",
            "vars": [],
            "procs": [],
            "file": "code/obj.dm",
            "line": 1,
        },
        {
            "path": "/obj/test",
            "parent": "/obj",
            "vars": [],
            "procs": [],
            "file": "code/test.dm",
            "line": 1,
        },
        {
            "path": "/obj/test/widget",
            "parent": "/obj/test",
            "vars": [{"name": "charge", "value": "0"}],
            "procs": [{"name": "zap"}, {"name": "attack_self"}],
            "file": "code/modules/test/widget.dm",
            "line": 1,
        },
        {
            "path": "/obj/test/widget/super",
            "parent": "/obj/test/widget",
            "vars": [{"name": "charge", "value": "100"}],
            "procs": [{"name": "megazap"}],
            "file": "code/modules/test/super_widget.dm",
            "line": 1,
        },
    ]
    massage_dmm_output(records, INDEX_DIR)


_bake_fixture_index()


def _bake_fixture_wiki() -> None:
    wiki_dir = FIXTURE_DIR / "wiki"
    if wiki_dir.exists():
        return
    from pipeline.crawl_wiki import html_to_markdown_bundle

    html_to_markdown_bundle(FIXTURE_DIR / "wiki_html", wiki_dir)


_bake_fixture_wiki()


@pytest.fixture
def fixture_snapshot(monkeypatch, tmp_path):
    monkeypatch.setenv("VG_SNAPSHOT_DIR", str(FIXTURE_DIR))
    monkeypatch.setenv("VG_CACHE_DIR", str(tmp_path / "cache"))
    return FIXTURE_DIR
