import json
from datetime import datetime, timezone

from vgstation13_mcp.snapshot import is_configured, load_config, snapshot_dir, vg13_dir


def snapshot_info() -> dict:
    if not is_configured():
        return {
            "configured": False,
            "message": (
                "vgstation13-mcp has not been set up. Call the `setup` tool with a "
                "vg13_path argument (path to an existing vgstation13 checkout, or a "
                "directory to clone into with clone_if_missing=true)."
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
        "vg13_sha": cfg.get("vg13_sha", "unknown"),
        "vg13_path": str(vg13_dir()),
        "bumped_at": cfg.get("bumped_at", datetime.now(timezone.utc).isoformat()),
        "dm_types_count": dm_types_count,
    }
