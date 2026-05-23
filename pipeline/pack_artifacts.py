"""Final step of the bump pipeline: assemble the snapshot dir layout."""

import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path


def pack(
    vg13_clone: Path,
    index_dir: Path,
    wiki_dir: Path,
    out_dir: Path,
    sha: str,
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for sub in ("code", "icons", "sound", "interface"):
        src = vg13_clone / sub
        if src.exists():
            shutil.copytree(src, out_dir / sub, dirs_exist_ok=True)
    shutil.copytree(index_dir, out_dir / "index", dirs_exist_ok=True)
    shutil.copytree(wiki_dir, out_dir / "wiki", dirs_exist_ok=True)
    (out_dir / "SHA").write_text(sha)
    (out_dir / "BUMPED_AT").write_text(datetime.now(timezone.utc).isoformat())
    assets = [
        str(p.relative_to(out_dir).as_posix())
        for p in out_dir.rglob("*")
        if p.is_file() and p.suffix in {".dmi", ".png", ".ogg", ".mid"}
    ]
    (out_dir / "assets.idx").write_text("\n".join(sorted(assets)))


def main() -> None:
    vg13 = Path(sys.argv[1])
    index = Path(sys.argv[2])
    wiki = Path(sys.argv[3])
    out = Path(sys.argv[4])
    sha = sys.argv[5]
    pack(vg13, index, wiki, out, sha)
    print(f"packed snapshot to {out}", flush=True)


if __name__ == "__main__":
    main()
