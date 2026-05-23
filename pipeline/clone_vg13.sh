#!/usr/bin/env bash
set -euo pipefail

SHA="$1"
DEST="$2"

if [[ -z "$SHA" || -z "$DEST" ]]; then
  echo "usage: $0 <vg13_sha> <dest_dir>" >&2
  exit 2
fi

mkdir -p "$DEST"
cd "$DEST"
git init -q
git remote add origin https://github.com/vgstation-coders/vgstation13.git
git fetch --depth 1 origin "$SHA"
git checkout FETCH_HEAD

ACTUAL=$(git rev-parse HEAD)
if [[ "$ACTUAL" != "$SHA" ]]; then
  echo "SHA mismatch: requested $SHA, got $ACTUAL" >&2
  exit 1
fi
