from pathlib import Path
import struct
import sys

root = Path("build-src/MediAgenda_Android_v1")
res = root / "app/src/main/res/drawable-nodpi"
expected = ("saude_icon.png", "saude_splash.png", "saude_background.png")
for name in expected:
    file = res / name
    if not file.is_file():
        sys.exit(f"Missing required graphic: {file}")
    raw = file.read_bytes()
    if not raw.startswith(b"\x89PNG\r\n\x1a\n"):
        sys.exit(f"Not a PNG: {file}")
    width, height = struct.unpack(">II", raw[16:24])
    if width < 256 or height < 256:
        sys.exit(f"Placeholder graphic detected: {name} ({width}x{height})")
    print(f"OK: {name} {width}x{height}, {len(raw)} bytes")
print("All 3 branded images are real assets.")
