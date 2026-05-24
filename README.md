# ss13-mcp

Local-launch MCP server that exposes any SS13 fork's source and assets to AI
coding agents (Claude Code, etc.). Runs entirely on your machine — no hosted
service, no auth, no network calls after first-run setup.

Works with any fork that follows the standard SS13 layout (top-level `code/`
and `icons/` dirs). Ships with shortcuts for **vg**, **tg**, **paradise**,
**bay**, **goon**, and **cm**; for anything else, just pass a git URL.

## What it gives the agent

- **Source proxy:** read SS13 source files at the commit you've checked out.
- **DM index:** structured queries against the BYOND type tree (subtypes, procs,
  vars, fuzzy path lookup) using SpacemanDMM's `dmm-tools`.
- **Assets:** on-demand DMI → Robust SS14 RSI conversion with disk-cached results.

## Install

```bash
uvx --from git+https://github.com/vg14-developers/ss13-mcp ss13-mcp
```

Or pin via your Claude Code configuration (`.mcp.json`):

```json
{
  "mcpServers": {
    "ss13": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/vg14-developers/ss13-mcp",
        "ss13-mcp"
      ]
    }
  }
}
```

## First-run setup

The server ships with **no** automatic setup. On first launch its tools will
respond with a setup-required hint pointing the agent at the `setup` tool.

Tell the agent something like:

- **"I already have my SS13 fork cloned at `<path>`"** — the agent will call
  `setup(ss13_path="<path>")` and reuse your existing checkout.
- **"Clone tg to `<path>`"** — the agent will call
  `setup(ss13_path="<path>", fork="tg", clone_if_missing=True)` which clones
  the remote's default-branch HEAD into that directory.
- **"Clone https://github.com/.../my-fork.git to `<path>`"** — the agent will
  call `setup(ss13_path="<path>", repo_url="...", clone_if_missing=True)`.

Pass `sha="<commit>"` if you want a specific commit instead of the default
branch HEAD.

Setup then downloads the matching `dmm-tools` binary and builds the DM type
index (~3–10 min on a real fork). The result is persisted under your platform's
user cache dir so subsequent launches start in seconds:

| OS | Default snapshot path |
|----|----|
| Linux | `~/.cache/ss13-mcp/snapshot` |
| macOS | `~/Library/Caches/ss13-mcp/snapshot` |
| Windows | `%LOCALAPPDATA%\ss13-mcp\snapshot` |

To re-run setup against a different checkout, just call `setup` again with the
new path. Pass `force=True` to rebuild the DM index in place.

### Known fork shortcuts

| Key | Repository |
|----|----|
| `vg` | https://github.com/vgstation-coders/vgstation13 |
| `tg` | https://github.com/tgstation/tgstation |
| `paradise` | https://github.com/ParadiseSS13/Paradise |
| `bay` | https://github.com/Baystation12/Baystation12 |
| `goon` | https://github.com/goonstation/goonstation |
| `cm` | https://github.com/cmss13-devs/cmss13 |

Any SS13 fork (or other BYOND project with `code/` and `icons/` at the root)
works via the `repo_url=` parameter.

## System requirements

- **git** on `$PATH` (only needed if you ask setup to clone for you).
- **ripgrep** (`rg`) on `$PATH` for the `search_files` tool. Without it, that one
  tool errors; everything else still works.
- A SpacemanDMM-supported platform for `dmm-tools` (auto-downloaded):
  x86_64 Linux, x86_64 Windows, x86_64 macOS, arm64 macOS via Rosetta.
  For other platforms, build `dmm-tools` yourself and set `SS13_DMM_TOOLS_PATH`.

## Configuration

All optional — defaults work out of the box.

| Env var | Default | Purpose |
|----|----|----|
| `SS13_PATH` | from config | Override the SS13 checkout used by tools. Takes precedence over the configured path. |
| `SS13_SHA` | none | Default commit to check out when `clone_if_missing=true` and no `sha` is passed. Without it, the remote's default-branch HEAD is used. |
| `SS13_SNAPSHOT_DIR` | platform cache dir | Where the DM index + config live. |
| `SS13_CACHE_DIR` | platform cache dir | Where DMI→RSI conversions are cached. |
| `SS13_DMM_TOOLS_PATH` | downloaded | Override the `dmm-tools` binary location. |

## License

MIT.
