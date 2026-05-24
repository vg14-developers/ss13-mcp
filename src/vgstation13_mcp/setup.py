"""Setup tool exposed via MCP. Replaces the old auto-bootstrap.

Flow: the agent asks the user where their vgstation13 checkout is (or where
they'd like one cloned), then invokes `setup(vg13_path=...)`. This validates
or clones the repo, downloads the matching dmm-tools binary, builds the DM
type index, and writes a small config so future tool calls know where to
look.

Idempotent: re-running with the same vg13_path is a no-op unless force=true.
"""

from __future__ import annotations

import json
import logging
import os
import platform
import shutil
import stat
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

from vgstation13_mcp.snapshot import config_path, snapshot_dir, write_config

log = logging.getLogger(__name__)

# Default vgstation13 commit used when cloning fresh. Bump alongside any
# breaking changes you want new installs to pick up. Users can override via
# the `sha` parameter to setup() or the VG13_SHA env var.
DEFAULT_VG13_SHA = "8f05182163946c4133aa829e5e4ea96c1abc3d37"

DMM_TOOLS_RELEASE = "suite-1.10"
DMM_TOOLS_REPO = "SpaceManiac/SpacemanDMM"
VG13_GIT_URL = "https://github.com/vgstation-coders/vgstation13.git"


def _step(msg: str) -> None:
    print(f"[setup] {msg}", file=sys.stderr, flush=True)


def _dmm_tools_url() -> tuple[str, str]:
    sysname = platform.system().lower()
    machine = platform.machine().lower()
    if sysname == "windows":
        return (
            f"https://github.com/{DMM_TOOLS_REPO}/releases/download/"
            f"{DMM_TOOLS_RELEASE}/dmm-tools.exe",
            "dmm-tools.exe",
        )
    if sysname == "linux" and machine in {"x86_64", "amd64"}:
        return (
            f"https://github.com/{DMM_TOOLS_REPO}/releases/download/"
            f"{DMM_TOOLS_RELEASE}/dmm-tools",
            "dmm-tools",
        )
    if sysname == "darwin":
        return (
            f"https://github.com/{DMM_TOOLS_REPO}/releases/download/"
            f"{DMM_TOOLS_RELEASE}/dmm-tools",
            "dmm-tools",
        )
    raise RuntimeError(
        f"no prebuilt dmm-tools for {sysname}/{machine}. Build SpacemanDMM "
        f"from source (https://github.com/{DMM_TOOLS_REPO}) and set "
        "VG_DMM_TOOLS_PATH to the resulting binary."
    )


def _download(url: str, dest: Path) -> None:
    req = Request(url, headers={"User-Agent": "vgstation13-mcp-setup"})
    with urlopen(req) as resp:
        dest.parent.mkdir(parents=True, exist_ok=True)
        with dest.open("wb") as f:
            shutil.copyfileobj(resp, f)


def _ensure_dmm_tools() -> Path:
    override = os.environ.get("VG_DMM_TOOLS_PATH")
    if override:
        return Path(override)
    bin_dir = snapshot_dir() / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    url, name = _dmm_tools_url()
    dest = bin_dir / name
    if dest.exists():
        return dest
    _step(f"downloading dmm-tools from {url}")
    _download(url, dest)
    dest.chmod(dest.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return dest


def _looks_like_vg13(path: Path) -> bool:
    return (path / "code").is_dir() and (path / "icons").is_dir()


def _git_head_sha(path: Path) -> str | None:
    if not (path / ".git").exists():
        return None
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=path,
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def _clone_vg13(sha: str, dest: Path) -> None:
    _step(f"cloning vgstation-coders/vgstation13 @ {sha[:8]} -> {dest}")
    dest.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "-q"], cwd=dest, check=True)
    subprocess.run(
        ["git", "remote", "add", "origin", VG13_GIT_URL],
        cwd=dest,
        check=True,
    )
    subprocess.run(["git", "fetch", "--depth", "1", "origin", sha], cwd=dest, check=True)
    subprocess.run(["git", "checkout", "FETCH_HEAD"], cwd=dest, check=True)
    actual = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=dest, check=True, capture_output=True, text=True
    ).stdout.strip()
    if actual != sha:
        raise RuntimeError(f"SHA mismatch: requested {sha}, got {actual}")


def _build_dm_index(vg13: Path, dmm_tools: Path, out_dir: Path) -> None:
    _step("building DM type index (slowest local step, ~3-10 min)")
    env = os.environ.copy()
    env["VG_DMM_TOOLS"] = str(dmm_tools)
    subprocess.run(
        [sys.executable, "-m", "pipeline.build_dm_index", str(vg13), str(out_dir)],
        check=True,
        env=env,
    )


def setup(
    vg13_path: str,
    clone_if_missing: bool = False,
    sha: str | None = None,
    force: bool = False,
) -> dict:
    """Configure the MCP server against a vgstation13 checkout.

    Args:
        vg13_path: Absolute path to an existing vgstation13 clone, or the
            directory you'd like one cloned into (combine with
            clone_if_missing=true).
        clone_if_missing: If true and `vg13_path` does not exist (or is empty),
            clone vgstation-coders/vgstation13 into it. If false and the path
            is missing, this raises.
        sha: Commit SHA to check out when cloning. Defaults to the pinned
            commit baked into this release.
        force: Rebuild the DM index even if one already exists for this path.

    Returns a summary dict the caller can show to the user.
    """
    vg13 = Path(vg13_path).expanduser().resolve()

    if vg13.exists() and any(vg13.iterdir()):
        if not _looks_like_vg13(vg13):
            raise ValueError(
                f"{vg13} exists but doesn't look like a vgstation13 checkout "
                "(expected code/ and icons/ subdirs). Point setup at a real "
                "vgstation13 clone or an empty/nonexistent directory with "
                "clone_if_missing=true."
            )
        actual_sha = _git_head_sha(vg13) or "unknown"
        _step(f"using existing vg13 checkout at {vg13} (HEAD={actual_sha[:8]})")
    else:
        if not clone_if_missing:
            raise FileNotFoundError(
                f"{vg13} does not exist. Re-run with clone_if_missing=true to "
                "clone vgstation-coders/vgstation13 into that directory."
            )
        if not shutil.which("git"):
            raise RuntimeError("git is required to clone vgstation13 but was not found on PATH")
        clone_sha = sha or os.environ.get("VG13_SHA") or DEFAULT_VG13_SHA
        _clone_vg13(clone_sha, vg13)
        actual_sha = clone_sha

    dmm = _ensure_dmm_tools()

    index_dir = snapshot_dir() / "index"
    if force or not (index_dir.exists() and (index_dir / "types.json").exists()):
        if index_dir.exists():
            shutil.rmtree(index_dir)
        _build_dm_index(vg13, dmm, index_dir)
    else:
        _step(f"DM index already present at {index_dir}; skipping (pass force=true to rebuild)")

    cfg = {
        "vg13_path": str(vg13),
        "vg13_sha": actual_sha,
        "bumped_at": datetime.now(timezone.utc).isoformat(),
        "dmm_tools_path": str(dmm),
    }
    write_config(cfg)
    _step(f"wrote config to {config_path()}")

    types_count = 0
    types_file = index_dir / "types.json"
    if types_file.exists():
        types_count = len(json.loads(types_file.read_text()))

    return {
        "configured": True,
        "vg13_path": str(vg13),
        "vg13_sha": actual_sha,
        "dmm_tools_path": str(dmm),
        "snapshot_dir": str(snapshot_dir()),
        "dm_types_count": types_count,
    }
