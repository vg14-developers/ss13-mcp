import logging

from mcp.server.fastmcp import FastMCP

from vgstation13_mcp.tools.meta import snapshot_info as _snapshot_info
from vgstation13_mcp.tools.source import list_dir as _list_dir
from vgstation13_mcp.tools.source import read_file as _read_file
from vgstation13_mcp.tools.source import search_files as _search_files

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


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    # Default transport is stdio; the hosted deployment will swap this for SSE
    # via uvicorn (see deploy/ in a later task).
    mcp.run()


if __name__ == "__main__":
    main()
