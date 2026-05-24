import json
import subprocess

import pytest

from ss13_mcp.pipeline import build_dm_index
from ss13_mcp.pipeline.build_dm_index import massage_dmm_output, run_dm_dump


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


# --- run_dm_dump error handling (issue #16) ---


def test_run_dm_dump_surfaces_stderr_on_failure(monkeypatch, tmp_path):
    """A failing dm-dump invocation must raise with the real stderr, not silently leave a 0-byte file."""
    out = tmp_path / "dmm-raw.json"
    expected_stderr = "dm-dump: preprocessor failed"

    def fake_run(cmd, **kwargs):
        # Mimic subprocess.run with check=True hitting a non-zero exit.
        raise subprocess.CalledProcessError(
            returncode=2, cmd=cmd, output=None, stderr=expected_stderr
        )

    monkeypatch.setattr(build_dm_index.subprocess, "run", fake_run)
    with pytest.raises(RuntimeError, match=expected_stderr):
        run_dm_dump(tmp_path, out)
    # The 0-byte file we opened for writing must be cleaned up.
    assert not out.exists(), "failed run must clean up the partial output file"


def test_run_dm_dump_handles_missing_binary(monkeypatch, tmp_path):
    out = tmp_path / "dmm-raw.json"

    def fake_run(cmd, **kwargs):
        raise FileNotFoundError(2, "No such file", cmd[0])

    monkeypatch.setattr(build_dm_index.subprocess, "run", fake_run)
    with pytest.raises(RuntimeError, match="dm-dump binary not found"):
        run_dm_dump(tmp_path, out)
    assert not out.exists()


def test_run_dm_dump_falls_back_when_stderr_empty(monkeypatch, tmp_path):
    """Failure with no stderr text still produces an actionable RuntimeError."""
    out = tmp_path / "dmm-raw.json"

    def fake_run(cmd, **kwargs):
        raise subprocess.CalledProcessError(returncode=2, cmd=cmd, output=None, stderr="")

    monkeypatch.setattr(build_dm_index.subprocess, "run", fake_run)
    with pytest.raises(RuntimeError, match=r"\(no stderr\)"):
        run_dm_dump(tmp_path, out)
    assert not out.exists()


def test_run_dm_dump_writes_output_on_success(monkeypatch, tmp_path):
    out = tmp_path / "nested" / "dmm-raw.json"

    def fake_run(cmd, stdout=None, **kwargs):
        stdout.write('{"path": "/datum"}\n')
        return subprocess.CompletedProcess(cmd, 0, stdout=None, stderr="")

    monkeypatch.setattr(build_dm_index.subprocess, "run", fake_run)
    run_dm_dump(tmp_path, out)
    assert out.exists()
    assert '{"path": "/datum"}' in out.read_text()
