"""Builds the baked DM index from `dm-dump` NDJSON output.

The pipeline shells out to the vendored `dm-dump` Rust binary (see dm-dump/ in
the repo root) which walks the BYOND type tree using the dreammaker parser
crate. See issue #16 for why we ship our own binary instead of relying on
upstream SpacemanDMM's dmm-tools.
"""

import json
import os
import subprocess
import sys
from collections import defaultdict
from pathlib import Path


def run_dm_dump(ss13_clone: Path, out_json: Path) -> None:
    """Invoke dm-dump and write its NDJSON output to `out_json`.

    Captures stderr so a missing binary or runtime failure surfaces as a
    RuntimeError with the real error text rather than leaving a 0-byte
    dmm-raw.json behind (see issue #16).
    """
    dm_dump = os.environ.get("SS13_DM_DUMP", "dm-dump")
    out_json.parent.mkdir(parents=True, exist_ok=True)
    try:
        with out_json.open("w") as f:
            subprocess.run(
                [dm_dump, str(ss13_clone)],
                check=True,
                stdout=f,
                stderr=subprocess.PIPE,
                text=True,
            )
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        out_json.unlink(missing_ok=True)
        if isinstance(e, FileNotFoundError):
            raise RuntimeError(
                f"dm-dump binary not found at {dm_dump!r}. The pipeline reads "
                "the `SS13_DM_DUMP` env var (normally set by setup); to run "
                "the pipeline directly, build dm-dump from this repo's "
                "dm-dump/ crate and point this var at the binary."
            ) from e
        stderr = (e.stderr or "").strip() or "(no stderr)"
        raise RuntimeError(f"dm-dump failed (exit {e.returncode}): {stderr}") from e


def massage_dmm_output(records: list[dict], out_dir: Path) -> None:
    """Transform dm-dump records into the four index artifacts."""
    out_dir.mkdir(parents=True, exist_ok=True)
    types: dict[str, dict] = {}
    procs: dict[str, list[dict]] = defaultdict(list)
    vars_: dict[str, list[dict]] = defaultdict(list)
    children: dict[str, list[str]] = defaultdict(list)

    for rec in records:
        path = rec["path"]
        types[path] = {
            "parent": rec.get("parent"),
            "vars": rec.get("vars", []),
            "procs": [p["name"] for p in rec.get("procs", [])],
            "file": rec.get("file"),
            "line": rec.get("line"),
            "children": [],
        }
        if rec.get("parent"):
            children[rec["parent"]].append(path)
        for p in rec.get("procs", []):
            procs[p["name"]].append(
                {
                    "type": path,
                    "file": rec.get("file"),
                    "line": rec.get("line"),
                }
            )
        for v in rec.get("vars", []):
            vars_[v["name"]].append(
                {
                    "type": path,
                    "file": rec.get("file"),
                    "line": rec.get("line"),
                    "value": v.get("value"),
                }
            )

    # Fill in children lists.
    for parent, kids in children.items():
        if parent in types:
            types[parent]["children"] = sorted(kids)

    (out_dir / "types.json").write_text(json.dumps(types, indent=2))
    (out_dir / "procs.json").write_text(json.dumps(dict(procs), indent=2))
    (out_dir / "vars.json").write_text(json.dumps(dict(vars_), indent=2))
    (out_dir / "paths.idx").write_text("\n".join(sorted(types.keys())))


def main() -> None:
    ss13 = Path(sys.argv[1])
    out = Path(sys.argv[2])
    raw = out / "dmm-raw.json"
    raw.parent.mkdir(parents=True, exist_ok=True)
    run_dm_dump(ss13, raw)
    records = [json.loads(line) for line in raw.read_text().splitlines() if line]
    massage_dmm_output(records, out)
    raw.unlink()


if __name__ == "__main__":
    main()
