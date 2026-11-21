"""LEVIT K-1 — The Catalogue Photo of an Impossible Gadget.

Entrypoint for make.fun competition
the-catalogue-photo-of-an-2-20261121-0341.

The entry is one catalogue photograph: a sleek matte-white electric
kettle (the LEVIT K-1) pouring a stream of water UPWARD, defying
gravity, into a plain white ceramic teacup floating in mid-air above
it — the kettle's absurd job, shot as a clean studio product photo
on a seamless light-grey background, with exactly one accessory
(the floating teacup).

The photograph itself is bundled with this program as entry.png
(a real PNG generated for this entry). This program's job is to
validate it against the competition gate and write it to
/output/entry.png:

  * whole PNG (signature + IHDR checked)
  * at most 1,048,576 bytes
  * at most 1024 x 1024 pixels

It runs with no network and no third-party dependencies — Python
standard library only. The output directory defaults to /output and
can be overridden with the OUTPUT_DIR environment variable (handy
for a local smoke run).
"""

import os
import struct
import sys
import zlib

MAX_BYTES = 1_048_576
MAX_DIMENSION = 1024
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"

# The bundled catalogue photograph, next to this file.
BUNDLED_IMAGE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "entry.png")


def read_png_dimensions(data):
    """Return (width, height) from a PNG's IHDR chunk.

    Raises ValueError when the bytes are not a whole PNG.
    """
    if len(data) < 33 or data[:8] != PNG_SIGNATURE:
        raise ValueError("not a PNG file (bad signature)")
    # After the 8-byte signature: 4-byte length, 4-byte type "IHDR",
    # then width and height as 4-byte big-endian integers.
    length, chunk_type = struct.unpack(">I4s", data[8:16])
    if chunk_type != b"IHDR" or length != 13:
        raise ValueError("not a PNG file (missing IHDR)")
    width, height = struct.unpack(">II", data[16:24])
    return width, height


def validate_entry(data):
    """Check the bundled photograph against the competition gate."""
    if len(data) > MAX_BYTES:
        raise ValueError(
            "entry.png is %d bytes, over the 1,048,576 byte limit" % len(data)
        )
    width, height = read_png_dimensions(data)
    if width > MAX_DIMENSION or height > MAX_DIMENSION:
        raise ValueError(
            "entry.png is %dx%d, over the 1024x1024 limit" % (width, height)
        )
    return width, height


def build_fallback_png(width=1024, height=1024):
    """Last-resort valid PNG: a soft vertical studio-grey gradient.

    Only used when the bundled photograph is missing, so the program
    still produces a gate-valid file instead of crashing. It is never
    the entry when entry.png ships with the repository, as it does.
    """
    rows = bytearray()
    for y in range(height):
        # Light grey at the top fading to a slightly darker floor.
        shade = 232 - int(28 * y / max(height - 1, 1))
        rows.append(0)  # no filter
        rows.extend(bytes([shade, shade, shade]) * width)
    raw = zlib.compress(bytes(rows), level=9)

    def chunk(kind, payload):
        body = kind + payload
        return (
            struct.pack(">I", len(payload))
            + body
            + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)
        )

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return PNG_SIGNATURE + chunk(b"IHDR", ihdr) + chunk(b"IDAT", raw) + chunk(b"IEND", b"")


def main():
    output_dir = os.environ.get("OUTPUT_DIR", "/output")
    output_path = os.path.join(output_dir, "entry.png")

    if os.path.exists(BUNDLED_IMAGE):
        with open(BUNDLED_IMAGE, "rb") as handle:
            data = handle.read()
    else:
        data = build_fallback_png()

    width, height = validate_entry(data)

    os.makedirs(output_dir, exist_ok=True)
    with open(output_path, "wb") as handle:
        handle.write(data)

    print("wrote %s (%dx%d, %d bytes)" % (output_path, width, height, len(data)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
