"""Generates tests/fixtures/mini-ss13/icons/test.dmi.

Run once to (re)generate the DMI fixture. The output file size may vary slightly
across Pillow versions due to PNG encoder differences; what matters is that the
zTXt 'Description' chunk is present and CRC-valid, which downstream tests rely on.

Layout (14 cells total, 32x32 each, arranged 7 wide x 2 tall = 224x64 sheet):

  Row 0:  idle | active | walk f=0 d=0 | walk f=0 d=1 | walk f=0 d=2 | walk f=0 d=3 | walk f=1 d=0
  Row 1:  walk f=1 d=1 | walk f=1 d=2 | walk f=1 d=3 | walk f=2 d=0 | walk f=2 d=1 | walk f=2 d=2 | walk f=2 d=3

DMI sprite-sheet ordering is frame-major within each state: all directions for
frame 0, then all directions for frame 1, etc. Each walk cell is painted a
distinct RGB encoding (frame, dir) so tests can verify which DMI cell landed in
which RSI cell.
"""

import zlib
from pathlib import Path

from PIL import Image

OUT = Path(__file__).parent / "mini-ss13" / "icons" / "test.dmi"
OUT.parent.mkdir(parents=True, exist_ok=True)

CELLS_PER_ROW = 7
CELL = 32
SHEET_W = CELLS_PER_ROW * CELL
SHEET_H = 2 * CELL

sheet = Image.new("RGBA", (SHEET_W, SHEET_H), (0, 0, 0, 0))


def fill_cell(idx: int, color: tuple[int, int, int, int]) -> None:
    cx = (idx % CELLS_PER_ROW) * CELL
    cy = (idx // CELLS_PER_ROW) * CELL
    for x in range(CELL):
        for y in range(CELL):
            sheet.putpixel((cx + x, cy + y), color)


# Cells 0-1: single-state idle/active (preserves backward-compat).
fill_cell(0, (255, 0, 0, 255))  # idle: red
fill_cell(1, (0, 255, 0, 255))  # active: green


# Cells 2-13: walk state with dirs=4, frames=3, frame-major within state.
def walk_color(frame: int, direction: int) -> tuple[int, int, int, int]:
    """Encode (frame, dir) as RGB so tests can decode which cell is which."""
    return (30 + direction * 60, 30 + frame * 60, 200, 255)


idx = 2
for frame in range(3):
    for direction in range(4):
        fill_cell(idx, walk_color(frame, direction))
        idx += 1
assert idx == 14, f"expected 14 cells, painted {idx}"

# BYOND DMI metadata block (standard "Description" header).
desc = (
    "# BEGIN DMI\n"
    "version = 4.0\n"
    "\twidth = 32\n"
    "\theight = 32\n"
    'state = "idle"\n'
    "\tdirs = 1\n"
    "\tframes = 1\n"
    'state = "active"\n'
    "\tdirs = 1\n"
    "\tframes = 1\n"
    'state = "walk"\n'
    "\tdirs = 4\n"
    "\tframes = 3\n"
    "\tdelay = 1.0,1.5,2.0\n"
    "# END DMI\n"
)

# Save baseline PNG, then patch in zTXt chunk by hand.
tmp = OUT.with_suffix(".tmp.png")
sheet.save(tmp, format="PNG")
raw = tmp.read_bytes()
tmp.unlink()

keyword = b"Description\x00\x00"  # \x00 sep + \x00 compression method
compressed = zlib.compress(desc.encode("latin-1"))
chunk_data = keyword + compressed
length = len(chunk_data).to_bytes(4, "big")
chunk_type = b"zTXt"
crc = (zlib.crc32(chunk_type + chunk_data) & 0xFFFFFFFF).to_bytes(4, "big")
ztxt = length + chunk_type + chunk_data + crc

iend_idx = raw.rfind(b"IEND") - 4  # back up to its length field
patched = raw[:iend_idx] + ztxt + raw[iend_idx:]
OUT.write_bytes(patched)
print(f"wrote {OUT} ({len(patched)} bytes)")
