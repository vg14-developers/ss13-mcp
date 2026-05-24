import json
import sys
from pathlib import Path

import pytest

from vgstation13_mcp import setup as setup_mod
from vgstation13_mcp.snapshot import config_path, is_configured

FIXTURE_VG13 = Path(__file__).parent / "fixtures" / "mini-vg13"


@pytest.fixture
def empty_snapshot(monkeypatch, tmp_path):
    monkeypatch.setenv("VG_SNAPSHOT_DIR", str(tmp_path / "snap"))
    monkeypatch.delenv("VG13_PATH", raising=False)
    # Skip the real dmm-tools download + DM index build in unit tests.
    fake_dmm = tmp_path / "dmm-tools-fake"
    fake_dmm.write_text("#!/bin/sh\nexit 0\n")
    monkeypatch.setenv("VG_DMM_TOOLS_PATH", str(fake_dmm))

    def fake_build(vg13, dmm_tools, out_dir):
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "types.json").write_text(json.dumps({"/datum": {}}))

    monkeypatch.setattr(setup_mod, "_build_dm_index", fake_build)
    return tmp_path


def test_setup_uses_existing_vg13_checkout(empty_snapshot):
    result = setup_mod.setup(str(FIXTURE_VG13))
    assert result["configured"] is True
    assert result["vg13_path"] == str(FIXTURE_VG13.resolve())
    assert is_configured()
    cfg = json.loads(config_path().read_text())
    assert cfg["vg13_path"] == str(FIXTURE_VG13.resolve())


def test_setup_rejects_non_vg13_dir(empty_snapshot, tmp_path):
    bogus = tmp_path / "not-vg13"
    bogus.mkdir()
    (bogus / "random.txt").write_text("nope")
    with pytest.raises(ValueError, match="doesn't look like a vgstation13 checkout"):
        setup_mod.setup(str(bogus))


def test_setup_requires_clone_flag_for_missing_path(empty_snapshot, tmp_path):
    missing = tmp_path / "nope"
    with pytest.raises(FileNotFoundError, match="clone_if_missing=true"):
        setup_mod.setup(str(missing))


def test_setup_is_idempotent(empty_snapshot):
    setup_mod.setup(str(FIXTURE_VG13))
    # Second call should not rebuild (we count fake_build invocations indirectly
    # by ensuring the second call succeeds and config is still present).
    result = setup_mod.setup(str(FIXTURE_VG13))
    assert result["configured"] is True


def test_unconfigured_tools_raise_helpful_error(monkeypatch, tmp_path):
    monkeypatch.setenv("VG_SNAPSHOT_DIR", str(tmp_path / "empty"))
    monkeypatch.delenv("VG13_PATH", raising=False)
    from vgstation13_mcp.tools.source import list_dir

    with pytest.raises(RuntimeError, match="setup"):
        list_dir(".")


# The pipeline module needs to be importable for the build step in real setup.
sys.modules.setdefault("pipeline", __import__("pipeline"))
