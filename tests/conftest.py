import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

FIXTURE_VG13 = Path(__file__).parent / "fixtures" / "mini-vg13"
FIXTURE_SHA = (FIXTURE_VG13 / "SHA").read_text().strip()


def _bake_index(out_dir: Path) -> None:
    """Generate index/ from a synthetic dmm-tools dump so DM-query tests have data."""
    from vgstation13_mcp.pipeline.build_dm_index import massage_dmm_output

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
            "vars": [],
            "procs": [],
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
        {
            "path": "/obj/test/widget",
            "parent": "/obj/test",
            "vars": [{"name": "charge", "value": "0"}],
            "procs": [{"name": "zap"}, {"name": "attack_self"}],
            "file": "code/modules/test/widget.dm",
            "line": 1,
        },
    ]
    massage_dmm_output(records, out_dir)


@pytest.fixture
def fixture_snapshot(monkeypatch, tmp_path):
    """Stand up a fresh per-test snapshot dir + config pointing at the fixture vg13."""
    snap = tmp_path / "snapshot"
    snap.mkdir()
    _bake_index(snap / "index")
    (snap / "config.json").write_text(
        json.dumps(
            {
                "vg13_path": str(FIXTURE_VG13),
                "vg13_sha": FIXTURE_SHA,
                "bumped_at": datetime.now(timezone.utc).isoformat(),
            }
        )
    )
    monkeypatch.setenv("VG_SNAPSHOT_DIR", str(snap))
    monkeypatch.setenv("VG13_PATH", str(FIXTURE_VG13))
    monkeypatch.setenv("VG_CACHE_DIR", str(tmp_path / "cache"))
    return snap
