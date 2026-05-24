"""Builds the baked DM index from dmm-tools dump-types output."""

import json
import os
import subprocess
import sys
from collections import defaultdict
from pathlib import Path


def run_dmm_tools(vg13_clone: Path, out_json: Path) -> None:
    """Invoke dmm-tools dump-types and write its NDJSON output."""
    dmm = os.environ.get("VG_DMM_TOOLS", "dmm-tools")
    subprocess.run(
        [dmm, "dump-types", "--format", "json", str(vg13_clone)],
        check=True,
        stdout=out_json.open("w"),
    )


def massage_dmm_output(records: list[dict], out_dir: Path) -> None:
    """Transform dmm-tools records into the four index artifacts."""
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
    vg13 = Path(sys.argv[1])
    out = Path(sys.argv[2])
    raw = out / "dmm-raw.json"
    raw.parent.mkdir(parents=True, exist_ok=True)
    run_dmm_tools(vg13, raw)
    records = [json.loads(line) for line in raw.read_text().splitlines() if line]
    massage_dmm_output(records, out)
    raw.unlink()


if __name__ == "__main__":
    main()
