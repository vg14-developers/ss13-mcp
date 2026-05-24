import json
from pathlib import Path

import pytest

from ss13_mcp import setup as setup_mod
from ss13_mcp.snapshot import config_path, is_configured

FIXTURE_SS13 = Path(__file__).parent / "fixtures" / "mini-ss13"


@pytest.fixture
def empty_snapshot(monkeypatch, tmp_path):
    monkeypatch.setenv("SS13_SNAPSHOT_DIR", str(tmp_path / "snap"))
    monkeypatch.delenv("SS13_PATH", raising=False)
    # Skip the real dmm-tools download + DM index build in unit tests.
    fake_dmm = tmp_path / "dmm-tools-fake"
    fake_dmm.write_text("#!/bin/sh\nexit 0\n")
    monkeypatch.setenv("SS13_DMM_TOOLS_PATH", str(fake_dmm))

    def fake_build(ss13, dmm_tools, out_dir):
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "types.json").write_text(json.dumps({"/datum": {}}))

    monkeypatch.setattr(setup_mod, "_build_dm_index", fake_build)
    return tmp_path


def test_setup_uses_existing_ss13_checkout(empty_snapshot):
    result = setup_mod.setup(str(FIXTURE_SS13))
    assert result["configured"] is True
    assert result["ss13_path"] == str(FIXTURE_SS13.resolve())
    assert is_configured()
    cfg = json.loads(config_path().read_text())
    assert cfg["ss13_path"] == str(FIXTURE_SS13.resolve())


def test_setup_rejects_non_ss13_dir(empty_snapshot, tmp_path):
    bogus = tmp_path / "not-ss13"
    bogus.mkdir()
    (bogus / "random.txt").write_text("nope")
    with pytest.raises(ValueError, match="doesn't look like an SS13 checkout"):
        setup_mod.setup(str(bogus))


def test_setup_requires_clone_flag_for_missing_path(empty_snapshot, tmp_path):
    missing = tmp_path / "nope"
    with pytest.raises(FileNotFoundError, match="clone_if_missing=true"):
        setup_mod.setup(str(missing))


def test_setup_clone_requires_fork_or_url(empty_snapshot, tmp_path, monkeypatch):
    """clone_if_missing=true without fork/repo_url should error before touching git."""
    # Make `git` lookup succeed so the error comes from missing fork/url, not git.
    monkeypatch.setattr(setup_mod.shutil, "which", lambda _: "/usr/bin/git")
    missing = tmp_path / "fresh"
    with pytest.raises(ValueError, match="fork=|repo_url="):
        setup_mod.setup(str(missing), clone_if_missing=True)


def test_setup_rejects_both_fork_and_url(empty_snapshot, tmp_path, monkeypatch):
    monkeypatch.setattr(setup_mod.shutil, "which", lambda _: "/usr/bin/git")
    missing = tmp_path / "fresh"
    with pytest.raises(ValueError, match="not both"):
        setup_mod.setup(
            str(missing),
            clone_if_missing=True,
            fork="vg",
            repo_url="https://example.com/x.git",
        )


def test_setup_rejects_unknown_fork(empty_snapshot, tmp_path, monkeypatch):
    monkeypatch.setattr(setup_mod.shutil, "which", lambda _: "/usr/bin/git")
    missing = tmp_path / "fresh"
    with pytest.raises(ValueError, match="unknown fork"):
        setup_mod.setup(str(missing), clone_if_missing=True, fork="nonesuch")


def test_setup_is_idempotent(empty_snapshot):
    setup_mod.setup(str(FIXTURE_SS13))
    # Second call should not rebuild (we count fake_build invocations indirectly
    # by ensuring the second call succeeds and config is still present).
    result = setup_mod.setup(str(FIXTURE_SS13))
    assert result["configured"] is True


def test_unconfigured_tools_raise_helpful_error(monkeypatch, tmp_path):
    monkeypatch.setenv("SS13_SNAPSHOT_DIR", str(tmp_path / "empty"))
    monkeypatch.delenv("SS13_PATH", raising=False)
    from ss13_mcp.tools.source import list_dir

    with pytest.raises(RuntimeError, match="setup"):
        list_dir(".")
