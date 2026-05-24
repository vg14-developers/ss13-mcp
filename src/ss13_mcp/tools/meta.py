import json
from datetime import datetime, timezone

from ss13_mcp.snapshot import is_configured, load_config, snapshot_dir, ss13_dir


def snapshot_info() -> dict:
    if not is_configured():
        return {
            "configured": False,
            "message": (
                "ss13-mcp has not been set up. Call the `setup` tool with an "
                "ss13_path argument (path to an existing SS13 fork checkout, or "
                "a directory to clone into with clone_if_missing=true and either "
                "fork=<vg|tg|paradise|bay|goon|cm> or repo_url=<git-url>)."
            ),
        }

    cfg = load_config()
    snap = snapshot_dir()

    types_idx = snap / "index" / "types.json"
    dm_types_count = 0
    if types_idx.exists():
        dm_types_count = len(json.loads(types_idx.read_text()))

    return {
        "configured": True,
        "fork": cfg.get("fork", "custom"),
        "ss13_sha": cfg.get("ss13_sha", "unknown"),
        "ss13_path": str(ss13_dir()),
        "bumped_at": cfg.get("bumped_at", datetime.now(timezone.utc).isoformat()),
        "dm_types_count": dm_types_count,
    }
