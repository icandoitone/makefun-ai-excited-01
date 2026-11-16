"""The Ocean in a Teacup — make.fun ai-excited-01 entry.

Copies the shipped image (entry.png, a JPEG) to /output/entry.png.
Deterministic: every run writes the same bytes. No network, stdlib only.

Before finishing, the program self-checks the copy against the gate:
a whole JPEG (SOI marker, EOI marker), at most 1 MiB and at most
1024 by 1024 pixels, byte-identical to the shipped file.
"""

import hashlib
import os
import shutil
import struct
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE / "entry.png"
OUT_DIR = Path(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output"))
MAX_BYTES = 1_048_576
MAX_SIDE = 1024


def jpeg_dimensions(data: bytes) -> tuple[int, int]:
    """Parse width/height from a JPEG's first SOF marker (stdlib only)."""
    if data[:2] != b"\xff\xd8":
        raise ValueError("not a JPEG: missing SOI marker")
    i = 2
    while i < len(data) - 1:
        if data[i] != 0xFF:
            i += 1
            continue
        marker = data[i + 1]
        if marker in (0xD8, 0xD9) or 0xD0 <= marker <= 0xD7:
            i += 2
            continue
        length = struct.unpack(">H", data[i + 2 : i + 4])[0]
        if 0xC0 <= marker <= 0xCF and marker not in (0xC4, 0xC8, 0xCC):
            height, width = struct.unpack(">HH", data[i + 5 : i + 9])
            return width, height
        i += 2 + length
    raise ValueError("no SOF marker found")


def main() -> None:
    data = SRC.read_bytes()
    if len(data) > MAX_BYTES:
        raise ValueError(f"image is {len(data)} bytes, over the 1 MiB limit")
    if not data.endswith(b"\xff\xd9"):
        raise ValueError("not a whole JPEG: missing EOI marker")
    width, height = jpeg_dimensions(data)
    if width > MAX_SIDE or height > MAX_SIDE:
        raise ValueError(f"image is {width}x{height}, over the 1024x1024 limit")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    dest = OUT_DIR / "entry.png"
    shutil.copyfile(SRC, dest)
    if hashlib.sha256(dest.read_bytes()).hexdigest() != hashlib.sha256(data).hexdigest():
        raise ValueError("copied file differs from the shipped image")


if __name__ == "__main__":
    main()
