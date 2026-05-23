from urllib.parse import urlparse

from vgstation13_mcp.tools.source import read_file
from vgstation13_mcp.tools.wiki import wiki_read


def read_resource(uri: str) -> tuple[str, str]:
    parsed = urlparse(uri)
    if parsed.scheme != "vg13":
        raise ValueError(f"unknown URI scheme: {parsed.scheme}")
    kind = parsed.netloc
    rest = parsed.path.lstrip("/")
    if kind == "source":
        return read_file(rest), "text/plain"
    if kind == "wiki":
        return wiki_read(rest), "text/markdown"
    raise ValueError(f"unknown resource kind: {kind}")
