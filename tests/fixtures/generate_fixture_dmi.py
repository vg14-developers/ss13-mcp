"""Generates tests/fixtures/mini-vg13/icons/test.dmi.

Run once to (re)generate the DMI fixture. The output file size may vary slightly
across Pillow versions due to PNG encoder differences; what matters is that the
zTXt 'Description' chunk is present and CRC-valid, which downstream tests rely on.
"""
import zlib
from pathlib import Path

from PIL import Image

OUT = Path(__file__).parent / "mini-vg13" / "icons" / "test.dmi"
OUT.parent.mkdir(parents=True, exist_ok=True)

# Build a 64x32 sheet: 2 states (idle, active), each 32x32, 1 dir, 1 frame.
sheet = Image.new("RGBA", (64, 32), (0, 0, 0, 0))
# Paint each 32x32 cell a distinguishing color so visual diffs are obvious:
# red = "idle" state, green = "active" state (matches the DMI Description below).
for x in range(32):
    for y in range(32):
        sheet.putpixel((x, y), (255, 0, 0, 255))
        sheet.putpixel((x + 32, y), (0, 255, 0, 255))

# BYOND DMI metadata block (the standard "Description" header).
desc = (
    "# BEGIN DMI\n"
    "version = 4.0\n"
    "\twidth = 32\n"
    "\theight = 32\n"
    "state = \"idle\"\n"
    "\tdirs = 1\n"
    "\tframes = 1\n"
    "state = \"active\"\n"
    "\tdirs = 1\n"
    "\tframes = 1\n"
    "# END DMI\n"
)

# Save baseline PNG, then patch in zTXt chunk by hand.
tmp = OUT.with_suffix(".tmp.png")
sheet.save(tmp, format="PNG")
raw = tmp.read_bytes()
tmp.unlink()

# Build zTXt chunk: keyword "Description"\0 compression-method(0) compressed-text.
keyword = b"Description\x00\x00"  # \x00 sep + \x00 compression method
compressed = zlib.compress(desc.encode("latin-1"))
chunk_data = keyword + compressed
length = len(chunk_data).to_bytes(4, "big")
chunk_type = b"zTXt"
crc = (zlib.crc32(chunk_type + chunk_data) & 0xffffffff).to_bytes(4, "big")
ztxt = length + chunk_type + chunk_data + crc

# Insert before IEND.
iend_idx = raw.rfind(b"IEND") - 4  # back up to its length field
patched = raw[:iend_idx] + ztxt + raw[iend_idx:]
OUT.write_bytes(patched)
print(f"wrote {OUT} ({len(patched)} bytes)")
