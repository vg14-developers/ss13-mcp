import json

from pipeline.build_dm_index import massage_dmm_output


def test_massage_produces_expected_indices(tmp_path):
    # Synthetic dmm-tools dump-types output (NDJSON-ish).
    dmm_output = [
        {
            "path": "/obj",
            "parent": "/datum",
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
            "line": 2,
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
            "vars": [],
            "procs": [{"name": "megazap"}],
            "file": "code/modules/test/super_widget.dm",
            "line": 1,
        },
    ]
    out_dir = tmp_path / "index"
    massage_dmm_output(dmm_output, out_dir)

    types = json.loads((out_dir / "types.json").read_text())
    assert "/obj/test/widget" in types
    assert types["/obj/test/widget"]["parent"] == "/obj/test"
    assert types["/obj/test/widget"]["children"] == ["/obj/test/widget/super"]

    procs = json.loads((out_dir / "procs.json").read_text())
    assert "zap" in procs
    assert {"type": "/obj/test/widget", "file": "code/modules/test/widget.dm", "line": 1} in procs[
        "zap"
    ]
    assert "megazap" in procs

    paths = (out_dir / "paths.idx").read_text().splitlines()
    assert "/obj/test/widget" in paths
    assert "/obj/test/widget/super" in paths
