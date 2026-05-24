# vgstation13-mcp

Local-launch MCP server that exposes vgstation13 source, assets, and wiki to AI
coding agents (Claude Code, etc.). Runs entirely on your machine — no hosted
service, no auth, no network calls after first-run setup.

## What it gives the agent

- **Source proxy:** read vg13 files at a pinned commit.
- **DM index:** structured queries against the BYOND type tree (subtypes, procs,
  vars, fuzzy path lookup) using SpacemanDMM's `dmm-tools`.
- **Assets:** on-demand DMI → Robust SS14 RSI conversion with disk-cached results.
- **Wiki:** searchable snapshot of ss13.moe.

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

## ⚠️ First-run setup takes 20–30 minutes

The first launch downloads the pinned vgstation13 source, fetches a prebuilt
`dmm-tools` binary, builds the DM type index, and either downloads a pre-crawled
wiki tarball (if the maintainer has published one) or crawls ss13.moe directly
at 1 req/sec.

You only pay this cost **once**. Subsequent launches start in seconds.

The snapshot is written to your platform's user cache directory:

| OS | Default path |
|----|----|
| Linux | `~/.cache/vgstation13-mcp/snapshot` |
| macOS | `~/Library/Caches/vgstation13-mcp/snapshot` |
| Windows | `%LOCALAPPDATA%\vgstation13-mcp\snapshot` |

To force a clean re-run, delete that directory.

## System requirements

- **git** on `$PATH` (for the vgstation13 clone).
- **ripgrep** (`rg`) on `$PATH` for the `search_files` tool. Without it, that one
  tool errors; everything else still works.
- A SpacemanDMM-supported platform for `dmm-tools` (auto-downloaded):
  x86_64 Linux, x86_64 Windows, x86_64 macOS, arm64 macOS via Rosetta.
  For other platforms, build `dmm-tools` yourself and point `VG_DMM_TOOLS_PATH`
  at the binary.

## Configuration

All optional — defaults work out of the box.

| Env var | Default | Purpose |
|----|----|----|
| `VG13_SHA` | from `snapshot.json` | Override the pinned vgstation13 commit. |
| `VG_SNAPSHOT_DIR` | platform cache dir | Where the materialized snapshot lives. |
| `VG_CACHE_DIR` | platform cache dir | Where DMI→RSI conversions are cached. |
| `VG_DMM_TOOLS_PATH` | downloaded | Override the `dmm-tools` binary location. |

## Maintainer notes

`snapshot.json` pins the vgstation13 commit that every fresh install
materializes. Update it (and run `publish-wiki` if you also want to refresh the
hosted wiki tarball) whenever you want new installs to pick up new vg13 content.

The `publish-wiki` workflow (manual, `workflow_dispatch`) crawls ss13.moe once
and uploads a `wiki.tar.gz` asset to the `wiki` GitHub Release. Once published,
new installs download the tarball instead of re-crawling. Without it, installs
fall back to a one-time live crawl (paced 1 req/sec).

## License

MIT.
