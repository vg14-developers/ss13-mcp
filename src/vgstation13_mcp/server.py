import logging

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.resources import FunctionResource
from pydantic import AnyUrl

from vgstation13_mcp.resources import read_resource as _read_resource
from vgstation13_mcp.tools.assets import convert_dmi as _convert_dmi
from vgstation13_mcp.tools.assets import list_dmi_states as _list_dmi_states
from vgstation13_mcp.tools.assets import read_asset as _read_asset
from vgstation13_mcp.tools.dm_index import find_proc as _find_proc
from vgstation13_mcp.tools.dm_index import find_var as _find_var
from vgstation13_mcp.tools.dm_index import get_type as _get_type
from vgstation13_mcp.tools.dm_index import list_subtypes as _list_subtypes
from vgstation13_mcp.tools.dm_index import path_lookup as _path_lookup
from vgstation13_mcp.tools.meta import snapshot_info as _snapshot_info
from vgstation13_mcp.tools.source import list_dir as _list_dir
from vgstation13_mcp.tools.source import read_file as _read_file
from vgstation13_mcp.tools.source import search_files as _search_files
from vgstation13_mcp.tools.wiki import _index as _wiki_index_loader
from vgstation13_mcp.tools.wiki import wiki_read as _wiki_read
from vgstation13_mcp.tools.wiki import wiki_search as _wiki_search

log = logging.getLogger("vgstation13_mcp")
mcp = FastMCP("vgstation13")


@mcp.tool()
def snapshot_info() -> dict:
    """Return metadata about the currently-served vg13 snapshot."""
    return _snapshot_info()


@mcp.tool()
def list_dir(path: str) -> list[dict]:
    """List directory entries in the vg13 snapshot."""
    return _list_dir(path)


@mcp.tool()
def read_file(path: str, range: list[int] | None = None) -> str:
    """Read a vg13 source file. Optional 1-indexed [start, end] line range."""
    return _read_file(path, range=range)


@mcp.tool()
def search_files(pattern: str, glob: str | None = None, limit: int = 200) -> list[dict]:
    """Ripgrep across vg13 source. Optional glob narrows scope."""
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


@mcp.tool()
def wiki_search(query: str, limit: int = 25) -> list[dict]:
    """Search the snapshotted ss13.moe wiki. Returns page titles + excerpts.

    The wiki is player-written prose and is the right source for:
    - User-facing intent of a system ("what is atmospherics FOR")
    - Multi-step gameplay workflows ("how do I purge an overdose")
    - Cross-system interactions ("what happens if I throw a body into
      the singularity") that aren't stated in any single source file
    - Historical context for design choices

    It is the WRONG source for:
    - Specific numbers (reagent thresholds, gas constants, prices, HP
      values, timings) -- wiki pages drift from code by months or years
    - Current code behavior -- pages can be stale ("Needs revision"
      banners are common); always verify against source
    - Type paths or proc signatures -- use the DM index tools instead

    Rule of thumb: wiki for "why" and "how it's played"; code (via
    get_type, find_proc, find_var, read_file) for "what it actually does".
    """
    return _wiki_search(query, limit=limit)


@mcp.tool()
def wiki_read(page: str) -> str:
    """Return markdown for a single snapshotted wiki page.

    See wiki_search for the trust model. In short: wiki is for intent and
    emergent gameplay; for any specific number or current behavior, verify
    against source via the DM index or read_file.
    """
    return _wiki_read(page)


@mcp.resource("vg13://source/{path}")
def _resource_source(path: str) -> str:
    return _read_resource(f"vg13://source/{path}")[0]


def register_wiki_resources() -> int:
    """Enumerate snapshotted wiki pages and register each as an MCP resource.

    Called by main() after the snapshot is materialized. Returns the count for tests.
    """
    count = 0
    for entry in _wiki_index_loader():
        page = entry["page"]
        mcp.add_resource(
            FunctionResource(
                uri=AnyUrl(f"vg13://wiki/{page}"),
                name=entry["title"],
                mime_type="text/markdown",
                fn=lambda p=page: _wiki_read(p),
            )
        )
        count += 1
    return count


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    from vgstation13_mcp.setup import ensure_snapshot

    ensure_snapshot()
    register_wiki_resources()
    mcp.run()


if __name__ == "__main__":
    main()
