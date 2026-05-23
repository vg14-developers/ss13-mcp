# vgstation13-mcp

Hosted MCP server exposing vgstation13 source, assets, and wiki to the
vgstation14 agent fleet (Parity, Spec, Work-item).

## Status

In active build-out. See `docs/` for design and plan references in
`vgstation14`.

## What it does

- **Source proxy:** read vg13 files at a pinned commit SHA.
- **DM index:** structured queries against the BYOND type tree.
- **Assets:** on-demand DMI→RSI conversion with disk-cached results.
- **Wiki:** searchable snapshot of ss13.moe.
- **Auth:** GitHub OAuth for contributors; bearer-token bypass for CI.

## Bumping the vg13 snapshot

Open a PR that changes `snapshot.json:vg13_sha` to a newer
vgstation-coders/vgstation13 commit. CI handles the rest (build, push,
deploy).

## License

MIT.
