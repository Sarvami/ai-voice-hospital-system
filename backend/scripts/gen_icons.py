"""Generate simple PWA icons. Run: python backend/scripts/gen_icons.py"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "frontend"

def write_png(path, size, rgb=(15, 25, 45), accent=(79, 195, 247)):
    try:
        from PIL import Image, ImageDraw
        img = Image.new("RGB", (size, size), rgb)
        d = ImageDraw.Draw(img)
        m = int(size * 0.12)
        d.ellipse([m, m, size - m, size - m], fill=accent)
        img.save(path)
        print("wrote", path)
        return
    except ImportError:
        pass
    import struct, zlib
    w = h = size
    raw = b"".join(b"\x00" + bytes([rgb[0], rgb[1], rgb[2]] * w) for _ in range(h))

    def chunk(tag, data):
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    Path(path).write_bytes(
        b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b"")
    )
    print("wrote (minimal)", path)


if __name__ == "__main__":
    for s in (192, 512):
        write_png(ROOT / f"icon-{s}.png", s)
