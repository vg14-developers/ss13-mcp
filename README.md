# vgstation13-mcp

Local-launch MCP server that exposes vgstation13 source and assets to AI
coding agents (Claude Code, etc.). Runs entirely on your machine — no hosted
service, no auth, no network calls after first-run setup.

## What it gives the agent

- **Source proxy:** read vg13 files at the commit you've checked out.
- **DM index:** structured queries against the BYOND type tree (subtypes, procs,
  vars, fuzzy path lookup) using SpacemanDMM's `dmm-tools`.
- **Assets:** on-demand DMI → Robust SS14 RSI conversion with disk-cached results.

## Install

```bash
uvx --from git+https://github.com/vg14-developers/vgstation13-mcp vgstation13-mcp
```

Or pin via your Claude Code configuration (`.mcp.json`):

```json
{
  "mcpServers": {
    "vgstation13": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/vg14-developers/vgstation13-mcp",
        "vgstation13-mcp"
      ]
    }
  }
}
```

## First-run setup

The server ships with **no** automatic setup. On first launch its tools will
respond with a setup-required hint pointing the agent at the `setup` tool.

Tell the agent either:

- **"I already have vgstation13 cloned at `<path>`"** — the agent will call
  `setup(vg13_path="<path>")` and reuse your existing checkout.
- **"Clone vgstation13 to `<path>`"** — the agent will call
  `setup(vg13_path="<path>", clone_if_missing=True)` which clones the pinned
  commit there.

Setup then downloads the matching `dmm-tools` binary and builds the DM type
index (~3–10 min). The result is persisted under your platform's user cache
dir so subsequent launches start in seconds:

| OS | Default snapshot path |
|----|----|
| Linux | `~/.cache/vgstation13-mcp/snapshot` |
| macOS | `~/Library/Caches/vgstation13-mcp/snapshot` |
| Windows | `%LOCALAPPDATA%\vgstation13-mcp\snapshot` |

To re-run setup against a different checkout, just call `setup` again with the
new path. Pass `force=True` to rebuild the DM index in place.

## System requirements

- **git** on `$PATH` (only needed if you ask setup to clone for you).
- **ripgrep** (`rg`) on `$PATH` for the `search_files` tool. Without it, that one
  tool errors; everything else still works.
- A SpacemanDMM-supported platform for `dmm-tools` (auto-downloaded):
  x86_64 Linux, x86_64 Windows, x86_64 macOS, arm64 macOS via Rosetta.
  For other platforms, build `dmm-tools` yourself and set `VG_DMM_TOOLS_PATH`.

## Configuration

All optional — defaults work out of the box.

| Env var | Default | Purpose |
|----|----|----|
| `VG13_PATH` | from config | Override the vg13 checkout used by tools. Takes precedence over the configured path. |
| `VG13_SHA` | pinned in `setup.py` | Default commit to check out when `clone_if_missing=true` and no `sha` is passed. |
| `VG_SNAPSHOT_DIR` | platform cache dir | Where the DM index + config live. |
| `VG_CACHE_DIR` | platform cache dir | Where DMI→RSI conversions are cached. |
| `VG_DMM_TOOLS_PATH` | downloaded | Override the `dmm-tools` binary location. |

## Maintainer notes

`DEFAULT_VG13_SHA` in `src/vgstation13_mcp/setup.py` pins the commit that fresh
clones land on when the user passes `clone_if_missing=true` without specifying
a SHA. Bump it when you want new clones to track a newer vg13 tip.

## License

MIT.
