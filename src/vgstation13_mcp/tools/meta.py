import json
from datetime import datetime, timezone

from vgstation13_mcp.snapshot import read_snapshot_sha, snapshot_dir


def snapshot_info() -> dict:
    sha = read_snapshot_sha()
    snap = snapshot_dir()
    bumped_at_path = snap / "BUMPED_AT"
    if bumped_at_path.exists():
        bumped_at = bumped_at_path.read_text().strip()
    else:
        # Fall back to the SHA file's mtime, then now.
        mtime_src = snap / "SHA"
        ts = mtime_src.stat().st_mtime if mtime_src.exists() else datetime.now(timezone.utc).timestamp()
        bumped_at = datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()

    wiki_dir = snap / "wiki"
    wiki_pages = len(list(wiki_dir.glob("*.md"))) if wiki_dir.exists() else 0
    # Fallback: pre-bump deployments only have wiki_html/*.html, not wiki/*.md.
    if wiki_pages == 0:
        html_dir = snap / "wiki_html"
        wiki_pages = len(list(html_dir.glob("*.html"))) if html_dir.exists() else 0

    types_idx = snap / "index" / "types.json"
    dm_types_count = 0
    if types_idx.exists():
        dm_types_count = len(json.loads(types_idx.read_text()))

    return {
        "vg13_sha": sha,
        "vg13_commit_subject": "",  # populated by the bump pipeline
        "bumped_at": bumped_at,
        "wiki_pages": wiki_pages,
        "dm_types_count": dm_types_count,
    }
