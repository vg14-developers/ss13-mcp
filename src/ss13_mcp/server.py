import logging

from mcp.server.fastmcp import FastMCP

from ss13_mcp.resources import read_resource as _read_resource
from ss13_mcp.setup import setup as _setup
from ss13_mcp.tools.assets import convert_dmi as _convert_dmi
from ss13_mcp.tools.assets import list_dmi_states as _list_dmi_states
from ss13_mcp.tools.assets import read_asset as _read_asset
from ss13_mcp.tools.dm_index import find_proc as _find_proc
from ss13_mcp.tools.dm_index import find_var as _find_var
from ss13_mcp.tools.dm_index import get_type as _get_type
from ss13_mcp.tools.dm_index import list_subtypes as _list_subtypes
from ss13_mcp.tools.dm_index import path_lookup as _path_lookup
from ss13_mcp.tools.meta import snapshot_info as _snapshot_info
from ss13_mcp.tools.source import list_dir as _list_dir
from ss13_mcp.tools.source import read_file as _read_file
from ss13_mcp.tools.source import search_files as _search_files

log = logging.getLogger("ss13_mcp")
mcp = FastMCP("ss13")


@mcp.tool()
def setup(
    ss13_path: str,
    fork: str | None = None,
    repo_url: str | None = None,
    clone_if_missing: bool = False,
    sha: str | None = None,
    force: bool = False,
) -> dict:
    """One-time setup. Point this at an SS13 fork checkout (or have it clone one).

    Required before any other tool will work. Ask the user which fork they
    want to work with and where their clone lives, or where they'd like one
    cloned to, then call this.

    Known fork shortcuts: vg, tg, paradise, bay, goon, cm. For any other
    fork, pass a full git URL via `repo_url=`.

    Pass clone_if_missing=true if the directory doesn't exist yet and you
    want a fresh clone — must be combined with either `fork=<key>` or
    `repo_url=<git-url>`. Without `sha`, the remote's default-branch HEAD
    is cloned.

    Downloads the matching dmm-tools binary, builds the DM type index
    (~3-10 min the first time on a real fork), and writes a config so
    subsequent launches skip straight to serving.
    """
    return _setup(
        ss13_path,
        fork=fork,
        repo_url=repo_url,
        clone_if_missing=clone_if_missing,
        sha=sha,
        force=force,
    )


@mcp.tool()
def snapshot_info() -> dict:
    """Return metadata about the configured SS13 checkout, or a setup hint if unconfigured."""
    return _snapshot_info()


@mcp.tool()
def list_dir(path: str) -> list[dict]:
    """List directory entries in the configured SS13 checkout."""
    return _list_dir(path)


@mcp.tool()
def read_file(path: str, range: list[int] | None = None) -> str:
    """Read a source file from the SS13 checkout. Optional 1-indexed [start, end] line range."""
    return _read_file(path, range=range)


@mcp.tool()
def search_files(pattern: str, glob: str | None = None, limit: int = 200) -> list[dict]:
    """Regex search across the SS13 checkout. Optional glob narrows scope."""
    return _search_files(pattern, glob=glob, limit=limit)


@mcp.tool()
def get_type(path: str) -> dict:
    """Return parent, vars, procs, file:line for a BYOND type path."""
    return _get_type(path)


@mcp.tool()
def list_subtypes(path: str, transitive: bool = False) -> list[str]:
    """List direct subtypes of `path`; set transitive=true to walk the whole subtree."""
    return _list_subtypes(path, transitive=transitive)


@mcp.tool()
def find_proc(name: str, scope: str | None = None) -> list[dict]:
    """Find all procs with the given name. Optional `scope` narrows to a subtree."""
    return _find_proc(name, scope=scope)


@mcp.tool()
def find_var(name: str, scope: str | None = None) -> list[dict]:
    """Find all var declarations with the given name. Optional `scope` narrows to a subtree."""
    return _find_var(name, scope=scope)


@mcp.tool()
def path_lookup(query: str, limit: int = 50) -> list[dict]:
    """Fuzzy-match against the full type path index. Returns up to 50 ranked candidates."""
    return _path_lookup(query, limit=limit)


@mcp.tool()
def read_asset(path: str) -> dict:
    """Read a non-DMI asset (OGG/MID/PNG/etc). Returns size, mime, base64 bytes."""
    return _read_asset(path)


@mcp.tool()
def list_dmi_states(dmi_path: str) -> list[dict]:
    """List the states in a DMI sprite sheet without converting it."""
    return _list_dmi_states(dmi_path)


@mcp.tool()
def convert_dmi(dmi_path: str, state: str | None = None) -> dict:
    """Convert a DMI to a Robust SS14 RSI. Returns local path + URL."""
    return _convert_dmi(dmi_path, state=state)


@mcp.resource("ss13://source/{path}")
def _resource_source(path: str) -> str:
    return _read_resource(f"ss13://source/{path}")[0]


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    mcp.run()


if __name__ == "__main__":
    main()
