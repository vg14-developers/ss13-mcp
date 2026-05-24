from urllib.parse import urlparse

from ss13_mcp.tools.source import read_file


def read_resource(uri: str) -> tuple[str, str]:
    parsed = urlparse(uri)
    if parsed.scheme != "ss13":
        raise ValueError(f"unknown URI scheme: {parsed.scheme}")
    kind = parsed.netloc
    rest = parsed.path.lstrip("/")
    if kind == "source":
        return read_file(rest), "text/plain"
    raise ValueError(f"unknown resource kind: {kind}")
