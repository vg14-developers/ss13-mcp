import logging

from mcp.server.fastmcp import FastMCP

from vgstation13_mcp.tools.meta import snapshot_info as _snapshot_info

log = logging.getLogger("vgstation13_mcp")
mcp = FastMCP("vgstation13")


@mcp.tool()
def snapshot_info() -> dict:
    """Return metadata about the currently-served vg13 snapshot."""
    return _snapshot_info()


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    # Default transport is stdio; the hosted deployment will swap this for SSE
    # via uvicorn (see deploy/ in a later task).
    mcp.run()


if __name__ == "__main__":
    main()
