import logging

from mcp.server.fastmcp import FastMCP
from mcp.types import Resource
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
    """Full-text search across the snapshotted ss13.moe wiki. Returns page titles + excerpts."""
    return _wiki_search(query, limit=limit)


@mcp.tool()
def wiki_read(page: str) -> str:
    """Return markdown for a single snapshotted wiki page."""
    return _wiki_read(page)


# Resource handlers live on the low-level Server. FastMCP 1.2.0 doesn't expose
# `@mcp.list_resources()` / `@mcp.read_resource()` decorators directly, so we
# register on `mcp._mcp_server` and overwrite FastMCP's default handlers.
@mcp._mcp_server.list_resources()
async def list_resources() -> list[Resource]:
    """Advertise snapshotted wiki pages as vg13:// resources."""
    out: list[Resource] = []
    for entry in _wiki_index_loader():
        out.append(
            Resource(
                uri=AnyUrl(f"vg13://wiki/{entry['page']}"),
                name=entry["title"],
                mimeType="text/markdown",
            )
        )
    return out


@mcp._mcp_server.read_resource()
async def read_resource(uri: AnyUrl) -> str:
    """Resolve a vg13://source/... or vg13://wiki/... URI to its content."""
    content, _mime = _read_resource(str(uri))
    return content


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    # Default transport is stdio; the hosted deployment will swap this for SSE
    # via uvicorn (see deploy/ in a later task).
    mcp.run()


if __name__ == "__main__":
    main()
