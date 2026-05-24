"""First-run bootstrap: materialize the vg13 snapshot under the user's cache dir.

The first launch of `vgstation13-mcp` runs this. It is heavy (clones vgstation13,
downloads dmm-tools, fetches or crawls the ss13.moe wiki, builds the DM type
index) and may take 20-30 minutes. Subsequent launches detect the existing
snapshot and skip everything.

To re-run the bootstrap, delete the snapshot directory (`vgstation13-mcp
snapshot path` is printed at startup) and launch again.
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
import tarfile
import tempfile
import zipfile
from pathlib import Path
from urllib.request import Request, urlopen

from vgstation13_mcp.snapshot import snapshot_dir

log = logging.getLogger(__name__)

# Pin the vg13 commit + the dmm-tools release. Editing these changes what
# every fresh install materializes; existing installs are unaffected.
DEFAULT_VG13_SHA_FILE = Path(__file__).resolve().parents[2] / "snapshot.json"
DMM_TOOLS_RELEASE = "suite-1.10"
DMM_TOOLS_REPO = "SpaceManiac/SpacemanDMM"

# Wiki tarball published as a GitHub Release on this repo. If absent, fall back
# to crawling ss13.moe directly (slow, polite 1 req/sec).
WIKI_TARBALL_URL = (
    "https://github.com/vg14-developers/vgstation13-mcp/releases/download/wiki/wiki.tar.gz"
)


def _pinned_vg13_sha() -> str:
    sha = os.environ.get("VG13_SHA")
    if sha:
        return sha
    data = json.loads(DEFAULT_VG13_SHA_FILE.read_text())
    sha = data.get("vg13_sha", "")
    if not sha or sha == "0" * 40:
        raise RuntimeError(
            "snapshot.json has no pinned vg13_sha. Set VG13_SHA env var or edit "
            "snapshot.json to a real vgstation-coders/vgstation13 commit."
        )
    return sha


def _banner(msg: str) -> None:
    bar = "=" * max(60, len(msg) + 4)
    print(bar, file=sys.stderr)
    print(f"  {msg}", file=sys.stderr)
    print(bar, file=sys.stderr, flush=True)


def _step(msg: str) -> None:
    print(f"[setup] {msg}", file=sys.stderr, flush=True)


def _dmm_tools_url() -> tuple[str, str]:
    """Return (download_url, binary_filename) for the current platform."""
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


def _download(url: str, dest: Path) -> bool:
    """Download `url` to `dest`. Returns False on 404, raises on other errors."""
    req = Request(url, headers={"User-Agent": "vgstation13-mcp-setup"})
    try:
        with urlopen(req) as resp:
            dest.parent.mkdir(parents=True, exist_ok=True)
            with dest.open("wb") as f:
                shutil.copyfileobj(resp, f)
        return True
    except Exception as e:
        if hasattr(e, "code") and e.code == 404:  # type: ignore[attr-defined]
            return False
        raise


def _ensure_dmm_tools(snapshot: Path) -> Path:
    override = os.environ.get("VG_DMM_TOOLS_PATH")
    if override:
        return Path(override)
    bin_dir = snapshot / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    url, name = _dmm_tools_url()
    dest = bin_dir / name
    if dest.exists():
        return dest
    _step(f"downloading dmm-tools from {url}")
    if not _download(url, dest):
        raise RuntimeError(
            f"dmm-tools download returned 404: {url}. The pinned SpacemanDMM "
            f"release ({DMM_TOOLS_RELEASE}) may not publish a binary for this "
            "platform; build from source and set VG_DMM_TOOLS_PATH."
        )
    dest.chmod(dest.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return dest


def _clone_vg13(sha: str, dest: Path) -> None:
    if dest.exists() and (dest / ".git").exists():
        _step(f"vg13 clone already present at {dest}; skipping")
        return
    _step(f"cloning vgstation-coders/vgstation13 @ {sha[:8]} -> {dest}")
    dest.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "-q"], cwd=dest, check=True)
    subprocess.run(
        [
            "git",
            "remote",
            "add",
            "origin",
            "https://github.com/vgstation-coders/vgstation13.git",
        ],
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
    if (out_dir / "types.json").exists():
        _step(f"DM index already present at {out_dir}; skipping")
        return
    _step("building DM type index (this is the slowest local step, ~3-10 min)")
    env = os.environ.copy()
    # build_dm_index reads VG_DMM_TOOLS to locate the binary.
    env["VG_DMM_TOOLS"] = str(dmm_tools)
    subprocess.run(
        [sys.executable, "-m", "pipeline.build_dm_index", str(vg13), str(out_dir)],
        check=True,
        env=env,
    )


def _ensure_wiki(out_dir: Path) -> None:
    if (out_dir / "index.json").exists():
        _step(f"wiki snapshot already present at {out_dir}; skipping")
        return
    out_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(suffix=".tar.gz", delete=False) as tmp:
        tmp_path = Path(tmp.name)
    try:
        _step(f"trying wiki tarball from {WIKI_TARBALL_URL}")
        if _download(WIKI_TARBALL_URL, tmp_path):
            _step(f"extracting wiki tarball -> {out_dir}")
            if zipfile.is_zipfile(tmp_path):
                with zipfile.ZipFile(tmp_path) as zf:
                    zf.extractall(out_dir)
            else:
                with tarfile.open(tmp_path, "r:gz") as tf:
                    tf.extractall(out_dir)
            return
        _step("wiki tarball not published; falling back to live crawl (~20 min)")
    finally:
        tmp_path.unlink(missing_ok=True)
    _banner(
        "POLITE NOTICE: crawling ss13.moe at 1 request/second. "
        "This is a one-time per-install operation."
    )
    from pipeline.crawl_wiki import main as crawl_main

    crawl_main(out_dir)


def _pack(vg13: Path, index: Path, wiki: Path, out: Path, sha: str) -> None:
    if (out / "SHA").exists():
        return
    from pipeline.pack_artifacts import pack

    _step(f"packing snapshot -> {out}")
    pack(vg13, index, wiki, out, sha)


def ensure_snapshot() -> Path:
    """Materialize the snapshot if missing. Idempotent."""
    out = snapshot_dir()
    if (out / "SHA").exists():
        log.info("snapshot present at %s (vg13=%s)", out, (out / "SHA").read_text().strip()[:8])
        return out

    sha = _pinned_vg13_sha()
    _banner(
        "vgstation13-mcp first-run setup: ~20-30 minutes one-time. "
        "Subsequent launches start in seconds."
    )
    _step(f"snapshot will live at: {out}")

    work = out.parent / "_build"
    work.mkdir(parents=True, exist_ok=True)
    vg13_clone = work / "vg13"
    index_dir = work / "index"
    wiki_dir = work / "wiki"

    dmm = _ensure_dmm_tools(work)
    _clone_vg13(sha, vg13_clone)
    _build_dm_index(vg13_clone, dmm, index_dir)
    _ensure_wiki(wiki_dir)
    _pack(vg13_clone, index_dir, wiki_dir, out, sha)

    _banner(f"first-run setup complete. snapshot at {out}")
    return out
